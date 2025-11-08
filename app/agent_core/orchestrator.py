"""Main agent orchestrator - coordinates code generation and execution."""

from typing import Dict, Any
import re

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.mcp_client.client import MCPClient
from app.agent_core.code_executor import CodeExecutor
from app.agent_core.monitoring import Metrics, monitoring
from app.prompts.agent_prompt import AGENT_SYSTEM_PROMPT, get_code_generation_prompt


class AgentOrchestrator:
    """
    Main orchestrator for the agent.
    
    This implements the code execution approach to MCP:
    1. Receives user request
    2. Loads relevant tool definitions on-demand
    3. Generates Python code to accomplish the task
    4. Executes code in sandbox
    5. Returns summary and metrics
    """
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.1  # Low temperature for more deterministic code generation
        )
        self.mcp_client = MCPClient()
        self.code_executor = CodeExecutor()
    
    async def execute(self, user_request: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the agent workflow.
        
        Args:
            user_request: User's request/query
            parameters: Additional parameters
            
        Returns:
            Dictionary with status, summary, output_file, and metrics
        """
        if parameters is None:
            parameters = {}
        
        # Initialize metrics
        metrics = Metrics()
        metrics.start()
        
        try:
            # Step 1: Get tool definitions (progressive disclosure)
            tool_definitions = self._get_relevant_tool_definitions(user_request)
            
            # Step 2: Generate Python code using LLM
            print(f"[Orchestrator] Generating code for: {user_request}")
            code, tokens_used = await self._generate_code(user_request, parameters, tool_definitions)
            
            print(f"[Orchestrator] Generated code ({tokens_used} tokens):\n{code[:200]}...")
            
            # Step 3: Validate code
            is_valid, validation_error = self.code_executor.validate_code(code)
            if not is_valid:
                raise ValueError(f"Code validation failed: {validation_error}")
            
            # Step 4: Execute code
            print("[Orchestrator] Executing generated code...")
            exec_result = self.code_executor.execute(code)
            
            # Step 5: Process results
            metrics.end()
            metrics.record(
                tokens_used=tokens_used,
                model_name=settings.openai_model,
                tool_calls_count=self._count_tool_calls(code),
                code_exec_time_ms=exec_result["execution_time_ms"],
            )
            
            if not exec_result["success"]:
                result = {
                    "status": "error",
                    "summary": f"Code execution failed: {exec_result['error']}",
                    "output_file": None,
                    "metrics": metrics.to_dict(),
                    "error": exec_result["error"],
                    "code_output": exec_result["output"]
                }
            else:
                # Extract summary from output
                summary = self._extract_summary(exec_result["output"])
                output_file = self._extract_output_file(exec_result["output"])
                
                result = {
                    "status": "success",
                    "summary": summary,
                    "output_file": output_file,
                    "metrics": metrics.to_dict(),
                    "code_output": exec_result["output"]
                }
            
            # Save metrics to log
            metrics.save_to_log({
                "request": user_request,
                "parameters": parameters,
                "status": result["status"],
                "summary": result["summary"],
                "output_file": result.get("output_file"),
                "generated_code": code,
            })
            
            # Add to monitoring
            monitoring.add_run(metrics.to_dict())
            
            return result
            
        except Exception as e:
            metrics.end()
            metrics.record(
                tokens_used=0,
                model_name=settings.openai_model,
                tool_calls_count=0,
                code_exec_time_ms=0,
            )
            
            result = {
                "status": "error",
                "summary": f"Orchestration failed: {str(e)}",
                "output_file": None,
                "metrics": metrics.to_dict(),
                "error": str(e)
            }
            
            # Save error to log
            metrics.save_to_log({
                "request": user_request,
                "parameters": parameters,
                "status": "error",
                "error": str(e)
            })
            
            return result
    
    def _get_relevant_tool_definitions(self, user_request: str) -> str:
        """
        Get relevant tool definitions based on the request.
        
        This implements progressive disclosure - we only load tools that might be relevant.
        For the PoC, we load all available tools, but in production this could be smarter.
        
        Args:
            user_request: User's request
            
        Returns:
            Formatted tool definitions string
        """
        # For PoC: return all tools
        # In production: could use semantic search, keywords, or LLM to filter
        return self.mcp_client.get_tool_definitions_text()
    
    async def _generate_code(self, user_request: str, parameters: Dict[str, Any], 
                            tool_definitions: str) -> tuple[str, int]:
        """
        Generate Python code using the LLM.
        
        Args:
            user_request: User's request
            parameters: Additional parameters
            tool_definitions: Available tool definitions
            
        Returns:
            Tuple of (generated_code, tokens_used)
        """
        # Prepare messages
        messages = [
            SystemMessage(content=AGENT_SYSTEM_PROMPT),
            HumanMessage(content=get_code_generation_prompt(
                user_request, parameters, tool_definitions
            ))
        ]
        
        # Call LLM
        response = await self.llm.ainvoke(messages)
        
        # Extract code from response
        code = self._extract_code(response.content)
        
        # Estimate tokens (rough estimate based on response)
        tokens_used = len(response.content) // 4 + len(user_request) // 4 + 200
        
        return code, tokens_used
    
    def _extract_code(self, llm_response: str) -> str:
        """
        Extract Python code from LLM response.
        
        Handles cases where LLM wraps code in markdown blocks.
        
        Args:
            llm_response: Raw LLM response
            
        Returns:
            Extracted Python code
        """
        # Remove markdown code blocks if present
        code = llm_response
        
        # Pattern 1: ```python ... ```
        python_block_pattern = r'```python\s*(.*?)\s*```'
        match = re.search(python_block_pattern, code, re.DOTALL)
        if match:
            code = match.group(1)
        else:
            # Pattern 2: ``` ... ```
            code_block_pattern = r'```\s*(.*?)\s*```'
            match = re.search(code_block_pattern, code, re.DOTALL)
            if match:
                code = match.group(1)
        
        return code.strip()
    
    def _count_tool_calls(self, code: str) -> int:
        """
        Count the number of MCP tool calls in the code.
        
        Args:
            code: Generated Python code
            
        Returns:
            Number of tool calls
        """
        # Count occurrences of mcp_client.call_tool
        return code.count('mcp_client.call_tool(')
    
    def _extract_summary(self, output: str) -> str:
        """
        Extract summary from code output.
        
        Args:
            output: Captured stdout from code execution
            
        Returns:
            Summary text
        """
        if not output:
            return "Code executed successfully (no output)"
        
        # Take the last non-empty line as summary, or the whole output if short
        lines = [line for line in output.strip().split('\n') if line.strip()]
        
        if not lines:
            return "Code executed successfully"
        
        # If output is short, return it all
        if len(output) < 200:
            return output.strip()
        
        # Otherwise, return last line as summary
        return lines[-1]
    
    def _extract_output_file(self, output: str) -> str | None:
        """
        Extract output file path from code output.
        
        Args:
            output: Captured stdout
            
        Returns:
            File path if found, None otherwise
        """
        # Look for common patterns like "saved to workspace/..." or "file at workspace/..."
        patterns = [
            r'(?:saved to|written to|file at|output:)\s+(workspace/[^\s]+)',
            r"'(workspace/[^']+)'",
            r'"(workspace/[^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
