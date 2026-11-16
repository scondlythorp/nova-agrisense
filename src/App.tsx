import { useMemo, useState } from 'react';
import {
  ArrowUpRight,
  ChevronRight,
  Database,
  FileCode2,
  FolderTree,
  Search,
  Server,
  ShieldCheck,
} from 'lucide-react';
import {
  API_V1_ENDPOINTS,
  GAMBIA_REGIONS,
  MONOREPO_NODES,
  PHASE_ROADMAP,
  ROLE_DEFINITIONS,
  STREAMLIT_MIGRATION_INVENTORY,
} from './data/phase0Contract';

type WorkspaceTab = 'overview' | 'architecture' | 'api' | 'roadmap';

const HERO_IMAGE_PATH = '/src/assets/images/gambia_agriculture_hero_1794713337409.jpg';

export default function App() {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('overview');
  const [regionQuery, setRegionQuery] = useState('');
  const [selectedNodePath, setSelectedNodePath] = useState(MONOREPO_NODES[0].path);
  const [selectedEndpointId, setSelectedEndpointId] = useState(API_V1_ENDPOINTS[0].id);
  const [heroImageError, setHeroImageError] = useState(false);

  const [apiBaseInput, setApiBaseInput] = useState('http://localhost:8000/api/v1');
  const [probeState, setProbeState] = useState<{
    status: 'idle' | 'loading' | 'success' | 'error';
    message: string;
    payload?: string;
  }>({ status: 'idle', message: '' });

  const filteredRegions = useMemo(() => {
    const q = regionQuery.trim().toLowerCase();
    if (!q) return GAMBIA_REGIONS;
    return GAMBIA_REGIONS.filter(
      (r) =>
        r.name.toLowerCase().includes(q) ||
        r.code.toLowerCase().includes(q) ||
        r.headquarters.toLowerCase().includes(q),
    );
  }, [regionQuery]);

  const selectedNode = useMemo(
    () => MONOREPO_NODES.find((n) => n.path === selectedNodePath) ?? MONOREPO_NODES[0],
    [selectedNodePath],
  );

  const selectedEndpoint = useMemo(
    () => API_V1_ENDPOINTS.find((e) => e.id === selectedEndpointId) ?? API_V1_ENDPOINTS[0],
    [selectedEndpointId],
  );

  const runLiveEndpointCheck = async () => {
    const cleanedBase = apiBaseInput.replace(/\/+$/, '');
    const probePath =
      selectedEndpoint.method === 'GET' && !selectedEndpoint.path.includes('{')
        ? selectedEndpoint.path.replace('/api/v1', '')
        : '/health';
    const targetUrl = `${cleanedBase}${probePath}`;
    setProbeState({ status: 'loading', message: `Querying ${targetUrl}...` });

    try {
      const response = await fetch(targetUrl, { method: 'GET' });
      const text = await response.text();
      setProbeState({
        status: response.ok ? 'success' : 'error',
        message: `HTTP ${response.status} from ${targetUrl}`,
        payload: text,
      });
    } catch {
      setProbeState({
        status: 'error',
        message: `Unable to reach ${targetUrl} from this browser context. Start apps/api locally with uvicorn or deploy to Cloud Run to test live responses.`,
      });
    }
  };

  return (
    <div className="min-h-screen bg-[#f8f9f7] text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-8 px-6 py-4">
          <a
            href="#top"
            onClick={() => setActiveTab('overview')}
            className="text-lg font-bold tracking-tight text-slate-900 whitespace-nowrap shrink-0"
          >
            Nova AgriSense
          </a>

          <nav
            aria-label="Primary navigation"
            className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600"
          >
            <button
              type="button"
              onClick={() => setActiveTab('overview')}
              className={`whitespace-nowrap shrink-0 transition-colors cursor-pointer ${
                activeTab === 'overview'
                  ? 'text-[#14532d] underline underline-offset-4'
                  : 'hover:text-slate-900 hover:underline underline-offset-4'
              }`}
            >
              Overview
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('architecture')}
              className={`whitespace-nowrap shrink-0 transition-colors cursor-pointer ${
                activeTab === 'architecture'
                  ? 'text-[#14532d] underline underline-offset-4'
                  : 'hover:text-slate-900 hover:underline underline-offset-4'
              }`}
            >
              Architecture
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('api')}
              className={`whitespace-nowrap shrink-0 transition-colors cursor-pointer ${
                activeTab === 'api'
                  ? 'text-[#14532d] underline underline-offset-4'
                  : 'hover:text-slate-900 hover:underline underline-offset-4'
              }`}
            >
              API Contract
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('roadmap')}
              className={`whitespace-nowrap shrink-0 transition-colors cursor-pointer ${
                activeTab === 'roadmap'
                  ? 'text-[#14532d] underline underline-offset-4'
                  : 'hover:text-slate-900 hover:underline underline-offset-4'
              }`}
            >
              Phases
            </button>
          </nav>

          <div className="shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('architecture')}
              className="inline-flex items-center gap-1.5 rounded-lg bg-[#14532d] px-4 py-2 text-xs font-semibold text-white hover:bg-[#166534] transition-colors whitespace-nowrap shrink-0 cursor-pointer"
            >
              Inspect Foundation
            </button>
          </div>
        </div>
      </header>

      <div className="border-b border-slate-200 bg-white md:hidden">
        <div className="flex items-center gap-2 overflow-x-auto px-4 py-2 text-xs font-medium">
          {(
            [
              ['overview', 'Overview'],
              ['architecture', 'Architecture'],
              ['api', 'API Contract'],
              ['roadmap', 'Phases'],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => setActiveTab(id)}
              className={`rounded-md px-3 py-1.5 whitespace-nowrap shrink-0 ${
                activeTab === id
                  ? 'bg-[#14532d] text-white'
                  : 'bg-slate-100 text-slate-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <main id="top" className="mx-auto max-w-6xl px-6 py-10 space-y-12">
        {activeTab === 'overview' && (
          <>
            <section className="grid gap-8 lg:grid-cols-12 items-stretch">
              <div className="lg:col-span-7 flex flex-col justify-between space-y-6">
                <div className="space-y-4">
                  <p className="text-xs font-medium text-slate-500">
                    The Gambia · West Africa Expansion Architecture · Phase 0 Foundation
                  </p>
                  <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 text-balance">
                    Structured agricultural intelligence for cooperatives, officers, and researchers.
                  </h1>
                  <p className="text-base leading-relaxed text-slate-600 max-w-2xl">
                    Nova AgriSense is engineered to transform fragmented field records into
                    auditable agricultural intelligence. Built with an isolated FastAPI +
                    PostgreSQL/PostGIS backend and a mobile-first Next.js frontend designed
                    for low-bandwidth operating conditions.
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-4 pt-2">
                  <button
                    type="button"
                    onClick={() => setActiveTab('api')}
                    className="inline-flex items-center gap-2 rounded-lg bg-[#14532d] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#166534] transition-colors whitespace-nowrap cursor-pointer"
                  >
                    Explore API v1 Contract
                    <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab('roadmap')}
                    className="inline-flex items-center rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors whitespace-nowrap cursor-pointer"
                  >
                    View Phase Plan
                  </button>
                </div>
              </div>

              <div className="lg:col-span-5">
                <div className="relative h-64 lg:h-full min-h-[260px] overflow-hidden rounded-lg border border-slate-200 bg-slate-100">
                  {!heroImageError ? (
                    <img
                      src={HERO_IMAGE_PATH}
                      alt="Smallholder agricultural plots and fields in The Gambia river basin"
                      referrerPolicy="no-referrer"
                      onError={() => setHeroImageError(true)}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full w-full flex-col items-center justify-center bg-gradient-to-br from-emerald-950 to-slate-900 p-6 text-center text-white">
                      <p className="text-sm font-semibold">Nova AgriSense Field Context</p>
                      <p className="mt-1 text-xs text-slate-300">
                        Gambia River Basin · Smallholder Plots &amp; Cooperative Data
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </section>

            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 border-t border-slate-200 pt-8">
              <div className="rounded-lg border border-slate-200 bg-white p-5">
                <p className="text-xs font-medium text-slate-500">Backend Stack</p>
                <p className="mt-1.5 text-base font-semibold text-slate-900">
                  Python 3 · FastAPI
                </p>
                <p className="mt-1 text-xs text-slate-600">
                  SQLAlchemy 2.x, Alembic, Pydantic v2
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-5">
                <p className="text-xs font-medium text-slate-500">Frontend Stack</p>
                <p className="mt-1.5 text-base font-semibold text-slate-900">
                  Next.js · TypeScript
                </p>
                <p className="mt-1 text-xs text-slate-600">
                  Tailwind CSS, Zod, TanStack Query
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-5">
                <p className="text-xs font-medium text-slate-500">Geospatial Engine</p>
                <p className="mt-1.5 text-base font-semibold text-slate-900">
                  Cloud SQL + PostGIS
                </p>
                <p className="mt-1 text-xs text-slate-600">
                  Tenant-isolated RLS schema planned
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-5">
                <p className="text-xs font-medium text-slate-500">Current Build Stage</p>
                <p className="mt-1.5 text-base font-semibold text-[#14532d] tabular-nums">
                  Phase 1 Auth &amp; RLS Ready
                </p>
                <p className="mt-1 text-xs text-slate-600">
                  Awaiting external PostgreSQL verification
                </p>
              </div>
            </section>

            <section className="border-t border-slate-200 pt-10 space-y-6">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <h2 className="text-xl font-bold text-slate-900">
                    01. Initial Geography: The Gambia Administrative Regions
                  </h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Reference geography configured across shared TypeScript and FastAPI schemas.
                  </p>
                </div>
                <div className="relative w-full sm:w-64">
                  <Search
                    className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400"
                    aria-hidden="true"
                  />
                  <input
                    type="search"
                    value={regionQuery}
                    onChange={(e) => setRegionQuery(e.target.value)}
                    placeholder="Filter region or center..."
                    aria-label="Filter Gambian administrative regions"
                    className="w-full rounded-md border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#14532d] focus:outline-none focus:ring-2 focus:ring-[#14532d]/20"
                  />
                </div>
              </div>

              <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold text-slate-600">
                    <tr>
                      <th className="px-4 py-3">Region Code</th>
                      <th className="px-4 py-3">Administrative Region</th>
                      <th className="px-4 py-3">Administrative Center</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {filteredRegions.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="px-4 py-6 text-center text-sm text-slate-500">
                          No administrative regions match &ldquo;{regionQuery}&rdquo;.
                        </td>
                      </tr>
                    ) : (
                      filteredRegions.map((region) => (
                        <tr key={region.code} className="hover:bg-slate-50">
                          <td className="px-4 py-2.5 font-mono text-xs text-slate-700 tabular-nums">
                            {region.code}
                          </td>
                          <td className="px-4 py-2.5 font-medium text-slate-900">
                            {region.name}
                          </td>
                          <td className="px-4 py-2.5 text-slate-600">
                            {region.headquarters}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="border-t border-slate-200 pt-10 space-y-5">
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  02. Planned Role-Based Access Control Matrix
                </h2>
                <p className="mt-1 text-sm text-slate-600">
                  Eight initial roles enforced in Phase 1 backend authorization guards and
                  organization memberships.
                </p>
              </div>
              <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold text-slate-600">
                    <tr>
                      <th className="px-4 py-3">Role Identifier</th>
                      <th className="px-4 py-3">Display Title</th>
                      <th className="px-4 py-3">Tenant Scope</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {ROLE_DEFINITIONS.map((role) => (
                      <tr key={role.key} className="hover:bg-slate-50">
                        <td className="px-4 py-2.5 font-mono text-xs text-slate-700">
                          {role.key}
                        </td>
                        <td className="px-4 py-2.5 font-medium text-slate-900">
                          {role.label}
                        </td>
                        <td className="px-4 py-2.5 text-slate-600">{role.scope}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}

        {activeTab === 'architecture' && (
          <div className="space-y-10">
            <section className="space-y-3">
              <h1 className="text-2xl font-bold text-slate-900">
                Repository Architecture &amp; Environment Boundaries
              </h1>
              <p className="text-sm leading-relaxed text-slate-600 max-w-3xl">
                Google AI Studio Build Mode executes Node.js v22.23.2 and Vite on port 3000.
                Python 3.10.12 is present without pip, uvicorn, or PostgreSQL. Per architecture
                requirements, all FastAPI backend logic is preserved cleanly in{' '}
                <code className="font-mono text-xs text-slate-900">apps/api/</code> rather than
                substituting a Node.js backend.
              </p>
            </section>

            <section className="grid gap-6 lg:grid-cols-12">
              <div className="lg:col-span-5 rounded-lg border border-slate-200 bg-white overflow-hidden">
                <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 flex items-center gap-2 text-xs font-semibold text-slate-700">
                  <FolderTree className="h-4 w-4 text-[#14532d]" aria-hidden="true" />
                  <span>Monorepo Foundation Components</span>
                </div>
                <div className="divide-y divide-slate-200">
                  {MONOREPO_NODES.map((node) => {
                    const isSelected = node.path === selectedNode.path;
                    return (
                      <button
                        key={node.path}
                        type="button"
                        onClick={() => setSelectedNodePath(node.path)}
                        className={`w-full px-4 py-3 text-left flex items-center justify-between gap-3 transition-colors cursor-pointer ${
                          isSelected ? 'bg-emerald-50/70' : 'hover:bg-slate-50'
                        }`}
                      >
                        <div className="min-w-0">
                          <p className="font-mono text-xs font-medium text-slate-900 truncate">
                            {node.path}
                          </p>
                          <p className="text-xs text-slate-500 mt-0.5">{node.layer}</p>
                        </div>
                        <ChevronRight
                          className={`h-4 w-4 shrink-0 ${
                            isSelected ? 'text-[#14532d]' : 'text-slate-400'
                          }`}
                          aria-hidden="true"
                        />
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="lg:col-span-7 rounded-lg border border-slate-200 bg-white p-6 space-y-6">
                <div className="space-y-2 border-b border-slate-200 pb-4">
                  <p className="text-xs font-medium text-slate-500">
                    {selectedNode.layer} · {selectedNode.status}
                  </p>
                  <h2 className="font-mono text-base font-semibold text-slate-900">
                    {selectedNode.path}
                  </h2>
                </div>

                <p className="text-sm leading-relaxed text-slate-700">{selectedNode.summary}</p>

                <div className="grid gap-4 sm:grid-cols-2 text-sm pt-2">
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                      <Server className="h-4 w-4 text-[#14532d]" aria-hidden="true" />
                      <span>Target Runtime</span>
                    </div>
                    <p className="mt-1.5 font-mono text-xs text-slate-900">
                      {selectedNode.runtime}
                    </p>
                  </div>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                      <ShieldCheck className="h-4 w-4 text-[#14532d]" aria-hidden="true" />
                      <span>Phase 0 Verification</span>
                    </div>
                    <p className="mt-1.5 text-xs text-slate-700">{selectedNode.status}</p>
                  </div>
                </div>

                <div className="border-t border-slate-200 pt-5 space-y-3">
                  <h3 className="text-sm font-semibold text-slate-900">
                    Legacy Streamlit Source Inspection Status
                  </h3>
                  <p className="text-xs text-slate-600">
                    No legacy Streamlit files were present in the initial workspace. Once
                    supplied, reusable logic will be audited and refactored into FastAPI modules.
                  </p>
                  <div className="overflow-x-auto rounded-md border border-slate-200">
                    <table className="w-full text-left text-xs">
                      <thead className="border-b border-slate-200 bg-slate-50 font-semibold text-slate-600">
                        <tr>
                          <th className="px-3 py-2">Expected File</th>
                          <th className="px-3 py-2">Target Destination</th>
                          <th className="px-3 py-2">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200">
                        {STREAMLIT_MIGRATION_INVENTORY.map((item) => (
                          <tr key={item.file}>
                            <td className="px-3 py-2 font-mono text-slate-800">{item.file}</td>
                            <td className="px-3 py-2 text-slate-600">{item.target}</td>
                            <td className="px-3 py-2 text-amber-800 font-medium">{item.state}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </section>
          </div>
        )}

        {activeTab === 'api' && (
          <div className="space-y-8">
            <section className="space-y-2">
              <h1 className="text-2xl font-bold text-slate-900">
                Versioned REST API v1 Contract
              </h1>
              <p className="text-sm text-slate-600 max-w-3xl">
                Typed interfaces shared between FastAPI Pydantic v2 schemas (
                <code className="font-mono text-xs">apps/api/app/schemas/</code>) and frontend
                TypeScript contracts (
                <code className="font-mono text-xs">packages/shared-types/</code>).
              </p>
            </section>

            <section className="rounded-lg border border-slate-200 bg-white p-5 space-y-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                <div className="flex-1">
                  <label
                    htmlFor="api-base-url"
                    className="block text-xs font-semibold text-slate-700"
                  >
                    FastAPI Base URL (External / Local Python Runtime)
                  </label>
                  <input
                    id="api-base-url"
                    type="url"
                    value={apiBaseInput}
                    onChange={(e) => setApiBaseInput(e.target.value)}
                    className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-xs text-slate-900 focus:border-[#14532d] focus:outline-none focus:ring-2 focus:ring-[#14532d]/20"
                  />
                </div>
                <button
                  type="button"
                  onClick={runLiveEndpointCheck}
                  disabled={probeState.status === 'loading'}
                  className="rounded-lg bg-[#14532d] px-4 py-2 text-xs font-semibold text-white hover:bg-[#166534] disabled:opacity-60 transition-colors whitespace-nowrap shrink-0 cursor-pointer"
                >
                  Test Endpoint Connectivity
                </button>
              </div>

              {probeState.status !== 'idle' && (
                <div
                  className={`rounded-md border p-3 text-xs ${
                    probeState.status === 'success'
                      ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                  }`}
                >
                  <p className="font-medium">{probeState.message}</p>
                  {probeState.payload && (
                    <pre className="mt-2 overflow-x-auto font-mono text-[11px]">
                      {probeState.payload}
                    </pre>
                  )}
                </div>
              )}
            </section>

            <section className="grid gap-6 lg:grid-cols-12">
              <div className="lg:col-span-4 space-y-2">
                {API_V1_ENDPOINTS.map((endpoint) => {
                  const active = endpoint.id === selectedEndpoint.id;
                  return (
                    <button
                      key={endpoint.id}
                      type="button"
                      onClick={() => setSelectedEndpointId(endpoint.id)}
                      className={`w-full rounded-lg border p-4 text-left transition-colors cursor-pointer ${
                        active
                          ? 'border-[#14532d] bg-white'
                          : 'border-slate-200 bg-white hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center gap-2 text-xs font-mono">
                        <span className="font-semibold text-[#14532d]">{endpoint.method}</span>
                        <span className="text-slate-900">{endpoint.path}</span>
                      </div>
                      <p className="mt-1.5 text-xs text-slate-600">{endpoint.summary}</p>
                    </button>
                  );
                })}
              </div>

              <div className="lg:col-span-8 rounded-lg border border-slate-200 bg-white p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                  <div className="flex items-center gap-2 font-mono text-sm">
                    <FileCode2 className="h-4 w-4 text-[#14532d]" aria-hidden="true" />
                    <span className="font-semibold text-[#14532d]">
                      {selectedEndpoint.method}
                    </span>
                    <span className="text-slate-900">{selectedEndpoint.path}</span>
                  </div>
                  <span className="text-xs text-slate-500">Contract Schema Preview</span>
                </div>
                <p className="text-sm text-slate-600">{selectedEndpoint.summary}</p>
                <pre className="overflow-x-auto rounded-md border border-slate-200 bg-slate-950 p-4 font-mono text-xs text-slate-100 leading-relaxed">
                  {JSON.stringify(selectedEndpoint.sampleResponse, null, 2)}
                </pre>
              </div>
            </section>
          </div>
        )}

        {activeTab === 'roadmap' && (
          <div className="space-y-8">
            <section className="space-y-2">
              <h1 className="text-2xl font-bold text-slate-900">
                Controlled Phase Roadmap (Phases 0–7)
              </h1>
              <p className="text-sm text-slate-600 max-w-3xl">
                Each phase must pass database migrations, authorization checks, and automated
                tests before advancing. External Google Cloud setup requirements are tracked
                explicitly below.
              </p>
            </section>

            <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold text-slate-600">
                  <tr>
                    <th className="px-4 py-3">Phase</th>
                    <th className="px-4 py-3">Milestone</th>
                    <th className="px-4 py-3">Scope</th>
                    <th className="px-4 py-3">State</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {PHASE_ROADMAP.map((item) => (
                    <tr key={item.phase} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-mono text-xs font-medium text-slate-800 whitespace-nowrap tabular-nums">
                        {item.phase}
                      </td>
                      <td className="px-4 py-3 font-medium text-slate-900 whitespace-nowrap">
                        {item.title}
                      </td>
                      <td className="px-4 py-3 text-slate-600">{item.scope}</td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span
                          className={`text-xs font-semibold ${
                            item.status === 'Completed'
                              ? 'text-[#14532d]'
                              : 'text-slate-500'
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <section className="rounded-lg border border-slate-200 bg-white p-6 space-y-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                <Database className="h-4 w-4 text-[#14532d]" aria-hidden="true" />
                <span>External Infrastructure Prerequisites for Phase 1+</span>
              </div>
              <ul className="list-disc pl-5 space-y-1.5 text-sm text-slate-600">
                <li>
                  Provision PostgreSQL 15+ on Google Cloud SQL and execute{' '}
                  <code className="font-mono text-xs text-slate-800">
                    infrastructure/postgres-init.sql
                  </code>{' '}
                  to enable PostGIS.
                </li>
                <li>
                  Store <code className="font-mono text-xs text-slate-800">NOVA_DATABASE_URL</code>{' '}
                  and <code className="font-mono text-xs text-slate-800">NOVA_SECRET_KEY</code>{' '}
                  in Google Secret Manager.
                </li>
                <li>
                  Supply legacy Streamlit source files if business rules from{' '}
                  <code className="font-mono text-xs text-slate-800">crop_recommend.py</code> or{' '}
                  <code className="font-mono text-xs text-slate-800">i18n.py</code> should be
                  ported in Phases 1–6.
                </li>
              </ul>
            </section>
          </div>
        )}
      </main>

      <footer className="mt-16 border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-6 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <span>Nova AgriSense · Multi-Tenant Agricultural Intelligence Platform</span>
          <span>Phase 0 Architecture Foundation · The Gambia &amp; West Africa</span>
        </div>
      </footer>
    </div>
  );
}
