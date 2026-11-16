'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import type { ReactNode } from 'react';
import { useAuth } from '@/lib/auth-context';

export function WorkspaceShell({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const {
    user,
    isHydrating,
    activeOrganizationId,
    activeMemberships,
    activeMembership,
    isPlatformAdmin,
    selectOrganization,
    logout,
  } = useAuth();

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  if (isHydrating) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f8f9f7] px-6 text-sm text-slate-600">
        Restoring authenticated session...
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#f8f9f7] px-6 py-12">
        <div className="max-w-md rounded-lg border border-slate-200 bg-white p-8 text-center space-y-4">
          <h1 className="text-xl font-bold text-slate-900">Sign in required</h1>
          <p className="text-sm text-slate-600">
            Authenticate with your Nova AgriSense account to access your organization
            workspace.
          </p>
          <div className="flex items-center justify-center gap-3 pt-2">
            <Link
              href="/login"
              className="rounded-lg bg-[#14532d] px-4 py-2 text-sm font-semibold text-white hover:bg-[#166534]"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Register
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8f9f7] text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-4">
          <Link
            href="/dashboard"
            className="text-lg font-bold tracking-tight text-slate-900 whitespace-nowrap shrink-0"
          >
            Nova AgriSense
          </Link>

          <nav
            aria-label="Workspace navigation"
            className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600"
          >
            <Link
              href="/dashboard"
              className={`whitespace-nowrap shrink-0 ${
                pathname === '/dashboard'
                  ? 'text-[#14532d] underline underline-offset-4'
                  : 'hover:text-slate-900'
              }`}
            >
              Dashboard
            </Link>
            <Link
              href="/organizations"
              className={`whitespace-nowrap shrink-0 ${
                pathname === '/organizations'
                  ? 'text-[#14532d] underline underline-offset-4'
                  : 'hover:text-slate-900'
              }`}
            >
              Organizations
            </Link>
            <Link
              href="/profile"
              className={`whitespace-nowrap shrink-0 ${
                pathname === '/profile'
                  ? 'text-[#14532d] underline underline-offset-4'
                  : 'hover:text-slate-900'
              }`}
            >
              Account
            </Link>
            {isPlatformAdmin && (
              <Link
                href="/admin"
                className={`whitespace-nowrap shrink-0 ${
                  pathname === '/admin'
                    ? 'text-[#14532d] underline underline-offset-4'
                    : 'hover:text-slate-900'
                }`}
              >
                Platform Admin
              </Link>
            )}
          </nav>

          <div className="flex items-center gap-3 shrink-0">
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 whitespace-nowrap shrink-0 cursor-pointer"
            >
              Sign Out
            </button>
          </div>
        </div>
        <nav
          aria-label="Mobile workspace navigation"
          className="flex md:hidden items-center gap-4 overflow-x-auto border-t border-slate-100 px-6 py-2.5 text-xs font-medium text-slate-600"
        >
          <Link
            href="/dashboard"
            className={`whitespace-nowrap shrink-0 ${
              pathname === '/dashboard'
                ? 'text-[#14532d] font-semibold underline underline-offset-4'
                : 'hover:text-slate-900'
            }`}
          >
            Dashboard
          </Link>
          <Link
            href="/organizations"
            className={`whitespace-nowrap shrink-0 ${
              pathname === '/organizations'
                ? 'text-[#14532d] font-semibold underline underline-offset-4'
                : 'hover:text-slate-900'
            }`}
          >
            Organizations
          </Link>
          <Link
            href="/profile"
            className={`whitespace-nowrap shrink-0 ${
              pathname === '/profile'
                ? 'text-[#14532d] font-semibold underline underline-offset-4'
                : 'hover:text-slate-900'
            }`}
          >
            Account
          </Link>
          {isPlatformAdmin && (
            <Link
              href="/admin"
              className={`whitespace-nowrap shrink-0 ${
                pathname === '/admin'
                  ? 'text-[#14532d] font-semibold underline underline-offset-4'
                  : 'hover:text-slate-900'
              }`}
            >
              Platform Admin
            </Link>
          )}
        </nav>
      </header>

      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-6 py-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-xs text-slate-600">
            <span className="font-semibold text-slate-900">{title}</span>
            <span className="mx-2 text-slate-400">·</span>
            <span>{user.full_name}</span>
            {activeMembership && (
              <>
                <span className="mx-2 text-slate-400">·</span>
                <span className="font-mono">{activeMembership.role}</span>
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            <label htmlFor="org-selector" className="text-xs font-medium text-slate-600">
              Organization:
            </label>
            {activeMemberships.length > 0 ? (
              <select
                id="org-selector"
                value={activeOrganizationId ?? ''}
                onChange={(e) => selectOrganization(e.target.value)}
                className="rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-900 focus:border-[#14532d] focus:outline-none"
              >
                {activeMemberships.map((m) => (
                  <option key={m.organization_id} value={m.organization_id}>
                    {m.organization_name} ({m.role})
                  </option>
                ))}
              </select>
            ) : (
              <span className="text-xs text-slate-500">No active organization</span>
            )}
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-6xl px-6 py-8 space-y-8">{children}</main>
    </div>
  );
}
