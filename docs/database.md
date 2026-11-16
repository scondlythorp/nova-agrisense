# Nova AgriSense — Database & RLS Architecture (Phase 1)

## Engine & ORM Standards

- **Database**: PostgreSQL 15+ hosted on Google Cloud SQL.
- **Geospatial Extension**: PostGIS (`GEOGRAPHY` / `GEOMETRY`, SRID 4326) — verified separately; Phase 1 auth/tenancy migrations do not depend on PostGIS.
- **ORM & Migrations**: SQLAlchemy 2.x (`apps/api/app/models/`) and Alembic (`apps/api/alembic/versions/0001_phase1_auth_multitenancy_rls.py`).

## Phase 1 Tables

1. `users`: UUID PK, unique normalized lowercase `email`, Argon2id `password_hash`, `full_name`, optional `phone_number`, `is_active`, `is_verified`, nullable `platform_role`, UTC timestamps, `last_login_at`.
2. `organizations`: UUID PK, `name`, unique `slug`, `organization_type`, `description`, `contact_email`, `contact_phone`, `region`, `district`, `is_active`, UTC timestamps.
3. `organization_memberships`: UUID PK, `organization_id` (CASCADE), `user_id` (CASCADE), `role`, `status`, `invited_by_user_id` (SET NULL), `joined_at`, UTC timestamps, unique `(organization_id, user_id)`.
4. `refresh_sessions`: UUID PK, `user_id` (CASCADE), `token_family_id`, unique HMAC-SHA256 `token_hash`, `replaced_by_session_id`, `expires_at`, `revoked_at`, `revocation_reason`, `created_at`, `last_used_at`, `user_agent`, `ip_address`.
5. `audit_logs`: UUID PK, nullable `organization_id` (SET NULL), nullable `actor_user_id` (SET NULL), `action`, `resource_type`, `resource_id`, `request_id`, UTC `timestamp`, `metadata_json` (JSONB).

## Database Roles & PostgreSQL Row-Level Security (RLS)

To ensure RLS is never silently bypassed:

1. **Migration Owner Role (`nova_admin`)**: Owns tables and executes `alembic upgrade head`.
2. **Runtime Application Role (`nova_app_user`)**: Created with `NOBYPASSRLS` and granted `SELECT, INSERT, UPDATE, DELETE` on public tables. All normal FastAPI requests connect as `nova_app_user`.
3. **Transaction-Local Tenant Context**: FastAPI binds `app.current_user_id`, `app.current_organization_id`, and `app.is_platform_admin` via `SELECT set_config(..., ..., true)` (`is_local = true`). When a pooled connection rolls back or closes, PostgreSQL clears all transaction-local settings automatically.
4. **Enforced Tables**: `organization_memberships` and `audit_logs` have both `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY`. Unset context evaluates to `NULL` and denies row access. On `organization_memberships`, `user_id = app.current_user_id` grants `SELECT` visibility only, while `INSERT`, `UPDATE`, and `DELETE` strictly require `organization_id = app.current_organization_id` (or `app.is_platform_admin = 'true'`). `audit_logs` has `SELECT` and `INSERT` policies only, enforcing append-only immutability at the database level.
