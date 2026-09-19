import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_create_task_returns_201_with_full_task():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/setup_database", params={"confirm": "true"})

        response = await client.post(
            "/api/tasks",
            json={"title": "Тестовая задача", "description": "описание"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Тестовая задача"
        assert body["status"] == "new"
        assert "id" in body
        assert "created_at" in body


@pytest.mark.asyncio
async def test_update_task_status_field_works():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/setup_database", params={"confirm": "true"})
        created = await client.post(
            "/api/tasks", json={"title": "X", "description": "Y"}
        )
        task_id = created.json()["id"]

        updated = await client.patch(
            f"/api/tasks/{task_id}", json={"status": "in_progress"}
        )
        assert updated.status_code == 200
        assert updated.json()["status"] == "in_progress"