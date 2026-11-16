from __future__ import annotations

from enum import Enum

from app.models.enums import OrganizationRole


class Permission(str, Enum):
    # Organization & Membership Management
    ORG_READ = "org:read"
    ORG_UPDATE = "org:update"
    MEMBERSHIP_READ = "membership:read"
    MEMBERSHIP_MANAGE = "membership:manage"
    AUDIT_READ = "audit:read"

    # Agricultural Domain Permissions (enforced across Phases 2-6)
    FARMER_READ = "farmer:read"
    FARMER_WRITE = "farmer:write"
    FARM_READ = "farm:read"
    FARM_WRITE = "farm:write"
    PLOT_READ = "plot:read"
    PLOT_WRITE = "plot:write"
    CROP_READ = "crop:read"
    CROP_WRITE = "crop:write"
    PRODUCTION_READ = "production:read"
    PRODUCTION_WRITE = "production:write"
    IMPORT_MANAGE = "import:manage"
    ANALYTICS_READ = "analytics:read"
    REPORT_EXPORT = "report:export"


ROLE_PERMISSIONS: dict[OrganizationRole, frozenset[Permission]] = {
    OrganizationRole.ORGANIZATION_ADMIN: frozenset(
        {
            Permission.ORG_READ,
            Permission.ORG_UPDATE,
            Permission.MEMBERSHIP_READ,
            Permission.MEMBERSHIP_MANAGE,
            Permission.AUDIT_READ,
            Permission.FARMER_READ,
            Permission.FARMER_WRITE,
            Permission.FARM_READ,
            Permission.FARM_WRITE,
            Permission.PLOT_READ,
            Permission.PLOT_WRITE,
            Permission.CROP_READ,
            Permission.CROP_WRITE,
            Permission.PRODUCTION_READ,
            Permission.PRODUCTION_WRITE,
            Permission.IMPORT_MANAGE,
            Permission.ANALYTICS_READ,
            Permission.REPORT_EXPORT,
        }
    ),
    OrganizationRole.AGRICULTURAL_OFFICER: frozenset(
        {
            Permission.ORG_READ,
            Permission.MEMBERSHIP_READ,
            Permission.FARMER_READ,
            Permission.FARMER_WRITE,
            Permission.FARM_READ,
            Permission.FARM_WRITE,
            Permission.PLOT_READ,
            Permission.PLOT_WRITE,
            Permission.CROP_READ,
            Permission.PRODUCTION_READ,
            Permission.PRODUCTION_WRITE,
            Permission.ANALYTICS_READ,
            Permission.REPORT_EXPORT,
        }
    ),
    OrganizationRole.DATA_MANAGER: frozenset(
        {
            Permission.ORG_READ,
            Permission.MEMBERSHIP_READ,
            Permission.FARMER_READ,
            Permission.FARMER_WRITE,
            Permission.FARM_READ,
            Permission.FARM_WRITE,
            Permission.PLOT_READ,
            Permission.PLOT_WRITE,
            Permission.CROP_READ,
            Permission.CROP_WRITE,
            Permission.PRODUCTION_READ,
            Permission.PRODUCTION_WRITE,
            Permission.IMPORT_MANAGE,
            Permission.ANALYTICS_READ,
            Permission.REPORT_EXPORT,
        }
    ),
    OrganizationRole.RESEARCHER: frozenset(
        {
            Permission.ORG_READ,
            Permission.FARM_READ,
            Permission.PLOT_READ,
            Permission.CROP_READ,
            Permission.PRODUCTION_READ,
            Permission.ANALYTICS_READ,
            Permission.REPORT_EXPORT,
        }
    ),
    OrganizationRole.COOPERATIVE_MANAGER: frozenset(
        {
            Permission.ORG_READ,
            Permission.MEMBERSHIP_READ,
            Permission.FARMER_READ,
            Permission.FARMER_WRITE,
            Permission.FARM_READ,
            Permission.FARM_WRITE,
            Permission.PLOT_READ,
            Permission.CROP_READ,
            Permission.PRODUCTION_READ,
            Permission.PRODUCTION_WRITE,
            Permission.ANALYTICS_READ,
            Permission.REPORT_EXPORT,
        }
    ),
    OrganizationRole.FARMER: frozenset(
        {
            Permission.ORG_READ,
            Permission.FARM_READ,
            Permission.PLOT_READ,
            Permission.CROP_READ,
            Permission.PRODUCTION_READ,
            Permission.PRODUCTION_WRITE,
        }
    ),
    OrganizationRole.READ_ONLY_ANALYST: frozenset(
        {
            Permission.ORG_READ,
            Permission.FARMER_READ,
            Permission.FARM_READ,
            Permission.PLOT_READ,
            Permission.CROP_READ,
            Permission.PRODUCTION_READ,
            Permission.ANALYTICS_READ,
            Permission.REPORT_EXPORT,
        }
    ),
}


def get_permissions_for_role(role: OrganizationRole) -> frozenset[Permission]:
    return ROLE_PERMISSIONS.get(role, frozenset())


def has_permission(role: OrganizationRole, permission: Permission) -> bool:
    return permission in get_permissions_for_role(role)
