import Link from 'next/link';
import { GAMBIA_REGIONS } from '@nova-agrisense/shared-config';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#f8f9f7] text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-8 px-6 py-4">
          <Link
            href="/"
            className="text-lg font-bold tracking-tight text-slate-900 whitespace-nowrap shrink-0"
          >
            Nova AgriSense
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
            <a
              href="#platform"
              className="hover:text-slate-900 hover:underline underline-offset-4 whitespace-nowrap shrink-0"
            >
              Platform
            </a>
            <a
              href="#regions"
              className="hover:text-slate-900 hover:underline underline-offset-4 whitespace-nowrap shrink-0"
            >
              Coverage
            </a>
            <Link
              href="/dashboard"
              className="hover:text-slate-900 hover:underline underline-offset-4 whitespace-nowrap shrink-0"
            >
              Workspace
            </Link>
          </nav>

          <div className="shrink-0">
            <Link
              href="/login"
              className="inline-flex items-center rounded-lg bg-[#14532d] px-4 py-2 text-xs font-semibold text-white hover:bg-[#166534] transition-colors whitespace-nowrap shrink-0"
            >
              Sign In
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-14 space-y-16">
        <section className="max-w-3xl space-y-5">
          <p className="text-xs font-medium text-slate-500">
            The Gambia · West Africa Expansion Architecture · Phase 0 Foundation
          </p>
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl text-balance">
            Structured agricultural intelligence for cooperatives, officers, and researchers.
          </h1>
          <p className="text-base leading-relaxed text-slate-600">
            Nova AgriSense unifies farmer registries, farm and plot boundaries, seasonal
            production records, and validated data imports on a multi-tenant PostgreSQL
            and FastAPI platform built for low-bandwidth field conditions.
          </p>
          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Link
              href="/dashboard"
              className="inline-flex items-center rounded-lg bg-[#14532d] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#166534] transition-colors whitespace-nowrap"
            >
              Open Workspace
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors whitespace-nowrap"
            >
              Organization Login
            </Link>
          </div>
        </section>

        <section id="platform" className="border-t border-slate-200 pt-10">
          <h2 className="text-xl font-semibold text-slate-900">Core Platform Capabilities</h2>
          <div className="mt-6 grid gap-6 md:grid-cols-3">
            <div className="rounded-lg border border-slate-200 bg-white p-6">
              <h3 className="text-base font-semibold text-slate-900">
                01. Multi-Tenant Isolation
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                Strict organization boundaries across cooperatives, NGOs, and agricultural
                departments enforced at both API authorization and PostgreSQL schema levels.
              </p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-6">
              <h3 className="text-base font-semibold text-slate-900">
                02. Validated Field Ingestion
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                Manual mobile-first entry alongside staged CSV and Excel imports with
                duplicate detection and rejected-row reporting prior to production commit.
              </p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-6">
              <h3 className="text-base font-semibold text-slate-900">
                03. Traceable Analytics
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                Every seasonal yield metric and recommendation identifies its source records,
                collection timeframe, and methodological limitations.
              </p>
            </div>
          </div>
        </section>

        <section id="regions" className="border-t border-slate-200 pt-10">
          <h2 className="text-xl font-semibold text-slate-900">
            Initial Administrative Coverage: The Gambia
          </h2>
          <div className="mt-6 overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold text-slate-600">
                <tr>
                  <th className="px-4 py-3">Code</th>
                  <th className="px-4 py-3">Region / Municipality</th>
                  <th className="px-4 py-3">Administrative Center</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {GAMBIA_REGIONS.map((region) => (
                  <tr key={region.code} className="hover:bg-slate-50">
                    <td className="px-4 py-2.5 font-mono text-xs text-slate-700 tabular-nums">
                      {region.code}
                    </td>
                    <td className="px-4 py-2.5 font-medium text-slate-900">{region.name}</td>
                    <td className="px-4 py-2.5 text-slate-600">{region.headquarters}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}
