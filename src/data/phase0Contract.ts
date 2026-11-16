import { GAMBIA_REGIONS, ROLE_DEFINITIONS } from '../../packages/shared-config/src/index';

export { GAMBIA_REGIONS, ROLE_DEFINITIONS };

export interface MonorepoNode {
  path: string;
  layer: string;
  summary: string;
  runtime: string;
  status: 'Implemented (Phase 0)' | 'Implemented (Phase 1)' | 'CI / Infra Template';
}

export const MONOREPO_NODES: MonorepoNode[] = [
  {
    path: 'apps/api/app/models/',
    layer: 'SQLAlchemy 2.x Phase 1 Schema',
    summary:
      'User, Organization, OrganizationMembership, RefreshSession (with token family reuse detection), and AuditLog models.',
    runtime: 'SQLAlchemy 2.x + PostgreSQL',
    status: 'Implemented (Phase 1)',
  },
  {
    path: 'apps/api/alembic/versions/0001_phase1_auth_multitenancy_rls.py',
    layer: 'Alembic Migration + PostgreSQL RLS',
    summary:
      'Creates Phase 1 tables, indexes, constraints, and FORCE ROW LEVEL SECURITY policies on tenant-owned tables.',
    runtime: 'Alembic + PostgreSQL 15+',
    status: 'Implemented (Phase 1)',
  },
  {
    path: 'apps/api/app/security/',
    layer: 'Argon2id, JWT, RBAC, CSRF & Rate Limiting',
    summary:
      'Argon2id password hashing, HS256 JWT validation, opaque refresh token hashing, 7-role RBAC matrix, and transaction-local RLS context.',
    runtime: 'Python Security Layer',
    status: 'Implemented (Phase 1)',
  },
  {
    path: 'apps/api/app/api/v1/endpoints/auth.py',
    layer: 'Authentication API',
    summary:
      'Register, login, HttpOnly refresh cookie rotation, logout revocation, /auth/me, and password change endpoints.',
    runtime: 'FastAPI Router',
    status: 'Implemented (Phase 1)',
  },
  {
    path: 'apps/api/app/api/v1/endpoints/organizations.py',
    layer: 'Multi-Tenant Organizations & RBAC API',
    summary:
      'Organization CRUD, X-Organization-ID tenant isolation, member invitation/acceptance, role updates, and audit logs.',
    runtime: 'FastAPI Router',
    status: 'Implemented (Phase 1)',
  },
  {
    path: 'apps/web/src/app/',
    layer: 'Next.js 15 App Router Frontend',
    summary:
      'Connected login, register, WorkspaceShell org switcher, organization/member management, profile, and platform admin routes.',
    runtime: 'Node.js / Next.js Standalone',
    status: 'Implemented (Phase 1)',
  },
  {
    path: 'packages/shared-types/src/index.ts',
    layer: 'API Contract Mirror',
    summary:
      'Shared TypeScript interfaces matching Phase 1 Pydantic auth, organization, membership, and audit schemas.',
    runtime: 'TypeScript',
    status: 'Implemented (Phase 1)',
  },
  {
    path: '.github/workflows/ci.yml',
    layer: 'CI with PostgreSQL + PostGIS',
    summary:
      'Runs Ruff, Alembic upgrade head, non-superuser NOBYPASSRLS role setup, Pytest RLS integration suite, and Next.js build.',
    runtime: 'GitHub Actions',
    status: 'CI / Infra Template',
  },
];

export const STREAMLIT_MIGRATION_INVENTORY = [
  { file: 'app.py', target: 'Replaced by apps/web + /api/v1', state: 'Awaiting source file' },
  { file: 'crop_recommend.py', target: 'apps/api/app/analytics/ (rule-based phase)', state: 'Awaiting source file' },
  { file: 'weather_bot.py', target: 'apps/api/app/integrations/ (weather adapter)', state: 'Awaiting source file' },
  { file: 'farmer_tools.py', target: 'apps/api/app/modules/ (validated calculators)', state: 'Awaiting source file' },
  { file: 'i18n.py', target: 'packages/shared-config + apps/web locales', state: 'Awaiting source file' },
  { file: 'sms_ussd_stub.py', target: 'apps/api/app/integrations/ (low-bandwidth gateway)', state: 'Awaiting source file' },
  { file: 'requirements.txt', target: 'Audited against apps/api/requirements.txt', state: 'Awaiting source file' },
  { file: 'README.md', target: 'Merged into docs/streamlit-migration.md', state: 'Awaiting source file' },
] as const;

