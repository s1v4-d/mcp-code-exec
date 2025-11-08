"""Test the complete agent flow."""

import pytest
from httpx import AsyncClient
import asyncio

from app.main import app


@pytest.mark.asyncio
async def test_agent_invoice_analysis():
    """Test the agent with an invoice analysis request."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent",
            json={
                "request": "Fetch invoice data for last month, find duplicates and anomalies, and save results",
                "parameters": {
                    "month": "last_month",
                    "limit": 50
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "status" in data
        assert "summary" in data
        assert "metrics" in data
        
        # Check metrics
        assert "tokens_used" in data["metrics"]
        assert "code_exec_time_ms" in data["metrics"]
        
        print(f"\nAgent Response:")
        print(f"Status: {data['status']}")
        print(f"Summary: {data['summary']}")
        print(f"Output File: {data.get('output_file')}")
        print(f"Metrics: {data['metrics']}")


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test the health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_agent_invoice_analysis())
    asyncio.run(test_health_endpoint())
