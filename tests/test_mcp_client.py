"""Test MCP client."""

import pytest
from app.mcp_client.client import MCPClient


def test_list_tools():
    """Test listing available tools."""
    client = MCPClient()
    tools = client.list_tools()
    
    assert len(tools) > 0
    assert any(tool["name"] == "fetch_invoices" for tool in tools)
    assert any(tool["name"] == "update_anomaly_log" for tool in tools)


def test_get_tool_definitions_text():
    """Test getting tool definitions as text."""
    client = MCPClient()
    definitions = client.get_tool_definitions_text()
    
    assert "fetch_invoices" in definitions
    assert "update_anomaly_log" in definitions
    assert "Description:" in definitions


def test_call_fetch_invoices():
    """Test calling the fetch_invoices tool."""
    client = MCPClient()
    
    result = client.call_tool("fetch_invoices", {"month": "last_month", "limit": 10})
    
    assert isinstance(result, list)
    assert len(result) == 10
    assert "invoice_id" in result[0]
    assert "amount" in result[0]


def test_call_update_anomaly_log():
    """Test calling the update_anomaly_log tool."""
    client = MCPClient()
    
    anomalies = [
        {"invoice_id": "INV-001", "reason": "high_amount"},
        {"invoice_id": "INV-002", "reason": "duplicate"}
    ]
    
    result = client.call_tool("update_anomaly_log", {"anomalies": anomalies})
    
    assert "log_id" in result
    assert result["count"] == 2
    assert result["status"] == "logged"


def test_call_nonexistent_tool():
    """Test calling a tool that doesn't exist."""
    client = MCPClient()
    
    with pytest.raises(ValueError) as exc_info:
        client.call_tool("nonexistent_tool", {})
    
    assert "not found" in str(exc_info.value)


if __name__ == "__main__":
    test_list_tools()
    test_get_tool_definitions_text()
    test_call_fetch_invoices()
    test_call_update_anomaly_log()
    test_call_nonexistent_tool()
    print("All MCP client tests passed!")
