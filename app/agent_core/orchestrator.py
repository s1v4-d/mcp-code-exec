"""Main agent orchestrator - coordinates code generation and execution."""

from typing import Dict, Any
import re

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.mcp_client.client import MCPClient
from app.agent_core.code_executor import CodeExecutor
from app.agent_core.harness import ExecutionHarness  # New: Runtime harness
from app.agent_core.monitoring import Metrics, monitoring
from app.prompts.agent_prompt import (
    AGENT_SYSTEM_PROMPT,
    TOOL_DECISION_PROMPT,
    CODE_GENERATION_SYSTEM_PROMPT,
    get_code_generation_prompt,
    get_response_generation_prompt
)


class AgentOrchestrator:
    """
    Conversational agent with code execution capability for MCP tools.
    
    This implements a hybrid approach:
    1. User makes a request
    2. Agent decides if tools are needed
    3. If yes: generates code, executes it, and responds based on results
    4. If no: responds directly to the user
    5. Always provides natural conversational responses
    """
    
    def __init__(self, use_harness: bool = True):
        """Initialize the orchestrator.
        
        Args:
            use_harness: If True, use ExecutionHarness for improved code execution
        """
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.7  # Natural conversational temperature
        )
        self.code_llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.1  # Low temperature for code generation
        )
        self.mcp_client = MCPClient()
        
        # Choose executor (legacy or new harness)
        if use_harness:
            self.code_executor = ExecutionHarness(
                timeout_seconds=settings.code_exec_timeout_seconds,
                workspace_dir="workspace",
            )
        else:
            self.code_executor = CodeExecutor()
    
    async def execute(self, user_request: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the agent workflow.
        
        Args:
            user_request: User's request/query
            parameters: Additional parameters
            
        Returns:
            Dictionary with status, response, output_file, and metrics
        """
        if parameters is None:
            parameters = {}
        
        # Initialize metrics
        metrics = Metrics()
        metrics.start()
        
        try:
            # Step 1: Decide if tools are needed
            needs_tools = await self._needs_tools(user_request)
            
            if needs_tools:
                print(f"[Agent] Request requires tools: {user_request}")
                
                # Step 2: Minimal tool context (following Anthropic paper approach)
                # Instead of loading tool definitions, we tell the agent HOW to discover them
                tool_context = await self._get_minimal_tool_context()
                
                # Step 3: Generate Python code
                code, code_tokens = await self._generate_code(user_request, tool_context)
                print(f"[Agent] Generated code ({code_tokens} tokens)")
                
                # Step 4: Validate code (DISABLED - harness handles async wrapping)
                # The harness auto-wraps async code in asyncio.run(), so we can't validate
                # top-level await here. The reference repo doesn't validate before execution.
                # is_valid, validation_error = self.code_executor.validate_code(code)
                # if not is_valid:
                #     raise ValueError(f"Code validation failed: {validation_error}")
                
                # Step 5: Execute code
                print("[Agent] Executing code...")
                # Support both old executor and new harness
                if hasattr(self.code_executor, 'execute_async'):
                    exec_result = await self.code_executor.execute_async(code)
                else:
                    exec_result = self.code_executor.execute(code)
                
                if not exec_result["success"]:
                    raise ValueError(f"Code execution failed: {exec_result['error']}")
                
                # Step 6: Generate natural response based on results
                print("[Agent] Generating response based on results...")
                response, response_tokens = await self._generate_response(
                    user_request, 
                    exec_result["output"]
                )
                
                total_tokens = code_tokens + response_tokens
                tool_calls = self._count_tool_calls(code)
                output_file = self._extract_output_file(exec_result["output"])
                
            else:
                print(f"[Agent] Direct response (no tools needed): {user_request}")
                
                # Direct response without tools
                response_msg = await self.llm.ainvoke([
                    SystemMessage(content=AGENT_SYSTEM_PROMPT),
                    HumanMessage(content=user_request)
                ])
                
                response = response_msg.content
                total_tokens = response_msg.response_metadata.get("token_usage", {}).get("total_tokens", 0)
                tool_calls = 0
                output_file = None
                exec_result = {"execution_time_ms": 0}
            
            # Record metrics
            metrics.end()
            metrics.record(
                tokens_used=total_tokens,
                model_name=settings.openai_model,
                tool_calls_count=tool_calls,
                code_exec_time_ms=exec_result.get("execution_time_ms", 0),
            )
            
            result = {
                "status": "success",
                "response": response,
                "output_file": output_file,
                "metrics": metrics.to_dict(),
                "used_tools": needs_tools
            }
            
            # Save metrics to log
            metrics.save_to_log({
                "request": user_request,
                "status": "success",
                "response": response,
                "used_tools": needs_tools,
                "output_file": output_file,
            })
            
            # Add to monitoring
            monitoring.add_run(metrics.to_dict())
            
            return result
            
        except Exception as e:
            metrics.end()
            result = {
                "status": "error",
                "response": f"I encountered an error: {str(e)}",
                "output_file": None,
                "metrics": metrics.to_dict(),
                "error": str(e),
                "used_tools": False
            }
            
            # Save error to log
            metrics.save_to_log({
                "request": user_request,
                "status": "error",
                "error": str(e)
            })
            
            return result
    
    async def _needs_tools(self, user_request: str) -> bool:
        """Determine if the request requires tool usage."""
        tools_summary = "\n".join([f"- {tool}" for tool in self.mcp_client.list_tools()[:10]])
        
        decision_prompt = TOOL_DECISION_PROMPT.format(
            request=user_request,
            tools=tools_summary
        )
        
        response = await self.llm.ainvoke([
            SystemMessage(content="You are a helpful assistant that decides if tools are needed."),
            HumanMessage(content=decision_prompt)
        ])
        
        decision = response.content.strip().upper()
        return "YES" in decision
    
    async def _generate_response(self, user_request: str, code_output: str) -> tuple[str, int]:
        """Generate natural response based on code execution results."""
        response_prompt = get_response_generation_prompt(user_request, code_output)
        
        response = await self.llm.ainvoke([
            SystemMessage(content=AGENT_SYSTEM_PROMPT),
            HumanMessage(content=response_prompt)
        ])
        
        tokens = response.response_metadata.get("token_usage", {}).get("total_tokens", 0)
        return response.content, tokens
    
    async def _get_minimal_tool_context(self) -> str:
        """
        Get minimal tool context following the Anthropic paper's approach.
        
        Instead of loading all tool definitions, we provide instructions for
        the agent to explore the filesystem and discover tools themselves.
        This implements "progressive disclosure" as described in the paper.
        """
        from servers.discovery import tool_discovery
        
        # Get list of available servers (minimal info)
        servers = tool_discovery.list_servers()
        
        context = []
        context.append("# MCP Tool Discovery")
        context.append("")
        context.append("## Available Tool Servers")
        for server in servers:
            overview = await tool_discovery.get_server_overview(server)
            context.append(f"- **{server}**: {overview.get('description', 'MCP Server')} ({overview.get('tool_count', 0)} tools)")
        context.append("")
        context.append("## How to Discover and Use Tools")
        context.append("")
        context.append("You have access to `tool_discovery` for exploring available tools:")
        context.append("")
        context.append("```python")
        context.append("# List all servers")
        context.append("servers = tool_discovery.list_servers()")
        context.append("# Returns: ['weather', 'rag', 'invoice']")
        context.append("")
        context.append("# List tools in a server")
        context.append("tools = tool_discovery.list_tools('weather')")
        context.append("# Returns: ['get_current_weather', 'get_forecast', 'get_geo_data']")
        context.append("")
        context.append("# Search for relevant tools (with detail levels)")
        context.append("results = await tool_discovery.search_tools(")
        context.append("    query='weather forecast',")
        context.append("    top_k=3,")
        context.append("    detail_level='summary'  # 'name' | 'summary' | 'full'")
        context.append(")")
        context.append("")
        context.append("# Read a tool file to see its interface")
        context.append("code = await tool_discovery.read_file('weather/get_current_weather.py')")
        context.append("")
        context.append("# Or get just the definition")
        context.append("definition = await tool_discovery.get_tool_definition('weather', 'get_current_weather')")
        context.append("```")
        context.append("")
        context.append("## Using Tools")
        context.append("")
        context.append("Once you know which tools you need, import and use them directly:")
        context.append("")
        context.append("```python")
        context.append("from servers.weather import get_current_weather")
        context.append("")
        context.append("weather = await get_current_weather(city_name='Tokyo', country_name='Japan')")
        context.append("print(f\"Temperature: {weather['main']['temp']}°F\")")
        context.append("```")
        context.append("")
        context.append("## Important")
        context.append("- Use `detail_level='name'` first to see what's available (minimal tokens)")
        context.append("- Use `detail_level='summary'` to see descriptions")
        context.append("- Only use `detail_level='full'` when you need complete schemas")
        context.append("- Process data in code, only print summaries (keep token usage low)")
        
        return "\n".join(context)
    
    async def _get_relevant_tool_definitions(self, user_request: str) -> str:
        """
        DEPRECATED: Use _get_minimal_tool_context() instead.
        
        This method is kept for compatibility but now redirects to the
        paper-compliant approach where agents discover tools themselves.
        """
        return await self._get_minimal_tool_context()
    
    async def _generate_code(self, user_request: str, tool_definitions: str) -> tuple[str, int]:
        """Generate Python code using the LLM."""
        prompt = get_code_generation_prompt(user_request, tool_definitions)
        
        response = await self.code_llm.ainvoke([
            SystemMessage(content=CODE_GENERATION_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        code = self._extract_code(response.content)
        tokens = response.response_metadata.get("token_usage", {}).get("total_tokens", 0)
        
        return code, tokens
    
    def _extract_code(self, llm_response: str) -> str:
        """Extract Python code from LLM response."""
        import re
        
        # Pattern 1: ```python ... ```
        python_block_pattern = r'```python\s*(.*?)\s*```'
        match = re.search(python_block_pattern, llm_response, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Pattern 2: ``` ... ```
        code_block_pattern = r'```\s*(.*?)\s*```'
        match = re.search(code_block_pattern, llm_response, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # No code blocks, return as-is
        return llm_response.strip()
    
    def _count_tool_calls(self, code: str) -> int:
        """Count MCP tool calls in code."""
        return code.count('mcp_client.call_tool(')
    
    def _extract_output_file(self, output: str) -> str | None:
        """Extract output file path from code output."""
        import re
        
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
