import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const IS_PRODUCTION = process.env.NODE_ENV === 'production';
const ALLOWED_IPS = (process.env.ZERO_TRUST_ALLOWED_IPS || '')
  .split(',')
  .map((ip) => ip.trim())
  .filter(Boolean);

const REQUIRED_HEADERS = (process.env.ZERO_TRUST_REQUIRED_HEADERS || '')
  .split(',')
  .map((header) => header.trim().toLowerCase())
  .filter(Boolean);

const SSO_HEADER = (process.env.ZERO_TRUST_SSO_HEADER || 'x-user-auth').toLowerCase();
const TURNSTILE_HEADER = (process.env.TURNSTILE_HEADER || 'cf-turnstile-token').toLowerCase();
const RATE_LIMIT_MAX = Number(process.env.RATE_LIMIT_MAX || 200);
const RATE_LIMIT_WINDOW_MS = Number(process.env.RATE_LIMIT_WINDOW_MS || 60_000);
const REQUIRE_AUTH_COOKIE = (process.env.REQUIRE_AUTH_COOKIE || 'true').toLowerCase() !== 'false';
const AUTH_COOKIE_NAME = process.env.AUTH_COOKIE_NAME || '__Host-auth.session';
const REQUIRE_HTTPS = (process.env.REQUIRE_HTTPS || 'true').toLowerCase() !== 'false';
const ZERO_TRUST_BYPASS = (() => {
  const flag = (process.env.ZERO_TRUST_BYPASS || '').toLowerCase();
  if (flag === 'true') return true;
  if (flag === 'false') return false;
  return !IS_PRODUCTION;
})();

type RateLimitEntry = { count: number; expires: number };
const rateLimitStore: Map<string, RateLimitEntry> =
  globalThis.__rateLimitStore || new Map<string, RateLimitEntry>();
(globalThis as any).__rateLimitStore = rateLimitStore;

function getClientIp(request: NextRequest): string {
  return (
    request.ip ||
    request.headers.get('x-forwarded-for')?.split(',')[0].trim() ||
    request.headers.get('x-real-ip') ||
    'unknown'
  );
}

function enforceIpAllowList(ip: string) {
  if (!ALLOWED_IPS.length) return true;
  return ALLOWED_IPS.includes(ip);
}

function enforceHeaders(request: NextRequest) {
  for (const header of REQUIRED_HEADERS) {
    if (!request.headers.get(header)) return false;
  }
  return true;
}

function enforceSso(request: NextRequest) {
  return Boolean(request.headers.get(SSO_HEADER));
}

function enforceHttps(request: NextRequest) {
  if (!REQUIRE_HTTPS) return true;
  const forwardedProto = request.headers.get('x-forwarded-proto') || request.nextUrl.protocol.replace(':', '');
  return forwardedProto === 'https';
}

function enforceAuthCookie(request: NextRequest) {
  if (!REQUIRE_AUTH_COOKIE) return true;
  const cookie = request.cookies.get(AUTH_COOKIE_NAME);
  if (!cookie) return false;
  if (AUTH_COOKIE_NAME.startsWith('__Host-') || AUTH_COOKIE_NAME.startsWith('__Secure-')) {
    return true;
  }
  return false;
}

function rateLimit(ip: string): boolean {
  const now = Date.now();
  const entry = rateLimitStore.get(ip);
  if (!entry || entry.expires < now) {
    rateLimitStore.set(ip, { count: 1, expires: now + RATE_LIMIT_WINDOW_MS });
    return true;
  }
  if (entry.count >= RATE_LIMIT_MAX) return false;
  entry.count += 1;
  return true;
}

async function verifyTurnstile(token: string | null, ip: string) {
  if (!process.env.TURNSTILE_SECRET) return true;
  if (!token) return false;

  const formData = new FormData();
  formData.append('secret', process.env.TURNSTILE_SECRET);
  formData.append('response', token);
  if (ip && ip !== 'unknown') formData.append('remoteip', ip);

  const res = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) return false;
  const data = await res.json();
  return Boolean(data.success);
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};

export async function middleware(request: NextRequest) {
  if (ZERO_TRUST_BYPASS) {
    return NextResponse.next();
  }

  const ip = getClientIp(request);

  if (!enforceHttps(request)) {
    return NextResponse.json({ error: 'HTTPS required' }, { status: 403 });
  }

  if (!enforceIpAllowList(ip)) {
    return NextResponse.json({ error: 'IP not allowed' }, { status: 403 });
  }

  if (!enforceHeaders(request)) {
    return NextResponse.json({ error: 'Missing device posture headers' }, { status: 401 });
  }

  if (!enforceSso(request)) {
    const loginUrl = process.env.SSO_REDIRECT_URL || 'https://login.microsoftonline.com/';
    const redirectUrl = new URL(loginUrl);
    redirectUrl.searchParams.set('redirect', request.nextUrl.toString());
    return NextResponse.redirect(redirectUrl);
  }

  if (!enforceAuthCookie(request)) {
    return NextResponse.json({ error: 'Secure session cookie required' }, { status: 401 });
  }

  const isProxyRequest = request.nextUrl.pathname.startsWith('/api/proxy');
  if (isProxyRequest) {
    if (!rateLimit(ip)) {
      return NextResponse.json({ error: 'Rate limit exceeded' }, { status: 429 });
    }
    const token =
      request.headers.get(TURNSTILE_HEADER) ||
      request.nextUrl.searchParams.get(TURNSTILE_HEADER) ||
      null;
    const valid = await verifyTurnstile(token, ip);
    if (!valid) {
      return NextResponse.json({ error: 'Bot verification failed' }, { status: 400 });
    }
  }

  return NextResponse.next();
}
