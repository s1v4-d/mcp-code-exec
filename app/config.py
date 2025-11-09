from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    openai_api_key: str
    openai_model: str = "gpt-4o"
    
    open_weather_api_key: str = Field(default="")
    
    workspace_path: Path = Field(default=Path("workspace"))
    logs_path: Path = Field(default=Path("logs"))
    
    code_exec_timeout_seconds: int = Field(default=30, gt=0, le=300)
    max_retries: int = Field(default=3, ge=1, le=10)
    
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, gt=0, lt=65536)

    @field_validator("workspace_path", "logs_path", mode="after")
    @classmethod
    def ensure_path_exists(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v


settings = Settings()


ALLOWED_IMPORTS = frozenset({
    "json", "datetime", "typing", "pandas", "numpy",
    "re", "math", "statistics",
    "requests", "pytz", "timezonefinder",
    "os", "sys", "pathlib", "collections",
})

MCP_TOOLS_DIR = Path(__file__).parent / "mcp_client" / "tools"
