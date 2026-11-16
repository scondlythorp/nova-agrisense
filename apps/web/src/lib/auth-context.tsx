'use client';

import type {
  MembershipSummary,
  UserProfileResponse,
} from '@nova-agrisense/shared-types';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import {
  apiClient,
  setActiveOrganizationId,
  setInMemoryAccessToken,
} from './api-client';

interface AuthContextValue {
  user: UserProfileResponse | null;
  isHydrating: boolean;
  activeOrganizationId: string | null;
  activeMembership: MembershipSummary | null;
  activeMemberships: MembershipSummary[];
  pendingInvitations: MembershipSummary[];
  hasPermission: (permission: string) => boolean;
  isPlatformAdmin: boolean;
  login: (email: string, password: string) => Promise<UserProfileResponse>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<UserProfileResponse | null>;
  selectOrganization: (organizationId: string) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function pickDefaultOrgId(
  user: UserProfileResponse | null,
  currentId: string | null,
): string | null {
  if (!user) return null;
  const active = user.memberships.filter((m) => m.status === 'active');
  if (active.length === 0) return null;
  if (currentId && active.some((m) => m.organization_id === currentId)) {
    return currentId;
  }
  return active[0].organization_id;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfileResponse | null>(null);
  const [isHydrating, setIsHydrating] = useState(true);
  const [orgId, setOrgId] = useState<string | null>(null);

  const applyUserSession = useCallback((nextUser: UserProfileResponse | null) => {
    setUser(nextUser);
    setOrgId((prev) => {
      const nextOrg = pickDefaultOrgId(nextUser, prev);
      setActiveOrganizationId(nextOrg);
      return nextOrg;
    });
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const refreshed = await apiClient.refresh();
        if (active && refreshed) {
          applyUserSession(refreshed.user);
        }
      } catch {
        if (active) {
          setInMemoryAccessToken(null);
          applyUserSession(null);
        }
      } finally {
        if (active) setIsHydrating(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [applyUserSession]);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await apiClient.login({ email, password });
      applyUserSession(res.user);
      return res.user;
    },
    [applyUserSession],
  );

  const logout = useCallback(async () => {
    try {
      await apiClient.logout();
    } finally {
      applyUserSession(null);
    }
  }, [applyUserSession]);

  const refreshProfile = useCallback(async () => {
    try {
      const profile = await apiClient.getMe();
      applyUserSession(profile);
      return profile;
    } catch {
      return null;
    }
  }, [applyUserSession]);

  const selectOrganization = useCallback((organizationId: string) => {
    setActiveOrganizationId(organizationId);
    setOrgId(organizationId);
  }, []);

  const activeMemberships = useMemo(
    () => (user?.memberships ?? []).filter((m) => m.status === 'active'),
    [user],
  );

  const pendingInvitations = useMemo(
    () => (user?.memberships ?? []).filter((m) => m.status === 'invited'),
    [user],
  );

  const activeMembership = useMemo(
    () => activeMemberships.find((m) => m.organization_id === orgId) ?? null,
    [activeMemberships, orgId],
  );

  const hasPermission = useCallback(
    (permission: string) => {
      if (!activeMembership) return false;
      return activeMembership.permissions.includes(permission);
    },
    [activeMembership],
  );

  const value: AuthContextValue = {
    user,
    isHydrating,
    activeOrganizationId: orgId,
    activeMembership,
    activeMemberships,
    pendingInvitations,
    hasPermission,
    isPlatformAdmin: user?.platform_role === 'PLATFORM_ADMIN',
    login,
    logout,
    refreshProfile,
    selectOrganization,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return ctx;
}
