'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import {
  GAMBIA_REGIONS,
  ORGANIZATION_ROLE_DEFINITIONS,
  ORGANIZATION_TYPES,
} from '@nova-agrisense/shared-config';
import type { OrganizationRole, OrganizationType } from '@nova-agrisense/shared-types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { WorkspaceShell } from '@/components/WorkspaceShell';
import { ApiClientError, apiClient } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';

const createOrgSchema = z.object({
  name: z.string().min(2, 'Organization name must be at least 2 characters.'),
  organization_type: z.enum([
    'cooperative',
    'ngo',
    'government_department',
    'research_institute',
    'private_agribusiness',
  ]),
  region: z.string().min(2, 'Select a region.'),
  district: z.string().optional(),
  contact_email: z.string().email('Invalid contact email').optional().or(z.literal('')),
});

type CreateOrgFormValues = z.infer<typeof createOrgSchema>;

const addMemberSchema = z.object({
  email: z.string().email('Enter the registered user email.'),
  role: z.enum([
    'ORGANIZATION_ADMIN',
    'AGRICULTURAL_OFFICER',
    'DATA_MANAGER',
    'RESEARCHER',
    'COOPERATIVE_MANAGER',
    'FARMER',
    'READ_ONLY_ANALYST',
  ]),
  status: z.enum(['active', 'invited']),
});

type AddMemberFormValues = z.infer<typeof addMemberSchema>;

