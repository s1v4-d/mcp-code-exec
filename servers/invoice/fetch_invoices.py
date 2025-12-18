from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class FetchInvoicesParams(BaseModel):
    """Parameters for fetch_invoices."""
    start_date: Optional[str] = None | Field(description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = None | Field(description="End date (YYYY-MM-DD)")
    category: Optional[str] = None | Field(description="Invoice category")
    min_amount: Optional[float] = None | Field(description="Minimum amount")
    max_amount: Optional[float] = None | Field(description="Maximum amount")

async def fetch_invoices(params: FetchInvoicesParams) -> Dict[str, Any]:
    """
    Fetch invoices with optional filters
    
    Args:
        params: Tool parameters
        
    Returns:
        Tool execution result
    """
    from app.runtime.mcp_manager import call_tool
    
    result = await call_tool(
        "invoice__fetch_invoices",
        params.model_dump(exclude_none=True)
    )
    
    return result
