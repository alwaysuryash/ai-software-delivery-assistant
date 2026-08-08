"""Role-based access control (FR-002, BR-02).

Two layers of authorization:
1. Project-level: a user must have a ``ProjectAccess`` grant for a project to do anything with it.
2. Capability-level: the user's role determines which capabilities they may exercise.

Connector-level read/write separation is enforced separately in the connector gateway
(write tools disabled by default — BRD §16).
"""

from __future__ import annotations

from enum import StrEnum

from app.domain.enums import Role


class Permission(StrEnum):
    PROJECT_READ = "project:read"
    EVIDENCE_READ = "evidence:read"
    REPORT_READ = "report:read"
    REPORT_APPROVED_READ = "report:approved:read"
    REPORT_EDIT = "report:edit"
    RUN_ASSISTANT = "assistant:run"
    ACTION_APPROVE = "action:approve"
    FEEDBACK_WRITE = "feedback:write"
    ADMIN = "admin"


# Capability matrix (BRD §7). Executives can only read *approved* summaries.
_ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.DELIVERY_MANAGER: frozenset(
        {
            Permission.PROJECT_READ,
            Permission.EVIDENCE_READ,
            Permission.REPORT_READ,
            Permission.REPORT_EDIT,
            Permission.RUN_ASSISTANT,
            Permission.ACTION_APPROVE,
            Permission.FEEDBACK_WRITE,
        }
    ),
    Role.TECHNICAL_LEAD: frozenset(
        {
            Permission.PROJECT_READ,
            Permission.EVIDENCE_READ,
            Permission.REPORT_READ,
            Permission.RUN_ASSISTANT,
            Permission.FEEDBACK_WRITE,
        }
    ),
    Role.QA_LEAD: frozenset(
        {
            Permission.PROJECT_READ,
            Permission.EVIDENCE_READ,
            Permission.REPORT_READ,
            Permission.RUN_ASSISTANT,
            Permission.FEEDBACK_WRITE,
        }
    ),
    Role.DEVOPS_LEAD: frozenset(
        {
            Permission.PROJECT_READ,
            Permission.EVIDENCE_READ,
            Permission.REPORT_READ,
            Permission.RUN_ASSISTANT,
            Permission.FEEDBACK_WRITE,
        }
    ),
    Role.EXECUTIVE: frozenset(
        {
            Permission.PROJECT_READ,
            Permission.REPORT_APPROVED_READ,
        }
    ),
    Role.ADMINISTRATOR: frozenset(
        {
            Permission.PROJECT_READ,
            Permission.EVIDENCE_READ,
            Permission.REPORT_READ,
            Permission.REPORT_APPROVED_READ,
            Permission.REPORT_EDIT,
            Permission.RUN_ASSISTANT,
            Permission.ACTION_APPROVE,
            Permission.FEEDBACK_WRITE,
            Permission.ADMIN,
        }
    ),
}


def permissions_for(role: Role) -> frozenset[Permission]:
    return _ROLE_PERMISSIONS.get(role, frozenset())


def role_has_permission(role: Role, permission: Permission) -> bool:
    return permission in permissions_for(role)
