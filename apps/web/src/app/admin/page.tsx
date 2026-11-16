'use client';

import { useQuery } from '@tanstack/react-query';
import { WorkspaceShell } from '@/components/WorkspaceShell';
import { ApiClientError, apiClient } from '@/lib/api-client';

export default function PlatformAdminPage() {
  const orgsQuery = useQuery({
    queryKey: ['admin-orgs'],
    queryFn: apiClient.adminListOrganizations,
    retry: false,
  });

  return (
    <WorkspaceShell title="Platform Administration">
      {orgsQuery.isLoading && (
        <p className="text-sm text-slate-500">Loading platform organizations...</p>
      )}
      {orgsQuery.isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-900">
          {orgsQuery.error instanceof ApiClientError
            ? orgsQuery.error.message
            : 'Platform administrator access denied.'}
        </div>
      )}
      {orgsQuery.data && (
        <section className="rounded-lg border border-slate-200 bg-white p-6 space-y-4">
          <h1 className="text-xl font-bold text-slate-900">All Registered Organizations</h1>
          <div className="overflow-x-auto rounded-md border border-slate-200">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold text-slate-600">
                <tr>
                  <th className="px-4 py-2.5">Name</th>
                  <th className="px-4 py-2.5">Slug</th>
                  <th className="px-4 py-2.5">Type</th>
                  <th className="px-4 py-2.5">Region</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {orgsQuery.data.map((org) => (
                  <tr key={org.id}>
                    <td className="px-4 py-2.5 font-medium text-slate-900">{org.name}</td>
                    <td className="px-4 py-2.5 font-mono text-xs text-slate-600">{org.slug}</td>
                    <td className="px-4 py-2.5 text-slate-600">{org.organization_type}</td>
                    <td className="px-4 py-2.5 text-slate-600">{org.region}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </WorkspaceShell>
  );
}
