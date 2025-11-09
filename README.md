# Agent MCP Code Execution PoC

A Proof of Concept demonstrating code execution with Model Context Protocol (MCP) for efficient AI agents, enhanced with **Weather API** and **FAISS-based RAG** capabilities.

## 🆕 New Features

### Weather API Integration
- Real-time weather data using OpenWeatherMap
- 5-day weather forecasts with timezone awareness
- Flexible location search (city name or zip code)
- **Integrated as MCP tool** - Agent can generate code to use weather data
- Based on [langchain-weather-tool-calling](https://github.com/hari04hp/langchain-weather-tool-calling)

### FAISS-Based RAG System
- Document indexing with vector embeddings
- Fast semantic similarity search
- Multiple embedding options (HuggingFace or OpenAI)
- File upload support for text documents
- **Integrated as MCP tool** - Agent can store and retrieve knowledge
- Persistent storage with source tracking

### MCP Tool Integration
Both Weather and RAG are exposed as **MCP tools** that the agent can use by generating Python code:
- Agent receives user request
- LLM generates code that calls MCP tools
- Code executes in sandbox with tool access
- Results processed and summarized

📖 **See [docs/MCP_INTEGRATION.md](docs/MCP_INTEGRATION.md) for MCP usage guide**  
📖 **See [docs/WEATHER_AND_RAG.md](docs/WEATHER_AND_RAG.md) for detailed API documentation**

## Overview

This PoC implements the concepts from Anthropic's paper on [Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp), demonstrating how agents can use code execution to interact with MCP servers more efficiently.

### Key Benefits

- **Progressive Disclosure**: Load tool definitions on-demand rather than upfront
- **Context Efficient**: Filter and transform data in code before passing to LLM
- **Powerful Control Flow**: Use loops, conditionals in code instead of chaining tool calls
- **Privacy-Preserving**: Intermediate results stay in execution environment
- **State Persistence**: Save results and skills for reuse

## Architecture

```
User Request → FastAPI → LangChain Orchestrator → Code Generator (LLM)
                                ↓
                        Generated Python Code
                                ↓
                        Code Executor (Sandbox)
                                ↓
                        MCP Client → MCP Tool Servers
                                ↓
                        Results → Workspace Files
                                ↓
                        Summary → User
```

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (optional but recommended - for automatic PostgreSQL setup)
- OpenAI API key
- OpenWeatherMap API key (optional, for weather features)

### One-Command Setup

```bash
# Clone the repository
git clone <repository-url>
cd mcp-code-exec

# Complete setup (installs uv, dependencies, creates .env, sets up databases)
make setup

# Edit .env file with your API keys
nano .env

# Start the server
make start
```

The setup command automatically:
- Installs `uv` if not already installed
- Installs all Python dependencies via `uv sync`
- Creates `.env` file from template
- Creates required directories (workspace, logs, data)
- Starts PostgreSQL in Docker (if Docker is available)
- Sets up PostgreSQL database with sample data
- Sets up RAG index with sample documents

No manual PostgreSQL installation required - Docker handles it automatically!

### Manual Setup (Alternative)

If you prefer manual setup or don't have Docker:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Create directories
mkdir -p workspace logs data/rag data/invoices

# Setup RAG and PostgreSQL
uv run python scripts/setup_rag.py

# PostgreSQL (only if you have PostgreSQL installed locally)
uv run python scripts/setup_pg.py
```

### PostgreSQL Notes

The `make setup` command automatically starts PostgreSQL in Docker if:
- Docker is installed and running
- No PostgreSQL container named `postgres-mcp` exists

If you already have PostgreSQL running locally or prefer a different setup:
- Set the connection details in `.env` file
- Run `uv run python scripts/setup_pg.py` manually

**Manual PostgreSQL Setup:**

**Manual PostgreSQL Setup:**

**Option 1: Docker (Recommended)**
```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres --name postgres-mcp postgres:14
uv run python scripts/setup_pg.py
```

**Option 2: Local Installation**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql

# macOS
brew install postgresql@14
```

Then run:
```bash
uv run python scripts/setup_pg.py
```

### Configuration

Create a `.env` file (or copy from `.env.example`):

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-key-here
OPENAI_MODEL=gpt-4o

# Weather API (get key from https://openweathermap.org/api)
OPEN_WEATHER_API_KEY=your-openweather-key-here

# RAG Configuration
USE_OPENAI_EMBEDDINGS=false  # Set to true for OpenAI embeddings
RAG_INDEX_PATH=/workspaces/mcp-code-exec/agent-mcp-codeexec-poc/rag_index

# PostgreSQL Configuration (for PostgreSQL MCP Server)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mcp_demo
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Paths
WORKSPACE_PATH=/workspaces/mcp-code-exec/agent-mcp-codeexec-poc/workspace
LOGS_PATH=/workspaces/mcp-code-exec/agent-mcp-codeexec-poc/logs
```

### Running the Server

```bash
# Start the FastAPI server
make start
```

The server will start at `http://localhost:8000` with:
- Interactive API docs: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

### Available Make Commands

```bash
make help    # Show available commands
make setup   # Complete project setup (uv, deps, env, databases)
make start   # Start the FastAPI server
```

## Usage

### Quick Demo - MCP Agent with Weather & RAG

Test the agent using Weather and RAG tools through MCP:

```bash
# Start the server first
uv run fastapi dev app/main.py

# In another terminal, run the agent test
python examples/test_agent_mcp_tools.py
```

This interactive test demonstrates the agent generating code to:
- Get current weather for any city
- Get weather forecasts
- Add documents to RAG knowledge base
- Search RAG with semantic queries
- Combine weather + RAG in single workflow
- Upload files and query them
- Get RAG statistics

### MCP Agent Examples

**Weather Query:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/agent \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Get current weather for Tokyo, Japan and tell me the temperature"
  }'
