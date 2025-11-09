"""Server Module Generator

Auto-generates Pydantic-based Python wrappers for MCP server tools.
Creates modular server packages in servers/ directory.
"""

import os
from pathlib import Path
from typing import Dict, List, Any
from jinja2 import Environment, FileSystemLoader

from .schema_converter import SchemaConverter


class ServerModuleGenerator:
    """Generates Python module wrappers for MCP server tools."""
    
    def __init__(self, template_dir: str | None = None):
        """Initialize generator with Jinja2 templates.
        
        Args:
            template_dir: Path to template directory (defaults to ./templates)
        """
        if template_dir is None:
            # Default to templates/ directory adjacent to this file
            template_dir = Path(__file__).parent / "templates"
        
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.converter = SchemaConverter()
        
    def generate_server_module(
        self,
        server_name: str,
        tools: List[Dict[str, Any]],
        output_dir: str,
    ) -> Path:
        """Generate a complete server module with all tools.
        
        Args:
            server_name: Name of the MCP server (e.g., "filesystem", "postgres")
            tools: List of tool definitions from MCP server
            output_dir: Base directory for server modules (e.g., "servers/")
            
        Returns:
            Path to generated module directory
            
        Example:
            >>> generator = ServerModuleGenerator()
            >>> tools = [
            ...     {
            ...         "name": "read_file",
            ...         "description": "Read file contents",
            ...         "inputSchema": {
            ...             "type": "object",
            ...             "properties": {
            ...                 "path": {"type": "string", "description": "File path"}
            ...             },
            ...             "required": ["path"]
            ...         }
            ...     }
            ... ]
            >>> module_path = generator.generate_server_module(
            ...     "filesystem", tools, "servers/"
            ... )
        """
        # Create output directory for this server
        server_dir = Path(output_dir) / server_name
        server_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate individual tool modules
        tool_names = []
        for tool in tools:
            tool_name = tool["name"]
            tool_names.append(tool_name)
            
            # Generate tool module
            self._generate_tool_module(
                server_name=server_name,
                tool=tool,
                output_dir=server_dir,
            )
        
        # Generate __init__.py for the server package
        self._generate_server_init(
            server_name=server_name,
            tool_names=tool_names,
            output_dir=server_dir,
        )
        
        return server_dir
    
    def _generate_tool_module(
        self,
        server_name: str,
        tool: Dict[str, Any],
        output_dir: Path,
    ) -> Path:
        """Generate a single tool module file.
        
        Args:
            server_name: Name of the MCP server
            tool: Tool definition from MCP server
            output_dir: Directory to write module file
            
        Returns:
            Path to generated tool module file
        """
        tool_name = tool["name"]
        description = tool.get("description", f"MCP tool: {tool_name}")
        input_schema = tool.get("inputSchema", {})
        
        # Convert input schema to Pydantic model
        params_model_name = f"{self._capitalize_snake_case(tool_name)}Params"
        params_model_code = self.converter.schema_to_pydantic(
            schema=input_schema,
            model_name=params_model_name,
        )
        
        # Render template
        template = self.env.get_template("tool_module.py.jinja2")
        rendered = template.render(
            server_name=server_name,
            tool_name=tool_name,
            tool_identifier=f"{server_name}/{tool_name}",
            description=description,
            params_model_name=params_model_name,
            params_model=params_model_code,
        )
        
        # Write to file
        output_file = output_dir / f"{tool_name}.py"
        output_file.write_text(rendered)
        
        return output_file
    
    def _generate_server_init(
        self,
        server_name: str,
        tool_names: List[str],
        output_dir: Path,
    ) -> Path:
        """Generate __init__.py for server package.
        
        Args:
            server_name: Name of the MCP server
            tool_names: List of tool names in this server
            output_dir: Directory to write __init__.py
            
        Returns:
            Path to generated __init__.py
        """
        template = self.env.get_template("server_init.py.jinja2")
        rendered = template.render(
            server_name=server_name,
            tool_names=tool_names,
        )
        
        output_file = output_dir / "__init__.py"
        output_file.write_text(rendered)
        
        return output_file
    
    @staticmethod
    def _capitalize_snake_case(name: str) -> str:
        """Convert snake_case to PascalCase.
        
        Args:
            name: Snake case string (e.g., "read_file")
            
        Returns:
            PascalCase string (e.g., "ReadFile")
        """
        return "".join(word.capitalize() for word in name.split("_"))
