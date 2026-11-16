# Nova AgriSense — System Architecture (Phase 0)

## 1. Architectural Pattern

Nova AgriSense uses a **Modular Monolith** backend (`apps/api`) paired with a decoupled **Next.js App Router** frontend (`apps/web`), backed by **Google Cloud SQL for PostgreSQL + PostGIS**.

- **Frontend (`apps/web`)**: Next.js, React, TypeScript, Tailwind CSS, React Hook Form, Zod, TanStack Query, Recharts.
- **Backend (`apps/api`)**: Python 3, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, psycopg3, GeoAlchemy2/Shapely, Pandas/NumPy, Pytest.
- **Shared Contracts (`packages/`)**: TypeScript interface mirrors (`shared-types`) and regional/role constants (`shared-config`).

## 2. AI Studio Build Mode Environment Boundary

Inspection of the current Google AI Studio Build Mode container established:
- **Node.js v22.23.2** and **npm 10.9.8** are installed; the AI Studio live preview runs Vite on port `3000` (`src/`).
- **Python 3.10.12** is installed with standard library support (`unittest`, `ast`, `compileall`), **without `pip` or `ensurepip`**.
- **PostgreSQL (`psql`)**, **Docker**, **uvicorn**, and **Cloud SQL Auth Proxy** are not pre-installed in the container.

In compliance with Section 4 (*Development Environment Compatibility*):
1. All Python business logic remains exclusively in `apps/api/` using FastAPI + SQLAlchemy + Alembic.
2. No Node.js/Express backend is substituted for FastAPI.
3. The root Vite application (`src/`) renders the Nova AgriSense architecture console and frontend preview inside AI Studio while `apps/web` and `apps/api` remain independently runnable in local, Docker, or Cloud Run environments.

## 3. Multi-Tenant Data Isolation Strategy

Every agricultural entity (`farmers`, `farms`, `plots`, `production_records`, `import_batches`, `reports`) carries an explicit `organization_id` foreign key.
- Backend services derive tenant context strictly from verified JWT claims and `organization_memberships` records—never from unverified client headers or body payloads.
- PostgreSQL Row-Level Security (RLS) policies will be added in Phase 1 migrations alongside application-layer repository filtering.
