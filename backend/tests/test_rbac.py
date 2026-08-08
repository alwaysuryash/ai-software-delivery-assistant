"""Unit tests for the RBAC permission matrix (FR-002, BRD §7)."""

from __future__ import annotations

from app.domain.enums import Role
from app.domain.rbac import Permission, permissions_for, role_has_permission


def test_delivery_manager_can_approve_actions() -> None:
    assert role_has_permission(Role.DELIVERY_MANAGER, Permission.ACTION_APPROVE)
    assert role_has_permission(Role.DELIVERY_MANAGER, Permission.RUN_ASSISTANT)


def test_executive_reads_only_approved_reports() -> None:
    perms = permissions_for(Role.EXECUTIVE)
    assert Permission.REPORT_APPROVED_READ in perms
    # Executives cannot see raw evidence or run the assistant (BRD §7).
    assert Permission.EVIDENCE_READ not in perms
    assert Permission.RUN_ASSISTANT not in perms
    assert Permission.ACTION_APPROVE not in perms


def test_technical_lead_cannot_approve() -> None:
    assert not role_has_permission(Role.TECHNICAL_LEAD, Permission.ACTION_APPROVE)
    assert role_has_permission(Role.TECHNICAL_LEAD, Permission.EVIDENCE_READ)


def test_admin_has_admin_permission() -> None:
    assert role_has_permission(Role.ADMINISTRATOR, Permission.ADMIN)