```

**RAG Knowledge Base:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/agent \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Add this to knowledge base: Python is a programming language. Then search for Python."
  }'
```

**Combined Weather + RAG:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/agent \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Get weather for London, store it in RAG, then search for London weather"
  }'
```

### Direct API Examples (Non-Agent)

**Get Current Weather:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/weather/current \
  -H "Content-Type: application/json" \
  -d '{"city_name": "London", "country_name": "UK"}'
```

**Get Weather Forecast:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/weather/forecast \
  -H "Content-Type: application/json" \
  -d '{"city_name": "Tokyo", "country_name": "Japan", "days": 2, "hour": 14}'
```

**Add Documents to RAG:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/rag/documents/add \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Python is a programming language."],
    "source": "my-docs"
  }'
```

**Search Documents:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?", "k": 3}'
```

### Agent Example Request

```bash
curl -X POST http://127.0.0.1:8000/api/v1/agent \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Fetch invoice data, find duplicates and anomalies, then summarize the findings",
    "parameters": {
      "month": "last_month"
    }
  }'
```

### Example Response

```json
{
  "status": "success",
  "summary": "Found 12 duplicate invoices and 5 anomalies. Details saved to workspace.",
  "output_file": "workspace/invoice_analysis_2025-11-08_14-30-22.csv",
  "metrics": {
    "tokens_used": 1250,
    "model_name": "gpt-4o",
    "tool_calls_count": 1,
    "code_exec_time_ms": 450,
    "total_time_ms": 2100
  }
}
```

## Project Structure

```
agent-mcp-codeexec-poc/
├── README.md                 # This file
├── pyproject.toml            # Project metadata and dependencies
├── uv.lock                   # Locked dependencies
├── .env                      # Environment variables
├── .env.example              # Example environment file
├── logs/                     # Execution logs and metrics
├── workspace/                # Output files from agent
├── rag_index/                # FAISS vector index storage
├── examples/
│   ├── weather_and_rag_demo.py  # Direct API demo
│   └── test_agent_mcp_tools.py  # MCP agent tests
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration
│   ├── api/
│   │   └── v1/
│   │       ├── agent.py     # Agent endpoint
│   │       ├── weather.py   # Weather API endpoints
│   │       └── rag.py       # RAG API endpoints
│   ├── agent_core/
│   │   ├── orchestrator.py  # Main agent orchestration
│   │   ├── code_executor.py # Sandboxed code execution
│   │   └── monitoring.py    # Metrics collection
│   ├── mcp_client/
│   │   ├── client.py        # MCP client wrapper
│   │   └── tools/
│   │       ├── invoice_tool.py  # Example invoice tool
│   │       ├── weather_tool.py  # Weather API tool (MCP)
│   │       └── rag_tool.py      # RAG tool (MCP)
│   ├── rag/
│   │   └── document_store.py    # FAISS-based RAG system
│   └── prompts/
│       └── agent_prompt.py  # LLM prompt templates
├── tests/
│   ├── test_agent_flow.py
│   ├── test_code_executor.py
│   └── test_mcp_client.py
└── docs/
    ├── architecture.md
    ├── monitoring.md
    ├── WEATHER_AND_RAG.md   # Weather & RAG API documentation
    └── MCP_INTEGRATION.md   # MCP integration guide