export const PHASE_ROADMAP = [
  {
    phase: 'Phase 0',
    title: 'Architecture & Repository Foundation',
    status: 'Completed',
    scope: 'Monorepo layout, FastAPI + Next.js scaffolds, API v1 contract, GCP & CI templates, environment audit.',
  },
  {
    phase: 'Phase 1',
    title: 'Database, Multi-Tenancy, Auth & RBAC',
    status: 'Code Complete (DB Verification Pending)',
    scope: 'Alembic migration, Argon2id auth, HttpOnly refresh rotation, RBAC, X-Organization-ID isolation, PostgreSQL RLS, Next.js auth integration.',
  },
  {
    phase: 'Phase 2',
    title: 'Core Agricultural Management',
    status: 'Planned',
    scope: 'Farmers, farms, PostGIS plots, crop catalogue, and seasonal production records with full CRUD and tests.',
  },
  {
    phase: 'Phase 3',
    title: 'Agricultural Data Operations',
    status: 'Planned',
    scope: 'CSV/Excel staging tables, validation pipeline, duplicate detection, rejected-row exports, import history.',
  },
  {
    phase: 'Phase 4',
    title: 'Dashboard & Agricultural Analytics',
    status: 'Planned',
    scope: 'Tenant-scoped Recharts analytics, yield comparisons, regional filters, explicit source/date metadata.',
  },
  {
    phase: 'Phase 5',
    title: 'Reporting & External Integrations',
    status: 'Planned',
    scope: 'CSV/XLSX/PDF exports, Cloud Storage signed links, weather provider interfaces, idempotent background jobs.',
  },
  {
    phase: 'Phase 6',
    title: 'Explainable Agricultural Intelligence',
    status: 'Planned',
    scope: 'Transparent rule-based crop/weather advisories, explicit input provenance, uncertainty bounds, human review.',
  },
  {
    phase: 'Phase 7',
    title: 'Production Readiness & Audit',
    status: 'Planned',
    scope: 'Security audit, load testing, WCAG accessibility review, backup/recovery verification, Cloud Run rollout.',
  },
] as const;

export interface EndpointContractSpec {
  id: string;
  method: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  path: string;
  summary: string;
  sampleResponse: unknown;
}

export const API_V1_ENDPOINTS: EndpointContractSpec[] = [
  {
    id: 'auth-login',
    method: 'POST',
    path: '/api/v1/auth/login',
    summary:
      'Verifies Argon2id hash, issues short-lived Bearer JWT, sets HttpOnly refresh cookie and CSRF cookie.',
    sampleResponse: {
      access_token: '<short-lived-jwt-access-token>',
      token_type: 'Bearer',
      expires_in: 900,
      user: {
        id: '3fa85f64-5717-4562-b3fc-2c963f66afa6',
        email: 'officer@lrr-coop.gm',
        full_name: 'Amina Jallow',
        is_active: true,
        platform_role: null,
        memberships: [
          {
            organization_id: '8c1b6a20-23ab-4a0d-b9e1-7a991c31f001',
            organization_name: 'Lower River Growers Cooperative',
            role: 'ORGANIZATION_ADMIN',
            status: 'active',
          },
        ],
      },
    },
  },
  {
    id: 'auth-refresh',
    method: 'POST',
    path: '/api/v1/auth/refresh',
    summary:
      'Validates CSRF + HttpOnly refresh cookie, rotates token in family, and revokes whole family on reuse.',
    sampleResponse: {
      access_token: '<rotated-short-lived-jwt>',
      token_type: 'Bearer',
      expires_in: 900,
    },
  },
  {
    id: 'orgs-members',
    method: 'GET',
    path: '/api/v1/organizations/{organization_id}/members',
    summary:
      'Requires Bearer JWT, X-Organization-ID header, active membership, membership:read permission, and PostgreSQL RLS context.',
    sampleResponse: [
      {
        id: 'c8f51210-1b2a-4c3d-9e4f-111122223333',
        organization_id: '8c1b6a20-23ab-4a0d-b9e1-7a991c31f001',
        email: 'officer@lrr-coop.gm',
        full_name: 'Amina Jallow',
        role: 'ORGANIZATION_ADMIN',
        status: 'active',
      },
    ],
  },
  {
    id: 'health',
    method: 'GET',
    path: '/api/v1/health',
    summary: 'Liveness probe confirming FastAPI service identity, version, and runtime environment.',
    sampleResponse: {
      status: 'ok',
      service: 'Nova AgriSense API',
      version: '0.2.0',
      environment: 'development',
      timestamp_utc: '2026-11-14T19:45:00Z',
    },
  },
  {
    id: 'ready',
    method: 'GET',
    path: '/api/v1/health/ready',
    summary: 'Readiness probe checking PostgreSQL connectivity and PostGIS extension availability.',
    sampleResponse: {
      status: 'not_ready',
      checks: {
        database: {
          configured: false,
          reachable: false,
          postgis_enabled: null,
          detail: 'NOVA_DATABASE_URL is not configured.',
        },
      },
      timestamp_utc: '2026-11-14T19:45:00Z',
    },
  },
];
