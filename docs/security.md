# Nova AgriSense — Security Architecture (Phase 1)

## Authentication & Token Lifecycle

- **Password Hashing**: Argon2id via `argon2-cffi` (`time_cost=3`, `memory_cost=65536`, `parallelism=4`). Minimum 12-character policy requiring upper, lower, and digit characters, blocking common passphrases and email local-part reuse.
- **Account Verification Policy**: Self-registered accounts initialize with `is_verified=False`. Because Phase 1 does not bundle an external email/SMS delivery provider, `NOVA_REQUIRE_EMAIL_VERIFICATION` defaults to `false` so registered accounts can authenticate while displaying their unverified status. Setting `NOVA_REQUIRE_EMAIL_VERIFICATION=true` strictly blocks unverified accounts (`403 account_unverified`) at login, `/auth/me`, and `/auth/refresh`.
- **Access Tokens**: Short-lived HS256 JWTs (`15m` default) validating signature, `exp`, `iss`, `aud`, `type="access"`, `sub`, `jti`, and live `user.is_active` status on every request.
- **Refresh Sessions**: High-entropy CSPRNG opaque tokens stored exclusively as HMAC-SHA256 digests (`refresh_sessions.token_hash`) and delivered in `HttpOnly`, `SameSite=Lax` (or configured), `Secure` (staging/production) cookies.
- **Rotation & Reuse Detection**: Every `/auth/refresh` rotates to a new session row in the same `token_family_id`. Re-presenting a rotated or revoked refresh token immediately revokes every session in that token family and records `auth.refresh_reuse_detected`.
- **CSRF Protection**: Double-submit `nova_csrf_token` cookie paired with `X-CSRF-Token` header verified via constant-time `hmac.compare_digest` on cookie-authenticated `/auth/refresh` and `/auth/logout`. Login and refresh responses also return `csrf_token` in the CORS-restricted JSON body for in-memory header attachment; for full page-reload refresh across separate subdomains in production, share a parent `NOVA_COOKIE_DOMAIN` or route `/api/v1/*` under a unified HTTPS origin.
- **Login & Auth Rate Limiting**: Sliding-window per-IP and per-account rate limiter (`apps/api/app/security/rate_limit.py`) returning HTTP `429`. Client IP resolution ignores `X-Forwarded-For` unless `NOVA_TRUST_PROXY_HEADERS=true`, and uses the rightmost proxy-appended IP to prevent client-header spoofing. Multi-instance Cloud Run deployments should additionally pair with Cloud Armor edge rate limits.

## Multi-Tenancy & RBAC

- **Tenant Resolution**: Organization-scoped routes require `X-Organization-ID` header, validate UUID format, confirm active organization + active membership in PostgreSQL, bind transaction-local RLS context (`set_config(..., true)`), and assert path/header ID alignment.
- **Centralized RBAC (`apps/api/app/security/rbac.py`)**: Enforces fine-grained permissions across `ORGANIZATION_ADMIN`, `AGRICULTURAL_OFFICER`, `DATA_MANAGER`, `RESEARCHER`, `COOPERATIVE_MANAGER`, `FARMER`, and `READ_ONLY_ANALYST`.
- **Privilege Escalation Prevention**: Self-registration cannot assign `PLATFORM_ADMIN`; organization member endpoints only accept `OrganizationRole` values; last active `ORGANIZATION_ADMIN` cannot be demoted or deactivated.

## Audit Logging

- Append-only `audit_logs` records auth lifecycle, membership changes, and organization mutations while scrubbing sensitive keys (`password`, `token`, `secret`, `authorization`).
