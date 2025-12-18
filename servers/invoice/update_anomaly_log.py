from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class UpdateAnomalyLogParams(BaseModel):
    """Parameters for update_anomaly_log."""
    invoice_id: str = Field(description="Invoice ID")
    is_anomaly: bool = Field(description="Is this invoice an anomaly")
    notes: Optional[str] = None | Field(description="Notes about the anomaly")


async def update_anomaly_log(params: UpdateAnomalyLogParams) -> Dict[str, Any]:
    """
    Update anomaly status for an invoice
    
    Args:
        params: Tool parameters
        
    Returns:
        Tool execution result
    """
    from app.runtime.mcp_manager import call_tool
    
    result = await call_tool(
        "invoice__update_anomaly_log",
        params.model_dump(exclude_none=True)
    )
    
    return result
