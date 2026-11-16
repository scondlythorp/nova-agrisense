import type {
  ApiErrorResponse,
  AuditLogResponse,
  AuthTokenResponse,
  HealthResponse,
  LogoutResponse,
  OrganizationMemberResponse,
  OrganizationResponse,
  OrganizationRole,
  OrganizationType,
  OrganizationWithRoleResponse,
  PlatformMetaResponse,
  ReadinessResponse,
  UserProfileResponse,
} from '@nova-agrisense/shared-types';
import { webEnv } from './env';

export class ApiClientError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly requestId: string;

  constructor(status: number, code: string, message: string, requestId: string) {
    super(message);
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

export function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${escaped}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

let inMemoryAccessToken: string | null = null;
let inMemoryCsrfToken: string | null = null;
let activeOrganizationId: string | null = null;
let refreshPromise: Promise<AuthTokenResponse | null> | null = null;

export function setInMemoryAccessToken(token: string | null): void {
  inMemoryAccessToken = token;
}

export function getInMemoryAccessToken(): string | null {
  return inMemoryAccessToken;
}

export function setInMemoryCsrfToken(token: string | null): void {
  inMemoryCsrfToken = token;
}

export function getInMemoryCsrfToken(): string | null {
  return inMemoryCsrfToken;
}

export function setActiveOrganizationId(orgId: string | null): void {
  activeOrganizationId = orgId;
}

export function getActiveOrganizationId(): string | null {
  return activeOrganizationId;
}

interface RequestOptions extends RequestInit {
  skipAuthRetry?: boolean;
  includeOrgHeader?: boolean;
  includeCsrf?: boolean;
}

async function parseErrorResponse(response: Response): Promise<ApiClientError> {
  let parsed: ApiErrorResponse | null = null;
  try {
    parsed = (await response.json()) as ApiErrorResponse;
  } catch {
    parsed = null;
  }
  return new ApiClientError(
    response.status,
    parsed?.error?.code ?? `http_${response.status}`,
    parsed?.error?.message ?? 'API request failed.',
    parsed?.error?.request_id ?? 'unknown',
  );
}

async function performRefresh(): Promise<AuthTokenResponse | null> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const csrf = inMemoryCsrfToken ?? readCookie('nova_csrf_token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (csrf) {
        headers['X-CSRF-Token'] = csrf;
      }
      const res = await fetch(`${webEnv.NEXT_PUBLIC_API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers,
        credentials: 'include',
      });
      if (!res.ok) {
        inMemoryAccessToken = null;
        inMemoryCsrfToken = null;
        return null;
      }
      const data = (await res.json()) as AuthTokenResponse;
      inMemoryAccessToken = data.access_token;
      if (data.csrf_token) {
        inMemoryCsrfToken = data.csrf_token;
      }
      return data;
    })().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const {
    skipAuthRetry = false,
    includeOrgHeader = false,
    includeCsrf = false,
    headers: customHeaders,
    ...init
  } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((customHeaders as Record<string, string> | undefined) ?? {}),
  };

  if (inMemoryAccessToken && !headers.Authorization) {
    headers.Authorization = `Bearer ${inMemoryAccessToken}`;
  }
  if (includeOrgHeader && activeOrganizationId && !headers['X-Organization-ID']) {
    headers['X-Organization-ID'] = activeOrganizationId;
  }
  if (includeCsrf) {
    const csrf = inMemoryCsrfToken ?? readCookie('nova_csrf_token');
    if (csrf) {
      headers['X-CSRF-Token'] = csrf;
    }
  }

  const url = `${webEnv.NEXT_PUBLIC_API_BASE_URL}${path}`;
  const response = await fetch(url, {
    ...init,
    headers,
    credentials: 'include',
  });

  if (response.status === 401 && !skipAuthRetry && inMemoryAccessToken) {
    const refreshed = await performRefresh();
    if (refreshed) {
      return requestJson<T>(path, { ...options, skipAuthRetry: true });
    }
  }

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const apiClient = {
  getHealth: () => requestJson<HealthResponse>('/health', { skipAuthRetry: true }),
  getReadiness: () => requestJson<ReadinessResponse>('/health/ready', { skipAuthRetry: true }),
  getMeta: () => requestJson<PlatformMetaResponse>('/meta', { skipAuthRetry: true }),

  // Authentication
  register: (payload: {
    email: string;
    password: string;
    full_name: string;
    phone_number?: string;
  }) =>
    requestJson<UserProfileResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
      skipAuthRetry: true,
    }),

  login: async (payload: { email: string; password: string }) => {
    const res = await requestJson<AuthTokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
      skipAuthRetry: true,
    });
    setInMemoryAccessToken(res.access_token);
    if (res.csrf_token) {
      setInMemoryCsrfToken(res.csrf_token);
    }
    return res;
  },

  refresh: () => performRefresh(),

  logout: async () => {
    try {
      return await requestJson<LogoutResponse>('/auth/logout', {
        method: 'POST',
        includeCsrf: true,
        skipAuthRetry: true,
      });
    } finally {
      setInMemoryAccessToken(null);
      setInMemoryCsrfToken(null);
      setActiveOrganizationId(null);
    }
  },

  getMe: () => requestJson<UserProfileResponse>('/auth/me'),

  changePassword: (payload: { current_password: string; new_password: string }) =>
    requestJson<void>('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Organizations & Memberships
  listOrganizations: () => requestJson<OrganizationWithRoleResponse[]>('/organizations'),

  createOrganization: (payload: {
    name: string;
    slug?: string;
    organization_type: OrganizationType;
    description?: string;
    contact_email?: string;
    contact_phone?: string;
    region: string;
    district?: string;
  }) =>
    requestJson<OrganizationWithRoleResponse>('/organizations', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getOrganization: (orgId: string) =>
    requestJson<OrganizationResponse>(`/organizations/${orgId}`, {
      includeOrgHeader: true,
    }),

  updateOrganization: (
    orgId: string,
    payload: {
      name?: string;
      description?: string;
      contact_email?: string;
      contact_phone?: string;
      region?: string;
      district?: string;
    },
  ) =>
    requestJson<OrganizationResponse>(`/organizations/${orgId}`, {
      method: 'PATCH',
      includeOrgHeader: true,
      body: JSON.stringify(payload),
    }),

  listMembers: (orgId: string) =>
    requestJson<OrganizationMemberResponse[]>(`/organizations/${orgId}/members`, {
      includeOrgHeader: true,
    }),

  addMember: (
    orgId: string,
    payload: { email: string; role: OrganizationRole; status: 'active' | 'invited' },
  ) =>
    requestJson<OrganizationMemberResponse>(`/organizations/${orgId}/members`, {
      method: 'POST',
      includeOrgHeader: true,
      body: JSON.stringify(payload),
    }),

  acceptInvitation: (orgId: string) =>
    requestJson<OrganizationMemberResponse>(`/organizations/${orgId}/invitations/accept`, {
      method: 'POST',
    }),

  updateMemberRole: (orgId: string, membershipId: string, role: OrganizationRole) =>
    requestJson<OrganizationMemberResponse>(`/organizations/${orgId}/members/${membershipId}`, {
      method: 'PATCH',
      includeOrgHeader: true,
      body: JSON.stringify({ role }),
    }),

  deactivateMember: (orgId: string, membershipId: string) =>
    requestJson<OrganizationMemberResponse>(`/organizations/${orgId}/members/${membershipId}`, {
      method: 'DELETE',
      includeOrgHeader: true,
    }),

  listAuditLogs: (orgId: string) =>
    requestJson<AuditLogResponse[]>(`/organizations/${orgId}/audit-logs`, {
      includeOrgHeader: true,
    }),

  // Platform Admin
  adminListOrganizations: () =>
    requestJson<OrganizationResponse[]>('/admin/organizations'),

  adminListAuditLogs: () => requestJson<AuditLogResponse[]>('/admin/audit-logs'),
};
