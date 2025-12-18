"""Configuration models for MCP servers."""

from typing import Any, Optional, Dict
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
import json


class ServerConfig(BaseModel):
    """Configuration for a single MCP server."""
    
    command: str = Field(..., description="Command to run the server")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")
    disabled: bool = Field(default=False, description="Skip this server if True")
    
    @field_validator("command")
    @classmethod
    def validate_command(cls, v: str) -> str:
        """Ensure command is not empty."""
        if not v or not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip()


class McpConfiguration(BaseModel):
    """Root configuration for all MCP servers."""
    
    mcpServers: Dict[str, ServerConfig] = Field(
        ..., 
        description="Map of server name to configuration"
    )
    
    @field_validator("mcpServers")
    @classmethod
    def validate_servers(cls, v: Dict[str, ServerConfig]) -> Dict[str, ServerConfig]:
        """Ensure at least one server exists."""
        if not v:
            raise ValueError("At least one MCP server must be configured")
        return v
    
    def active_servers(self) -> Dict[str, ServerConfig]:
        """Get only enabled servers."""
        return {
            name: config 
            for name, config in self.mcpServers.items() 
            if not config.disabled
        }
    
    def get_server(self, name: str) -> Optional[ServerConfig]:
        """Get server config by name."""
        return self.mcpServers.get(name)
    
    @classmethod
    def load_from_file(cls, path: Path) -> "McpConfiguration":
        """Load configuration from JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path) as f:
            data = json.load(f)
        
        return cls.model_validate(data)
