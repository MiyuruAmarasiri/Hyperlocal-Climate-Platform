# Hyperlocal Climate Platform – Web Experience

A Next.js site that showcases the Hyperlocal Climate-Risk Early-Warning and Adaptation Platform. It connects to the FastAPI service to display forecasts, risk maps, and operational status.

## Prerequisites
- Node.js 18+
- The backend API (`uvicorn api.main:app`) running and reachable (default `http://localhost:8000`).

## Getting started
```bash
cd web
cp .env.local.example .env.local # adjust API base if needed
npm install
npm run dev
```

Open http://localhost:3000 in your browser. The dashboard will fetch live data from the configured API base. Use `npm run build && npm start` for a production build.

## Structure
- `pages/` – Next.js route pages for overview, forecast explorer, risk intelligence, and sensor docs.
- `components/` – Layout, section, and card components shared across pages.
- `lib/api.js` – Minimal client for the FastAPI endpoints.
- `styles/` – CSS modules and global styling.

## Deployment
You can deploy the `web` app as a standalone Next.js service (Vercel, Azure Static Web Apps, etc.). Expose `NEXT_PUBLIC_API_BASE` pointing to your public API gateway and run `npm run build` during CI/CD.
## Security
Set `API_CLIENT_KEY` via your secrets manager and inject it at deploy time. The Next.js proxy forwards the key in `x-api-key`, which FastAPI validates against SHA-256 hashes.
- For CSP, set `NEXT_PUBLIC_CONNECT_SRC=https://api.hyperlocal.openai.com` (comma separated) so only production domains are contacted. During dev it falls back to `NEXT_PUBLIC_API_BASE`.
- When deploying behind Zero Trust gateways, set `ALLOW_INLINE_STYLES=false` to drop `'unsafe-inline'` from `style-src` and rely entirely on CSS modules.
## Zero-trust middleware
The `middleware.ts` enforces enterprise controls before any page/API responds. Configure via environment variables:

- `ZERO_TRUST_SSO_HEADER`, `SSO_REDIRECT_URL`: header that proves SSO (e.g., Azure AD `x-ms-client-principal`) and the login URL to redirect unauthenticated users.
- `ZERO_TRUST_ALLOWED_IPS`: comma-separated allowlist (optional). `ZERO_TRUST_REQUIRED_HEADERS`: device posture headers from your MDM.
- `TURNSTILE_SECRET` + `TURNSTILE_HEADER`: Cloudflare Turnstile verification for `/api/proxy` requests. Provide the widget token in that header.
- `RATE_LIMIT_MAX`, `RATE_LIMIT_WINDOW_MS`: per-IP throttling for the proxy route.

Always set `NEXT_PUBLIC_CONNECT_SRC` to your production API domain(s) and flip `ALLOW_INLINE_STYLES=false` once all styling is handled through CSS modules.
- Set `AUTH_COOKIE_NAME` (default `__Host-auth.session`) and `REQUIRE_AUTH_COOKIE=true` so middleware only admits requests carrying the secure SSO cookie. Use `__Host-`/`__Secure-` prefixes so browsers enforce `Secure`, `HttpOnly`, `SameSite=Strict`, and `path=/`. `REQUIRE_HTTPS=true` rejects any request not forwarded over TLS.
- Forward Next.js proxy access logs to your SIEM. Set `CSP_REPORT_URI`/`CSP_REPORT_TO` to collect CSP violation reports and correlate them with WAF telemetry.
- Use `CDN_ASSET_PREFIX` to point static assets to your signed CDN distribution (Azure CDN, CloudFront). Configure the CDN with origin shields and signed URLs.
- When loading third-party scripts, define `NEXT_PUBLIC_THIRD_PARTY_SCRIPT_SRC` and the SHA-384 hash in `NEXT_PUBLIC_THIRD_PARTY_SCRIPT_INTEGRITY`; `SecurityHead` will inject the script with `integrity` + `crossorigin` attributes.

- For local development, zero-trust checks are bypassed automatically (NODE_ENV !== production). Set `ZERO_TRUST_BYPASS=false` to exercise the full policy locally.

