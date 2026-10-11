import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_get_customer():
    headers = {"x-core-api-key": "MOCK_CORE_API_KEY"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/mock-core/v1/health")
        assert response.status_code == 200

        no_auth = await ac.get("/mock-core/v1/customers/123")
        assert no_auth.status_code == 422

        bad_auth = await ac.get("/mock-core/v1/customers/123", headers={"x-core-api-key": "INVALID"})
        assert bad_auth.status_code == 401

        import uuid
        fake_uuid = str(uuid.uuid4())
        auth_res = await ac.get(f"/mock-core/v1/customers/{fake_uuid}", headers=headers)
        # Should be 404 or 422 depending on UUID validation, but we used string so it might just return 404.
        assert auth_res.status_code == 404
