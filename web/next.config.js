/** @type {import('next').NextConfig} */
const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
const isDev = process.env.NODE_ENV !== 'production';
const reportUri = process.env.CSP_REPORT_URI || '';
const reportTo = process.env.CSP_REPORT_TO || '';

const connectSrc = process.env.NEXT_PUBLIC_CONNECT_SRC
  ? process.env.NEXT_PUBLIC_CONNECT_SRC.split(',').map((src) => src.trim()).filter(Boolean)
  : [apiBase];

const allowInlineStyles = (process.env.ALLOW_INLINE_STYLES || '').toLowerCase() !== 'false';

const styleSrc = ["'self'"];
if (allowInlineStyles) {
  styleSrc.push("'unsafe-inline'");
}

const csp = [
  "default-src 'self'",
  `style-src ${styleSrc.join(' ')}`,
  `connect-src 'self' ${connectSrc.join(' ')}`,
  "img-src 'self' data: https:",
  `script-src 'self'${isDev ? " 'unsafe-eval'" : ''}`,
  "font-src 'self' data:",
  "frame-ancestors 'self'",
  reportUri ? `report-uri ${reportUri}` : '',
  reportTo ? `report-to ${reportTo}` : '',
]
  .filter(Boolean)
  .join('; ');

const securityHeaders = [
  { key: 'Content-Security-Policy', value: csp },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-XSS-Protection', value: '0' },
  { key: 'Permissions-Policy', value: 'geolocation=(), microphone=(), camera=()' },
  { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
];

if (reportTo) {
  securityHeaders.push({
    key: 'Report-To',
    value: reportTo,
  });
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_BASE: apiBase,
  },
  assetPrefix: process.env.CDN_ASSET_PREFIX || undefined,
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: securityHeaders,
      },
    ];
  },
};

module.exports = nextConfig;
