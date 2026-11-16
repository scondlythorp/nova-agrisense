# Nova AgriSense

Multi-tenant agricultural intelligence platform initially designed for **The Gambia** with expansion architecture across **West Africa**.

## Monorepo Structure

```text
.
├── apps/
│   ├── api/                 # Python 3 + FastAPI + Pydantic v2 + SQLAlchemy 2.x + Alembic
│   └── web/                 # Next.js (App Router) + React + TypeScript + Tailwind + TanStack Query
├── packages/
│   ├── shared-types/        # Shared TypeScript API contracts mirrored with Pydantic
│   └── shared-config/       # Gambia administrative regions & RBAC role definitions
├── infrastructure/          # Cloud Run manifests, PostGIS init SQL, GCP setup guide
├── docs/                    # Architecture, API contract, database, security, Streamlit migration docs
├── scripts/                 # Local developer launcher scripts
├── .github/workflows/       # GitHub Actions CI with PostgreSQL + PostGIS service container
├── src/                     # Google AI Studio Build Mode live Vite preview shell
└── .env.example             # Environment variable template (no secrets)
```

## Phase 1 Setup (PostgreSQL + Migrations + Backend + Frontend)

1. **Provision PostgreSQL 15+ and create migration + non-superuser runtime roles**:
   ```sql
   CREATE ROLE nova_admin WITH LOGIN PASSWORD 'CHANGE_ME';
   CREATE DATABASE nova_agrisense OWNER nova_admin;
   CREATE ROLE nova_app_user WITH LOGIN PASSWORD 'CHANGE_ME' NOBYPASSRLS;
   ```
2. **Run Alembic migrations as `nova_admin`**:
   ```bash
   cd apps/api
   export NOVA_DATABASE_URL="postgresql+psycopg://nova_admin:CHANGE_ME@localhost:5432/nova_agrisense"
   alembic upgrade head
   ```
   Grant runtime DML privileges to `nova_app_user`:
   ```sql
   GRANT USAGE ON SCHEMA public TO nova_app_user;
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nova_app_user;
   GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO nova_app_user;
   ```
3. **Run FastAPI backend as `nova_app_user`**:
   ```bash
   cd apps/api
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   export NOVA_DATABASE_URL="postgresql+psycopg://nova_app_user:CHANGE_ME@localhost:5432/nova_agrisense"
   export NOVA_SECRET_KEY="$(openssl rand -hex 32)"
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. **Run PostgreSQL integration & RLS tests**:
   ```bash
   cd apps/api
   export NOVA_TEST_DATABASE_URL="postgresql+psycopg://nova_app_user:CHANGE_ME@localhost:5432/nova_agrisense_test"
   pytest -q
   ```
5. **Run Next.js frontend**:
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```
