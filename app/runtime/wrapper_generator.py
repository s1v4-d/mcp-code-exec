"""Automatic wrapper generator for MCP tools.

Auto-generates Python functions from MCP tool schemas.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict

from .mcp_manager import get_mcp_manager
from .config_models import McpConfiguration


logger = logging.getLogger("mcp_execution.generator")


def sanitize_identifier(name: str) -> str:
    """Convert tool name to valid Python identifier."""
    # Replace invalid chars with underscore
    sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
    
    # Ensure doesn't start with number
    if sanitized and sanitized[0].isdigit():
        sanitized = f"tool_{sanitized}"
    
    return sanitized or "unnamed_tool"


def generate_params_model(tool_name: str, tool: Any) -> str:
    """
    Generate Pydantic model for tool parameters.
    
    Args:
        tool_name: Name of the tool
        tool: Tool definition with inputSchema
        
    Returns:
        Python code for Pydantic model
    """
    safe_name = sanitize_identifier(tool_name)
    class_name = f"{''.join(word.capitalize() for word in safe_name.split('_'))}Params"
    
    # Get schema
    schema = getattr(tool, "inputSchema", {})
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    if not properties:
        # No parameters - use empty model
        return f"""
class {class_name}(BaseModel):
    \"\"\"Parameters for {tool_name}.\"\"\"
    pass
"""
    
    # Build field definitions
    fields = []
    for prop_name, prop_schema in properties.items():
        is_required = prop_name in required
        prop_type = prop_schema.get("type", "Any")
        description = prop_schema.get("description", "")
        
        # Map JSON schema types to Python types
        type_map = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "List[Any]",
            "object": "Dict[str, Any]",
        }
        
        python_type = type_map.get(prop_type, "Any")
        
        if is_required:
            field_def = f"    {prop_name}: {python_type}"
        else:
            field_def = f"    {prop_name}: Optional[{python_type}] = None"
        
        if description:
            field_def += f' = Field(description="{description}")'
        
        fields.append(field_def)
    
    fields_code = "\n".join(fields)
    
    return f"""
class {class_name}(BaseModel):
    \"\"\"Parameters for {tool_name}.\"\"\"
{fields_code}
"""


def generate_wrapper_function(server_name: str, tool_name: str, tool: Any) -> str:
    """
    Generate async wrapper function for a tool.
    
    Args:
        server_name: MCP server name
        tool_name: Tool name
        tool: Tool definition
        
    Returns:
        Python code for wrapper function
    """
    safe_name = sanitize_identifier(tool_name)
    class_name = f"{''.join(word.capitalize() for word in safe_name.split('_'))}Params"
    tool_id = f"{server_name}__{tool_name}"
    
    description = getattr(tool, "description", "MCP tool wrapper")
    description = description.replace('"""', '\\"\\"\\"')
    
    return f"""
async def {safe_name}(params: {class_name}) -> Dict[str, Any]:
    \"\"\"
    {description}
    
    Args:
        params: Tool parameters
        
    Returns:
        Tool execution result
    \"\"\"
    from app.runtime.mcp_manager import call_tool
    
    result = await call_tool(
        "{tool_id}",
        params.model_dump(exclude_none=True)
    )
    
    return result
"""


def generate_server_module(server_name: str, tools: list, output_dir: Path):
    """
    Generate complete module for a server's tools.
    
    Creates:
    - servers/{server_name}/__init__.py (barrel export)
    - servers/{server_name}/{tool_name}.py (individual tools)
    - servers/{server_name}/README.md (documentation)
    """
    server_dir = output_dir / server_name
    server_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating {len(tools)} tools for: {server_name}")
    
    # Common imports for all tool files
    imports = [
        "from typing import Any, Dict, List, Optional",
        "from pydantic import BaseModel, Field",
    ]
    
    tool_names = []
    
    for tool in tools:
        safe_name = sanitize_identifier(tool.name)
        tool_names.append(safe_name)
        
        # Generate tool file
        tool_file = server_dir / f"{safe_name}.py"
        
        params_model = generate_params_model(tool.name, tool)
        wrapper_func = generate_wrapper_function(server_name, tool.name, tool)
        
        tool_code = "\n".join(imports) + "\n" + params_model + "\n" + wrapper_func
        
        tool_file.write_text(tool_code)
        logger.debug(f"Generated: {tool_file}")
    
    # Generate __init__.py (barrel export)
    init_file = server_dir / "__init__.py"
    init_imports = [f"from .{name} import {name}" for name in tool_names]
    init_all = f"__all__ = {tool_names}"
    init_content = "\n".join(init_imports) + "\n\n" + init_all + "\n"
    init_file.write_text(init_content)
    
    # Generate README
    readme_file = server_dir / "README.md"
    readme_content = f"""# {server_name} MCP Tools

Auto-generated wrappers for {server_name} server.

## Available Tools

{chr(10).join([f"- `{t.name}`: {getattr(t, 'description', 'No description')}" for t in tools])}

## Usage

```python
from servers.{server_name} import {tool_names[0] if tool_names else 'tool_name'}

# Call the tool
result = await {tool_names[0] if tool_names else 'tool_name'}(params)
```

**Note**: Auto-generated. Do not edit manually.
"""
    readme_file.write_text(readme_content)
    
    logger.info(f"Module complete: servers/{server_name}/")


async def generate_all_wrappers(config_path: Path = None):
    """
    Main wrapper generation orchestrator.
    
    1. Load MCP config
    2. Connect to each server
    3. List tools
    4. Generate wrappers
    """
    logger.info("Starting wrapper generation")
    
    # Load config
    path = config_path or Path.cwd() / "mcp_config.json"
    
    if not path.exists():
        logger.error(f"Config not found: {path}")
        return
    
    config = McpConfiguration.load_from_file(path)
    
    # Get manager
    manager = get_mcp_manager()
    await manager.load_config(path)
    
    # Output directory
    output_dir = Path.cwd() / "servers"
    output_dir.mkdir(exist_ok=True)
    
    # Generate for each server
    active = config.active_servers()
    
    for server_name, server_config in active.items():
        try:
            logger.info(f"Processing server: {server_name}")
            
            # Connect and list tools
            await manager._connect_server(server_name, server_config)
            tools = await manager._fetch_tools(server_name)
            
            if not tools:
                logger.warning(f"No tools found for: {server_name}")
                continue
            
            # Generate wrappers
            generate_server_module(server_name, tools, output_dir)
            
        except Exception as e:
            logger.error(f"Failed for '{server_name}': {e}")
            continue
    
    # Cleanup
    await manager.shutdown()
    
    logger.info("Wrapper generation complete")


def main():
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    asyncio.run(generate_all_wrappers())


if __name__ == "__main__":
    main()
