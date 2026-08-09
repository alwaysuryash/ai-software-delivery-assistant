"""Integration tests for RBAC gaps, permission checks, and status 409 errors."""

from __future__ import annotations

import pytest
from app.domain.enums import Role, ReportStatus


@pytest.mark.anyio
async def test_executive_cannot_see_drafts(client, session_factory):
    # Log in as Executive
    login_resp = await client.post("/auth/dev-login", json={"email": "exec@acme.com"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    project_id = client.seeded["project_id"]

    # Log in as PM to generate a draft report
    pm_login = await client.post("/auth/dev-login", json={"email": "pm@acme.com"})
    pm_token = pm_login.json()["access_token"]
    pm_headers = {"Authorization": f"Bearer {pm_token}"}

    run_resp = await client.post(
        f"/projects/{project_id}/run",
        json={"prompt": "Review"},
        headers=pm_headers
    )
    report_id = run_resp.json()["report"]["id"]

    # Retrieve as Executive - list should be empty because report is draft
    exec_list_resp = await client.get(f"/projects/{project_id}/reports", headers=headers)
    assert exec_list_resp.status_code == 200
    reports = exec_list_resp.json()
    assert len(reports) == 0

    # Approve as PM/Admin to make it APPROVED
    await client.post(f"/projects/{project_id}/reports/{report_id}/approve", headers=pm_headers)

    # Retrieve as Executive - now it should be visible!
    exec_list_resp_2 = await client.get(f"/projects/{project_id}/reports", headers=headers)
    assert exec_list_resp_2.status_code == 200
    reports_2 = exec_list_resp_2.json()
    assert len(reports_2) == 1
    assert reports_2[0]["id"] == report_id


@pytest.mark.anyio
async def test_non_approver_cannot_approve_action(client):
    # Tech lead does NOT have Permission.ACTION_APPROVE
    login_resp = await client.post("/auth/dev-login", json={"email": "techlead@acme.com"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    project_id = client.seeded["project_id"]

    # Try to approve action
    app_resp = await client.post(f"/projects/{project_id}/actions/dummy-id/approve", headers=headers)
    print("DEBUG:", app_resp.status_code, app_resp.json())
    assert app_resp.status_code == 403
