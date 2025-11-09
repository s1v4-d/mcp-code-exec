"""Agent API endpoint."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import traceback

from app.agent_core.orchestrator import AgentOrchestrator

router = APIRouter()

# Create orchestrator instance
orchestrator = AgentOrchestrator()


class AgentRequest(BaseModel):
    """Agent request model."""
    request: str = Field(..., description="User request/query for the agent")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Additional parameters")


class AgentResponse(BaseModel):
    """Agent response model."""
    status: str = Field(..., description="Status: success or error")
    response: str = Field(..., description="Response or summary")
    output_file: Optional[str] = Field(None, description="Path to output file if any")
    metrics: Dict[str, Any] = Field(..., description="Execution metrics")
    error: Optional[str] = Field(None, description="Error message if failed")


@router.post("/agent", response_model=AgentResponse)
async def execute_agent(request: AgentRequest) -> AgentResponse:
    """
    Execute the agent with code generation and MCP tool integration.
    
    This endpoint demonstrates the code execution approach to MCP:
    - Loads tool definitions on-demand (progressive disclosure)
    - Generates Python code to call tools and process data
    - Executes code in sandbox
    - Returns summary and metrics
    """
    try:
        result = await orchestrator.execute(
            user_request=request.request,
            parameters=request.parameters
        )
        
        return AgentResponse(
            status=result["status"],
            response=result["response"],
            output_file=result.get("output_file"),
            metrics=result["metrics"],
            error=result.get("error")
        )
        
    except Exception as e:
        # Log the full error
        error_trace = traceback.format_exc()
        print(f"Error in agent execution:\n{error_trace}")
        
        return AgentResponse(
            status="error",
            response="Agent execution failed",
            metrics={
                "tokens_used": 0,
                "tool_calls_count": 0,
                "code_exec_time_ms": 0,
                "total_time_ms": 0
            },
            error=str(e)
        )
