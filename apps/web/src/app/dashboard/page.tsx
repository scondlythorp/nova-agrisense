'use client';

import { useMutation } from '@tanstack/react-query';
import Link from 'next/link';
import { WorkspaceShell } from '@/components/WorkspaceShell';
import { apiClient } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';

export default function DashboardPage() {
  const {
    user,
    activeMembership,
    pendingInvitations,
    refreshProfile,
    selectOrganization,
  } = useAuth();

  const acceptMutation = useMutation({
    mutationFn: (orgId: string) => apiClient.acceptInvitation(orgId),
    onSuccess: async (accepted) => {
      await refreshProfile();
      selectOrganization(accepted.organization_id);
    },
  });

  return (
    <WorkspaceShell title="Workspace Overview">
      {pendingInvitations.length > 0 && (
        <section className="rounded-lg border border-amber-200 bg-amber-50 p-5 space-y-3">
          <h2 className="text-sm font-semibold text-amber-950">
            Pending Organization Invitations
          </h2>
          <div className="divide-y divide-amber-200">
            {pendingInvitations.map((invite) => (
              <div
                key={invite.id}
                className="flex flex-col gap-2 py-2.5 sm:flex-row sm:items-center sm:justify-between text-sm"
              >
                <div>
                  <span className="font-medium text-amber-950">
                    {invite.organization_name}
                  </span>
                  <span className="mx-2 text-amber-700">·</span>
                  <span className="font-mono text-xs text-amber-900">{invite.role}</span>
                </div>
                <button
                  type="button"
                  onClick={() => acceptMutation.mutate(invite.organization_id)}
                  disabled={acceptMutation.isPending}
                  className="rounded-md bg-[#14532d] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#166534] cursor-pointer"
                >
                  Accept Invitation
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {!activeMembership ? (
        <section className="rounded-lg border border-slate-200 bg-white p-6 space-y-3">
          <h1 className="text-xl font-bold text-slate-900">
            No Active Organization Selected
          </h1>
          <p className="text-sm text-slate-600">
            Create an organization or accept an administrator invitation to establish an
            isolated tenant context.
          </p>
          <div className="pt-2">
            <Link
              href="/organizations"
              className="inline-flex rounded-lg bg-[#14532d] px-4 py-2 text-sm font-semibold text-white hover:bg-[#166534]"
            >
              Manage Organizations
            </Link>
          </div>
        </section>
      ) : (
        <section className="rounded-lg border border-slate-200 bg-white p-6 space-y-5">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-4">
            <div>
              <p className="text-xs text-slate-500">
                Active Tenant Context · {activeMembership.organization_type}
              </p>
              <h1 className="text-2xl font-bold text-slate-900">
                {activeMembership.organization_name}
              </h1>
            </div>
            <Link
              href="/organizations"
              className="rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            >
              Organization Settings
            </Link>
          </div>

          <div className="grid gap-4 sm:grid-cols-3 text-sm">
            <div>
              <p className="text-xs text-slate-500">Organization ID</p>
              <p className="mt-1 font-mono text-xs text-slate-900">
                {activeMembership.organization_id}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Assigned Role</p>
              <p className="mt-1 font-mono text-xs font-semibold text-[#14532d]">
                {activeMembership.role}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Signed-In User</p>
              <p className="mt-1 text-xs font-medium text-slate-900">{user?.email}</p>
            </div>
          </div>

          <div className="border-t border-slate-200 pt-4">
            <h2 className="text-sm font-semibold text-slate-900">
              Server-Granted Role Permissions
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Returned by FastAPI for UI visibility. All authorization is enforced server-side.
            </p>
            <div className="mt-3 grid gap-2 sm:grid-cols-3">
              {activeMembership.permissions.map((perm) => (
                <div
                  key={perm}
                  className="rounded border border-slate-200 bg-slate-50 px-3 py-1.5 font-mono text-xs text-slate-700"
                >
                  {perm}
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </WorkspaceShell>
  );
}
