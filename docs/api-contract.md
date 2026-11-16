# Nova AgriSense — Versioned REST API Contract (`/api/v1`)

All endpoints are mounted under `/api/v1`.

## Phase 0 Endpoints

| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Public | Liveness probe |
| `GET` | `/api/v1/health/ready` | Public | Readiness probe (PostgreSQL & PostGIS) |
| `GET` | `/api/v1/meta` | Public | Supported Gambia regions, RBAC roles, phase status |

## Phase 1 Authentication & Administration Endpoints

| Method | Path | Auth / Headers | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Public (if enabled) | Register user account (Argon2id hashed) |
| `POST` | `/api/v1/auth/login` | Public | Authenticate, return Bearer JWT, set HttpOnly refresh + CSRF cookies |
| `POST` | `/api/v1/auth/refresh` | Refresh cookie + `X-CSRF-Token` | Rotate refresh session (with reuse detection) and issue fresh JWT |
| `POST` | `/api/v1/auth/logout` | Refresh cookie + `X-CSRF-Token` | Revoke refresh session and clear cookies |
| `GET` | `/api/v1/auth/me` | Bearer JWT | Return current user profile and memberships |
| `POST` | `/api/v1/auth/change-password` | Bearer JWT | Verify current password, update hash, revoke all active refresh sessions |
| `POST` | `/api/v1/organizations` | Bearer JWT | Create organization and assign creator as `ORGANIZATION_ADMIN` |
| `GET` | `/api/v1/organizations` | Bearer JWT | List organizations where current user holds a membership |
| `GET` | `/api/v1/organizations/{id}` | Bearer JWT + `X-Organization-ID` | View organization details (`org:read`) |
| `PATCH` | `/api/v1/organizations/{id}` | Bearer JWT + `X-Organization-ID` | Update organization profile (`org:update`) |
| `GET` | `/api/v1/organizations/{id}/members` | Bearer JWT + `X-Organization-ID` | List organization members (`membership:read`) |
| `POST` | `/api/v1/organizations/{id}/members` | Bearer JWT + `X-Organization-ID` | Add/invite registered user (`membership:manage`) |
| `POST` | `/api/v1/organizations/{id}/invitations/accept` | Bearer JWT | Accept pending invitation for `{id}` |
| `PATCH` | `/api/v1/organizations/{id}/members/{membership_id}` | Bearer JWT + `X-Organization-ID` | Update member role (`membership:manage`) |
| `DELETE` | `/api/v1/organizations/{id}/members/{membership_id}` | Bearer JWT + `X-Organization-ID` | Deactivate membership (`membership:manage`) |
| `GET` | `/api/v1/organizations/{id}/audit-logs` | Bearer JWT + `X-Organization-ID` | List tenant-scoped audit logs (`audit:read`) |
| `GET` | `/api/v1/admin/organizations` | Bearer JWT (`PLATFORM_ADMIN`) | Platform-wide organization listing |
| `GET` | `/api/v1/admin/audit-logs` | Bearer JWT (`PLATFORM_ADMIN`) | Platform-wide audit log listing |
