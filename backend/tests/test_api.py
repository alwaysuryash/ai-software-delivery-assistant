"""End-to-end API tests: auth, project listing, and access isolation (US-05, BR-02)."""

from __future__ import annotations

from httpx import AsyncClient


async def test_healthz_is_public(client: AsyncClient) -> None:
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    # Correlation ID is echoed back on every response (NFR-05).
    assert "X-Correlation-ID" in resp.headers


async def _login(client: AsyncClient, email: str) -> str:
    resp = await client.post("/auth/dev-login", json={"email": email})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def test_dev_login_and_me(client: AsyncClient) -> None:
    token = await _login(client, "pm@acme.com")
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "pm@acme.com"
    assert resp.json()["role"] == "delivery_manager"


async def test_project_listing_scoped_to_access(client: AsyncClient) -> None:
    token = await _login(client, "pm@acme.com")
    resp = await client.get("/projects", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()]
    assert names == ["Project Alpha"]


async def test_unauthenticated_request_rejected(client: AsyncClient) -> None:
    resp = await client.get("/projects")
    assert resp.status_code == 401  # missing bearer credentials


async def test_outsider_cannot_see_project(client: AsyncClient) -> None:
    # 'nobody@acme.com' has no ProjectAccess grant — must not see or fetch the project (BR-02).
    token = await _login(client, "nobody@acme.com")
    headers = {"Authorization": f"Bearer {token}"}

    listing = await client.get("/projects", headers=headers)
    assert listing.status_code == 200
    assert listing.json() == []

    project_id = client.seeded["project_id"]  # type: ignore[attr-defined]
    direct = await client.get(f"/projects/{project_id}", headers=headers)
    # Uniform 404 — existence not disclosed to unauthorized users.
    assert direct.status_code == 404
