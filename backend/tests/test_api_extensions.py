"""Integration tests for all newly added project API endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.anyio
async def test_run_assistant_endpoint(client):
    # Log in as PM
    login_resp = await client.post("/auth/dev-login", json={"email": "pm@acme.com"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    project_id = client.seeded["project_id"]

    # Run assistant
    resp = await client.post(
        f"/projects/{project_id}/run",
        json={"prompt": "Review Project Alpha"},
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    assert "report" in data
    assert data["report"]["overall_health"] == "red"
    assert "findings" in data["report"]
    assert "evaluations" in data["report"]


@pytest.mark.anyio
async def test_report_list_and_approve_endpoints(client):
    login_resp = await client.post("/auth/dev-login", json={"email": "pm@acme.com"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    project_id = client.seeded["project_id"]

    # Generate a report first
    run_resp = await client.post(
        f"/projects/{project_id}/run",
        json={"prompt": "Review"},
        headers=headers
    )
    report_id = run_resp.json()["report"]["id"]

    # List reports
    list_resp = await client.get(f"/projects/{project_id}/reports", headers=headers)
    assert list_resp.status_code == 200
    reports = list_resp.json()
    assert len(reports) > 0
    assert reports[0]["id"] == report_id

    # Approve report
    app_resp = await client.post(f"/projects/{project_id}/reports/{report_id}/approve", headers=headers)
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "approved"


@pytest.mark.anyio
async def test_actions_workflow_endpoints(client):
    login_resp = await client.post("/auth/dev-login", json={"email": "pm@acme.com"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    project_id = client.seeded["project_id"]

    # Generate report and action
    await client.post(f"/projects/{project_id}/run", json={"prompt": "Review"}, headers=headers)

    # List proposed actions
    act_resp = await client.get(f"/projects/{project_id}/actions", headers=headers)
    assert act_resp.status_code == 200
    actions = act_resp.json()
    assert len(actions) > 0
    action_id = actions[0]["id"]
    payload = actions[0]["proposed_write_payload"]

    # Approve action
    app_resp = await client.post(f"/projects/{project_id}/actions/{action_id}/approve", headers=headers)
    assert app_resp.status_code == 200
    assert app_resp.json()["approval_status"] == "approved"

    # Execute action with correct payload
    exec_resp = await client.post(
        f"/projects/{project_id}/actions/{action_id}/execute",
        json={"payload": payload},
        headers=headers
    )
    assert exec_resp.status_code == 200
    assert exec_resp.json()["approval_status"] == "executed"
