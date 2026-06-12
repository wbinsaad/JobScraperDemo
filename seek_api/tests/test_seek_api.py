import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport

# Add project root to import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.anyio
async def test_get_random_jobs_default_count(client):
    response = await client.get("/jobs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    for job_item in data:
        assert "id" in job_item
        assert "title" in job_item
        assert "company" in job_item


@pytest.mark.anyio
@pytest.mark.parametrize("count", [1, 3])
async def test_get_random_jobs_custom_count(client, count):
    response = await client.get("/jobs", params={"count": count})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == count


@pytest.mark.anyio
async def test_get_random_jobs_unique_uuids(client):
    response = await client.get("/jobs", params={"count": 3})
    assert response.status_code == 200
    data = response.json()
    uuids = [job["id"] for job in data]
    assert len(uuids) == len(set(uuids))


@pytest.mark.anyio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}