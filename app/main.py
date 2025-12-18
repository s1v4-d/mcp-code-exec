import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import agent, weather, rag
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="MCP Code Execution Agent",
    description="AI agent with code execution and MCP tool integration",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent.router, prefix="/api/v1", tags=["agent"])
app.include_router(weather.router, prefix="/api/v1/weather", tags=["weather"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])


@app.on_event("startup")
async def startup_event():
    logger.info("="*80)
    logger.info("MCP CODE EXECUTION AGENT STARTING")
    logger.info("="*80)
    logger.info(f"OpenAI Model: {settings.openai_model}")
    logger.info(f"Workspace: {settings.workspace_path}")
    logger.info(f"Logs: {settings.logs_path}")
    logger.info(f"Code Execution Timeout: {settings.code_exec_timeout_seconds}s")
    logger.info("="*80)


@app.get("/")
async def root():
    return {
        "message": "MCP Code Execution Agent API",
        "docs": "/docs",
        "version": "0.2.0",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "workspace": str(settings.workspace_path),
        "logs": str(settings.logs_path),
    }