```

## How It Works

### 1. Request Processing

The FastAPI endpoint receives a user request and passes it to the LangChain orchestrator.

### 2. Code Generation

Instead of loading all tool definitions upfront, the agent:
- Analyzes the request
- Loads only relevant tool definitions on-demand
- Uses the LLM to generate Python code that:
  - Calls MCP tools via client wrapper
  - Processes data locally (filtering, aggregation, etc.)
  - Writes results to workspace
  - Returns a summary

### 3. Code Execution

The generated code is executed in a sandboxed environment with:
- Restricted imports (only allowed libraries)
- Timeout protection
- Resource limits
- Captured stdout/stderr

### 4. Monitoring

Each execution is logged with:
- Timestamp
- Tokens used
- Tools called
- Execution time
- Success/failure status
- Error messages if any

## Example Tools

### Weather Tool (MCP)

Exposed as MCP tool for agent code generation:
- `get_current_weather(city_name, country_name)` - Get current weather
- `get_forecast(city_name, country_name, days, hour)` - Get weather forecast
- `get_geo_data(city_name, zip_code, country_name)` - Get geographic coordinates

**Agent Usage:**
```python
# Generated code example
from mcp_client_wrapper import mcp_client

weather = mcp_client.call_tool('get_current_weather', {
    'city_name': 'Tokyo',
    'country_name': 'Japan'
})
print(f"Temperature: {weather['main']['temp']}°F")
```

### RAG System (MCP)

Exposed as MCP tool for knowledge management:
- `add_documents(texts, source)` - Index documents
- `search_documents(query, k)` - Semantic similarity search
- `get_context(query, k)` - Get formatted context for LLMs
- `add_file(file_path, source)` - Add file to index
- `get_rag_stats()` - Get index statistics

**Agent Usage:**
```python
# Generated code example
from mcp_client_wrapper import mcp_client

# Add to knowledge base
mcp_client.call_tool('add_documents', {
    'texts': ['Python is a programming language'],
    'source': 'facts'
})

# Search
results = mcp_client.call_tool('search_documents', {
    'query': 'What is Python?',
    'k': 2
})
```

### Invoice Tool (MCP)

The PoC includes a mock invoice tool that simulates:
- `fetch_invoices(month)` - Fetches invoice data
- `update_anomaly_log(anomalies)` - Logs detected anomalies

## Testing

```bash
# Run all tests
uv run pytest

# Run specific test
uv run pytest tests/test_agent_flow.py

# With coverage
uv run pytest --cov=app tests/
```

## Monitoring

Metrics are saved to `logs/run_<timestamp>.json`:

```json
{
  "timestamp": "2025-11-08T14:30:22Z",
  "request": "Fetch invoice data...",
  "model_name": "gpt-4o",
  "tokens_used": 1250,
  "tool_calls_count": 1,
  "code_exec_time_ms": 450,
  "total_time_ms": 2100,
  "status": "success",
  "output_file": "workspace/invoice_analysis.csv"
}
```

## Future Enhancements

- [ ] Add Streamlit UI for interactive agent interaction
- [ ] Implement more MCP tool servers
- [ ] Add Docker containerization
- [ ] Implement skill persistence (save reusable functions)
- [ ] Add more sophisticated sandboxing
- [ ] Multi-tenant support
- [ ] Authentication and authorization
- [ ] Integrate Weather API with agent orchestrator
- [ ] Add RAG-powered context to agent responses
- [ ] Implement hybrid search (keyword + semantic)

## Credits

- Weather API based on: [langchain-weather-tool-calling](https://github.com/hari04hp/langchain-weather-tool-calling) by Haripriya Rajendran
- Weather data by: [OpenWeatherMap](https://openweathermap.org/)
- Vector search by: [FAISS](https://github.com/facebookresearch/faiss)
- Embeddings by: [sentence-transformers](https://www.sbert.net/)

## References

- [Anthropic: Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [LangChain Documentation](https://python.langchain.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [OpenWeatherMap API](https://openweathermap.org/api)

## License

MIT
