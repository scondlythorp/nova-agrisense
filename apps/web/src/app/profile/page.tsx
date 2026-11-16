'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { WorkspaceShell } from '@/components/WorkspaceShell';
import { ApiClientError, apiClient } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';

const passwordSchema = z.object({
  current_password: z.string().min(1, 'Current password is required.'),
  new_password: z
    .string()
    .min(12, 'New password must be at least 12 characters.')
    .regex(/[a-z]/, 'Include a lowercase letter.')
    .regex(/[A-Z]/, 'Include an uppercase letter.')
    .regex(/\d/, 'Include a digit.'),
});

type PasswordFormValues = z.infer<typeof passwordSchema>;

export default function ProfilePage() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
  });

  const onSubmit = async (values: PasswordFormValues) => {
    setErrorMessage(null);
    try {
      await apiClient.changePassword(values);
      reset();
      await logout();
      router.push('/login?password_changed=1');
    } catch (err) {
      setErrorMessage(
        err instanceof ApiClientError ? err.message : 'Unable to update password.',
      );
    }
  };

  return (
    <WorkspaceShell title="Account & Security">
      <section className="rounded-lg border border-slate-200 bg-white p-6 space-y-3">
        <h1 className="text-xl font-bold text-slate-900">User Profile</h1>
        <div className="grid gap-4 sm:grid-cols-4 text-sm pt-2">
          <div>
            <p className="text-xs text-slate-500">Full Name</p>
            <p className="mt-1 font-medium text-slate-900">{user?.full_name}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Normalized Email</p>
            <p className="mt-1 font-mono text-xs text-slate-900">{user?.email}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Verification Status</p>
            <p className="mt-1 font-mono text-xs text-slate-900">
              {user?.is_verified ? 'Verified' : 'Unverified (Phase 1)'}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Platform Role</p>
            <p className="mt-1 font-mono text-xs text-slate-900">
              {user?.platform_role ?? 'Standard User'}
            </p>
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 max-w-lg space-y-4">
        <h2 className="text-lg font-bold text-slate-900">Change Password</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div>
            <label htmlFor="current_password" className="block text-xs font-medium text-slate-700">
              Current Password
            </label>
            <input
              id="current_password"
              type="password"
              {...register('current_password')}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
            {errors.current_password && (
              <p className="mt-1 text-xs text-red-700">{errors.current_password.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="new_password" className="block text-xs font-medium text-slate-700">
              New Password
            </label>
            <input
              id="new_password"
              type="password"
              {...register('new_password')}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
            {errors.new_password && (
              <p className="mt-1 text-xs text-red-700">{errors.new_password.message}</p>
            )}
          </div>

          {errorMessage && (
            <p className="text-xs text-red-700">{errorMessage}</p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-lg bg-[#14532d] px-4 py-2 text-xs font-semibold text-white hover:bg-[#166534] cursor-pointer"
          >
            Update Password
          </button>
        </form>
      </section>
    </WorkspaceShell>
  );
}
