from __future__ import annotations

from enum import Enum


class PlatformRole(str, Enum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"


class OrganizationRole(str, Enum):
    ORGANIZATION_ADMIN = "ORGANIZATION_ADMIN"
    AGRICULTURAL_OFFICER = "AGRICULTURAL_OFFICER"
    DATA_MANAGER = "DATA_MANAGER"
    RESEARCHER = "RESEARCHER"
    COOPERATIVE_MANAGER = "COOPERATIVE_MANAGER"
    FARMER = "FARMER"
    READ_ONLY_ANALYST = "READ_ONLY_ANALYST"


class OrganizationType(str, Enum):
    COOPERATIVE = "cooperative"
    NGO = "ngo"
    GOVERNMENT_DEPARTMENT = "government_department"
    RESEARCH_INSTITUTE = "research_institute"
    PRIVATE_AGRIBUSINESS = "private_agribusiness"


class MembershipStatus(str, Enum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"
