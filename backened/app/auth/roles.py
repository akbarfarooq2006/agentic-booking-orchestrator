"""
Role-Based Access Control (RBAC) — Role definitions and hierarchy.

Defines the three roles supported by the system and provides helpers
for checking role permissions.

Roles:
    - user: Default role for customers booking services.
    - provider: Service providers (plumbers, electricians, etc.).
    - admin: System administrators with full access.

Usage:
    from app.auth.roles import UserRole, is_role_allowed

    if is_role_allowed(current_role, UserRole.PROVIDER):
        # allow provider-level action
"""

from enum import Enum
from typing import List


class UserRole(str, Enum):
    """Enumeration of supported user roles.

    Inherits from str so it serializes cleanly to/from JSON and can be
    compared with plain strings:  role == "admin"
    """
    USER = "user"
    PROVIDER = "provider"
    ADMIN = "admin"


# Role hierarchy — higher index = more privilege.
# Used by is_role_at_least() to check minimum privilege level.
_ROLE_HIERARCHY: List[UserRole] = [
    UserRole.USER,
    UserRole.PROVIDER,
    UserRole.ADMIN,
]


def get_role_level(role: str) -> int:
    """Return the numeric privilege level of a role.

    Args:
        role: Role string (e.g. "user", "provider", "admin").

    Returns:
        Integer level (0 = user, 1 = provider, 2 = admin).
        Returns -1 if the role is unrecognized.
    """
    try:
        return _ROLE_HIERARCHY.index(UserRole(role))
    except (ValueError, KeyError):
        return -1


def is_role_at_least(current_role: str, minimum_role: UserRole) -> bool:
    """Check if current_role meets or exceeds the minimum required role.

    Examples:
        is_role_at_least("admin", UserRole.PROVIDER)  → True
        is_role_at_least("user", UserRole.ADMIN)       → False
    """
    return get_role_level(current_role) >= get_role_level(minimum_role.value)


def is_role_allowed(current_role: str, allowed_roles: List[UserRole]) -> bool:
    """Check if the current role is in the list of allowed roles.

    Examples:
        is_role_allowed("provider", [UserRole.PROVIDER, UserRole.ADMIN])  → True
        is_role_allowed("user", [UserRole.ADMIN])                          → False
    """
    return current_role in [r.value for r in allowed_roles]