export default function OrganizationsPage() {
  const queryClient = useQueryClient();
  const {
    activeOrganizationId,
    activeMembership,
    hasPermission,
    refreshProfile,
    selectOrganization,
  } = useAuth();

  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const canReadMembers = hasPermission('membership:read');
  const canManageMembers = hasPermission('membership:manage');
  const canReadAudit = hasPermission('audit:read');

  const membersQuery = useQuery({
    queryKey: ['org-members', activeOrganizationId],
    queryFn: () => apiClient.listMembers(activeOrganizationId!),
    enabled: Boolean(activeOrganizationId && canReadMembers),
  });

  const auditQuery = useQuery({
    queryKey: ['org-audit', activeOrganizationId],
    queryFn: () => apiClient.listAuditLogs(activeOrganizationId!),
    enabled: Boolean(activeOrganizationId && canReadAudit),
  });

  const createOrgForm = useForm<CreateOrgFormValues>({
    resolver: zodResolver(createOrgSchema),
    defaultValues: {
      organization_type: 'cooperative',
      region: 'Lower River Region',
    },
  });

  const addMemberForm = useForm<AddMemberFormValues>({
    resolver: zodResolver(addMemberSchema),
    defaultValues: {
      role: 'AGRICULTURAL_OFFICER',
      status: 'invited',
    },
  });

  const createOrgMutation = useMutation({
    mutationFn: (values: CreateOrgFormValues) =>
      apiClient.createOrganization({
        name: values.name,
        organization_type: values.organization_type as OrganizationType,
        region: values.region,
        district: values.district || undefined,
        contact_email: values.contact_email || undefined,
      }),
    onSuccess: async (created) => {
      setActionError(null);
      setActionSuccess(`Organization "${created.name}" created.`);
      createOrgForm.reset();
      await refreshProfile();
      selectOrganization(created.id);
    },
    onError: (err) => {
      setActionSuccess(null);
      setActionError(err instanceof ApiClientError ? err.message : 'Failed to create organization.');
    },
  });

  const addMemberMutation = useMutation({
    mutationFn: (values: AddMemberFormValues) =>
      apiClient.addMember(activeOrganizationId!, {
        email: values.email,
        role: values.role as OrganizationRole,
        status: values.status,
      }),
    onSuccess: () => {
      setActionError(null);
      setActionSuccess('Member added to organization.');
      addMemberForm.reset({ role: 'AGRICULTURAL_OFFICER', status: 'invited', email: '' });
      queryClient.invalidateQueries({ queryKey: ['org-members', activeOrganizationId] });
      queryClient.invalidateQueries({ queryKey: ['org-audit', activeOrganizationId] });
    },
    onError: (err) => {
      setActionSuccess(null);
      setActionError(err instanceof ApiClientError ? err.message : 'Unable to add member.');
    },
  });

  const updateRoleMutation = useMutation({
    mutationFn: ({ membershipId, role }: { membershipId: string; role: OrganizationRole }) =>
      apiClient.updateMemberRole(activeOrganizationId!, membershipId, role),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ['org-members', activeOrganizationId] });
      queryClient.invalidateQueries({ queryKey: ['org-audit', activeOrganizationId] });
    },
    onError: (err) => {
      setActionError(err instanceof ApiClientError ? err.message : 'Role update failed.');
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (membershipId: string) =>
      apiClient.deactivateMember(activeOrganizationId!, membershipId),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ['org-members', activeOrganizationId] });
      queryClient.invalidateQueries({ queryKey: ['org-audit', activeOrganizationId] });
    },
    onError: (err) => {
      setActionError(err instanceof ApiClientError ? err.message : 'Deactivation failed.');
    },
  });

  return (
    <WorkspaceShell title="Organizations & Memberships">
      {(actionError || actionSuccess) && (
        <div
          className={`rounded-md border p-3 text-xs ${
            actionError
              ? 'border-red-200 bg-red-50 text-red-900'
              : 'border-emerald-200 bg-emerald-50 text-emerald-900'
          }`}
        >
          {actionError || actionSuccess}
        </div>
      )}

      <section className="rounded-lg border border-slate-200 bg-white p-6 space-y-4">
        <h2 className="text-lg font-bold text-slate-900">Create Organization</h2>
        <form
          onSubmit={createOrgForm.handleSubmit((v) => createOrgMutation.mutate(v))}
          className="grid gap-4 sm:grid-cols-2"
        >
          <div>
            <label htmlFor="org-name" className="block text-xs font-medium text-slate-700">
              Organization Name
            </label>
            <input
              id="org-name"
              type="text"
              {...createOrgForm.register('name')}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
            {createOrgForm.formState.errors.name && (
              <p className="mt-1 text-xs text-red-700">
                {createOrgForm.formState.errors.name.message}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="org-type" className="block text-xs font-medium text-slate-700">
              Organization Type
            </label>
            <select
              id="org-type"
              {...createOrgForm.register('organization_type')}
              className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              {ORGANIZATION_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="org-region" className="block text-xs font-medium text-slate-700">
              Region
            </label>
            <select
              id="org-region"
              {...createOrgForm.register('region')}
              className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              {GAMBIA_REGIONS.map((r) => (
                <option key={r.code} value={r.name}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="org-district" className="block text-xs font-medium text-slate-700">
              District (optional)
            </label>
            <input
              id="org-district"
              type="text"
              {...createOrgForm.register('district')}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </div>

          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={createOrgMutation.isPending}
              className="rounded-lg bg-[#14532d] px-4 py-2 text-xs font-semibold text-white hover:bg-[#166534] cursor-pointer"
            >
              {createOrgMutation.isPending ? 'Creating...' : 'Create Organization'}
            </button>
          </div>
        </form>
      </section>

      {activeOrganizationId && activeMembership && (
        <section className="rounded-lg border border-slate-200 bg-white p-6 space-y-6">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              Members — {activeMembership.organization_name}
            </h2>
            <p className="text-xs text-slate-500">
              Tenant-isolated membership roster enforced by X-Organization-ID and PostgreSQL RLS.
            </p>
          </div>

          {canManageMembers && (
            <form
              onSubmit={addMemberForm.handleSubmit((v) => addMemberMutation.mutate(v))}
              className="grid gap-3 rounded-md border border-slate-200 bg-slate-50 p-4 sm:grid-cols-4 items-end"
            >
              <div className="sm:col-span-2">
                <label htmlFor="member-email" className="block text-xs font-medium text-slate-700">
                  Registered User Email
                </label>
                <input
                  id="member-email"
                  type="email"
                  {...addMemberForm.register('email')}
                  className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm"
                />
              </div>
              <div>
                <label htmlFor="member-role" className="block text-xs font-medium text-slate-700">
                  Role
                </label>
                <select
                  id="member-role"
                  {...addMemberForm.register('role')}
                  className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm"
                >
                  {ORGANIZATION_ROLE_DEFINITIONS.map((r) => (
                    <option key={r.key} value={r.key}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </div>
              <button
                type="submit"
                disabled={addMemberMutation.isPending}
                className="rounded-md bg-[#14532d] px-3 py-2 text-xs font-semibold text-white hover:bg-[#166534] cursor-pointer"
              >
                Invite / Add
              </button>
            </form>
          )}

          {!canReadMembers ? (
            <p className="text-sm text-slate-600">
              Your role ({activeMembership.role}) does not include membership roster access.
            </p>
          ) : membersQuery.isLoading ? (
            <p className="text-sm text-slate-500">Loading organization members...</p>
          ) : membersQuery.isError ? (
            <p className="text-sm text-red-700">Failed to load organization members.</p>
          ) : (
            <div className="overflow-x-auto rounded-md border border-slate-200">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold text-slate-600">
                  <tr>
                    <th className="px-4 py-2.5">Name</th>
                    <th className="px-4 py-2.5">Email</th>
                    <th className="px-4 py-2.5">Role</th>
                    <th className="px-4 py-2.5">Status</th>
                    {canManageMembers && <th className="px-4 py-2.5">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {(membersQuery.data ?? []).map((member) => (
                    <tr key={member.id}>
                      <td className="px-4 py-2.5 font-medium text-slate-900">
                        {member.full_name}
                      </td>
                      <td className="px-4 py-2.5 text-slate-600">{member.email}</td>
                      <td className="px-4 py-2.5">
                        {canManageMembers && member.status !== 'deactivated' ? (
                          <select
                            aria-label={`Role for ${member.email}`}
                            value={member.role}
                            onChange={(e) =>
                              updateRoleMutation.mutate({
                                membershipId: member.id,
                                role: e.target.value as OrganizationRole,
                              })
                            }
                            className="rounded border border-slate-300 bg-white px-2 py-1 font-mono text-xs"
                          >
                            {ORGANIZATION_ROLE_DEFINITIONS.map((r) => (
                              <option key={r.key} value={r.key}>
                                {r.key}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <span className="font-mono text-xs">{member.role}</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs text-slate-700">
                        {member.status}
                      </td>
                      {canManageMembers && (
                        <td className="px-4 py-2.5">
                          {member.status !== 'deactivated' && (
                            <button
                              type="button"
                              onClick={() => deactivateMutation.mutate(member.id)}
                              className="text-xs font-medium text-red-700 hover:underline cursor-pointer"
                            >
                              Deactivate
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {activeOrganizationId && canReadAudit && (
        <section className="rounded-lg border border-slate-200 bg-white p-6 space-y-4">
          <h2 className="text-lg font-bold text-slate-900">Organization Audit Events</h2>
          {auditQuery.isLoading ? (
            <p className="text-sm text-slate-500">Loading audit events...</p>
          ) : (
            <div className="overflow-x-auto rounded-md border border-slate-200">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-200 bg-slate-50 font-semibold text-slate-600">
                  <tr>
                    <th className="px-3 py-2">Timestamp (UTC)</th>
                    <th className="px-3 py-2">Action</th>
                    <th className="px-3 py-2">Resource</th>
                    <th className="px-3 py-2">Request ID</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {(auditQuery.data ?? []).map((entry) => (
                    <tr key={entry.id}>
                      <td className="px-3 py-2 font-mono text-slate-600 tabular-nums">
                        {entry.timestamp}
                      </td>
                      <td className="px-3 py-2 font-mono font-medium text-slate-900">
                        {entry.action}
                      </td>
                      <td className="px-3 py-2 text-slate-700">{entry.resource_type}</td>
                      <td className="px-3 py-2 font-mono text-slate-500">
                        {entry.request_id ?? '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </WorkspaceShell>
  );
}
