export type PlatformRole = 'PLATFORM_ADMIN';

export type OrganizationRole =
  | 'ORGANIZATION_ADMIN'
  | 'AGRICULTURAL_OFFICER'
  | 'DATA_MANAGER'
  | 'RESEARCHER'
  | 'COOPERATIVE_MANAGER'
  | 'FARMER'
  | 'READ_ONLY_ANALYST';

export type UserRole = PlatformRole | OrganizationRole;

export type MembershipStatus = 'active' | 'invited' | 'suspended' | 'deactivated';

export type OrganizationType =
  | 'cooperative'
  | 'ngo'
  | 'government_department'
  | 'research_institute'
  | 'private_agribusiness';

export type GambiaAdminRegion =
  | 'Banjul'
  | 'Kanifing'
  | 'West Coast Region'
  | 'Lower River Region'
  | 'North Bank Region'
  | 'Central River Region'
  | 'Upper River Region';

export interface ApiErrorDetail {
  field?: string;
  message: string;
  code?: string;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    request_id: string;
    details?: ApiErrorDetail[];
  };
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  meta: PaginationMeta;
}

export interface HealthResponse {
  status: 'ok' | 'degraded';
  service: string;
  version: string;
  environment: string;
  timestamp_utc: string;
}

export interface ReadinessResponse {
  status: 'ready' | 'not_ready';
  checks: {
    database: {
      configured: boolean;
      reachable: boolean;
      postgis_enabled: boolean | null;
      detail: string;
    };
  };
  timestamp_utc: string;
}

export interface PlatformMetaResponse {
  platform: string;
  api_version: string;
  initial_geography: string;
  supported_regions: GambiaAdminRegion[];
  roles: string[];
  phases: {
    id: string;
    name: string;
    status: 'completed' | 'in_progress' | 'planned';
  }[];
}

export interface MembershipSummary {
  id: string;
  organization_id: string;
  organization_name: string;
  organization_slug: string;
  organization_type: OrganizationType;
  role: OrganizationRole;
  status: MembershipStatus;
  permissions: string[];
  joined_at: string | null;
}

export interface UserProfileResponse {
  id: string;
  email: string;
  full_name: string;
  phone_number: string | null;
  is_active: boolean;
  is_verified: boolean;
  platform_role: PlatformRole | null;
  last_login_at: string | null;
  created_at: string;
  memberships: MembershipSummary[];
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: 'Bearer';
  expires_in: number;
  csrf_token?: string | null;
  user: UserProfileResponse;
}

export interface LogoutResponse {
  revoked: boolean;
  message: string;
}

export interface OrganizationResponse {
  id: string;
  name: string;
  slug: string;
  organization_type: OrganizationType;
  description: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  region: string;
  district: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrganizationWithRoleResponse extends OrganizationResponse {
  membership_role: OrganizationRole;
  membership_status: MembershipStatus;
  permissions: string[];
}

export interface OrganizationMemberResponse {
  id: string;
  organization_id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: OrganizationRole;
  status: MembershipStatus;
  joined_at: string | null;
  created_at: string;
}

export interface AuditLogResponse {
  id: string;
  organization_id: string | null;
  actor_user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  request_id: string | null;
  timestamp: string;
  metadata_json: Record<string, unknown>;
}
