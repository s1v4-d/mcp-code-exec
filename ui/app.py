"""
MCP Code Execution POC - Streamlit Chat UI

Simplified single-page chat interface:
- Persistent chat history with st.session_state
- Calls FastAPI `/api/v1/agent` for each user message
- Shows health status and minimal metrics
"""

import streamlit as st
import httpx
import json
import os
from datetime import datetime
import traceback

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


# Page configuration
st.set_page_config(page_title="MCP Code Execution POC", page_icon="", layout="centered")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.75rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 1rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
    }
    .code-block {
        background-color: #f5f5f5;
        padding: 0.75rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        font-family: 'Courier New', monospace;
        white-space: pre-wrap;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize session state variables for chat."""
    if 'api_client' not in st.session_state:
        # Agent requests can take 60-120s for code generation + execution
        # Use longer timeout for agent requests
        st.session_state.api_client = httpx.Client(base_url=API_BASE_URL, timeout=120.0)
    if 'health_client' not in st.session_state:
        # Short timeout for health checks to keep UI responsive
        st.session_state.health_client = httpx.Client(base_url=API_BASE_URL, timeout=5.0)
    if 'api_healthy' not in st.session_state:
        st.session_state.api_healthy = False
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'last_metrics' not in st.session_state:
        st.session_state.last_metrics = None


# API Helper Functions
def check_api_health():
    """Check if the FastAPI backend is healthy."""
    try:
        # Use dedicated health client with short timeout
        response = st.session_state.health_client.get("/health")
        if response.status_code == 200:
            st.session_state.api_healthy = True
            return True, response.json()
        return False, None
    except Exception as e:
        st.session_state.api_healthy = False
        return False, str(e)


def execute_agent_request(request: str, parameters: dict = None):
    """Execute an agent request via the API.
    
    Uses longer timeout since agent workflows involve:
    - LLM calls for code generation
    - MCP tool discovery and connection
    - Code execution in sandbox
    """
    try:
        payload = {
            "request": request,
            "parameters": parameters or {}
        }
        # api_client has 120s timeout for long-running operations
        response = st.session_state.api_client.post("/api/v1/agent", json=payload)
        response.raise_for_status()
        return response.json()
    except httpx.ReadTimeout:
        return {
            "status": "error",
            "response": "Request timed out. The agent is taking longer than expected. Please try a simpler request or try again.",
            "metrics": {},
            "error": "ReadTimeout: Request exceeded 120 second timeout"
        }
    except httpx.ConnectError:
        return {
            "status": "error",
            "response": f"Cannot connect to API at {API_BASE_URL}. Is the server running?",
            "metrics": {},
            "error": "Connection refused"
        }
    except Exception as e:
        return {
            "status": "error",
            "response": f"API request failed: {str(e)}",
            "metrics": {},
            "error": str(e)
        }


def get_current_weather(location: str):
    """Get current weather via API."""
    try:
        payload = {"location": location}
        response = st.session_state.api_client.post("/api/v1/weather/current", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_weather_forecast(location: str, days: int = 5):
    """Get weather forecast via API."""
    try:
        payload = {"location": location, "days": days}
        response = st.session_state.api_client.post("/api/v1/weather/forecast", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def add_rag_document(content: str, metadata: dict = None):
    """Add document to RAG via API."""
    try:
        payload = {"content": content, "metadata": metadata or {}}
        response = st.session_state.api_client.post("/api/v1/rag/add", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def search_rag(query: str, top_k: int = 5):
    """Search RAG via API."""
    try:
        payload = {"query": query, "top_k": top_k}
        response = st.session_state.api_client.post("/api/v1/rag/search", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_rag_stats():
    """Get RAG statistics via API."""
    try:
        response = st.session_state.api_client.get("/api/v1/rag/stats")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def render_header():
    """Render header and API status."""
    st.markdown('<div class="main-header">MCP Code Execution Chat</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Single-page, persistent chat with agent backend</div>', unsafe_allow_html=True)
    healthy, health_data = check_api_health()
    if healthy:
        st.success("API Connected")
        if health_data:
            st.json(health_data)
    else:
        st.error("API Disconnected")
        st.info(f"Trying to connect to: {API_BASE_URL}")


# Page: Home
def page_home():
    """Render the home/dashboard page."""
    st.markdown('<div class="main-header">MCP Code Execution Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Demonstrating Lazy Loading & Progressive Disclosure via REST API</div>', unsafe_allow_html=True)
    
    # API Status Overview
    st.markdown("### API Connection Status")
    healthy, health_data = check_api_health()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="API Status",
            value="Healthy" if healthy else "Unavailable",
            delta="Connected" if healthy else "Check logs"
        )
    
    with col2:
        st.metric(
            label="Base URL",
            value=API_BASE_URL
        )
    
    with col3:
        st.metric(
            label="Total Executions",
            value=len(st.session_state.execution_history)
        )
    
    if healthy and health_data:
        st.success("FastAPI backend is running and accessible")
        with st.expander("Health Details"):
            st.json(health_data)
    else:
        st.error("FastAPI backend is not accessible")
        st.warning(f"Make sure the API server is running at {API_BASE_URL}")
        st.code("make start", language="bash")
    
    # Quick Start Guide
    st.markdown("---")
    st.markdown("### Quick Start Guide")
    
    st.markdown("""
    1. **Check API Status**: Ensure the API is healthy (see above)
    2. **Agent Playground**: Use natural language to execute complex workflows
    3. **Weather Tools**: Get current weather and forecasts
    4. **RAG Tools**: Add documents and search your knowledge base
    5. **View History**: Track all executions and their results
    """)
    
    # Architecture Overview
    st.markdown("---")
    st.markdown("### Architecture")
    
    st.markdown("""
    ```
    ┌─────────────────────────────────────────────┐
    │      Streamlit UI (Port 8501)               │
    │      • Agent Playground                     │
    │      • Tool Interfaces                      │
    │      • Execution History                    │
    └──────────────────┬──────────────────────────┘
                       │ HTTP/REST API
                       ▼
    ┌─────────────────────────────────────────────┐
    │      FastAPI Backend (Port 8000)            │
    │      • /api/v1/agent (Code execution)       │
    │      • /api/v1/weather/* (Weather tools)    │
    │      • /api/v1/rag/* (RAG tools)            │
    └──────────────────┬──────────────────────────┘
                       │
                       ▼
    ┌─────────────────────────────────────────────┐
    │      MCP Manager (Lazy Loading)             │
    │      • Connect servers on-demand            │
    │      • Cache tool definitions               │
    │      • Execute tool calls                   │
    └──────────────────┬──────────────────────────┘
                       │
                       ▼
    ┌─────────────────────────────────────────────┐
    │      MCP Tool Servers                       │
    │      • Weather (OpenWeatherMap)             │
    │      • RAG (FAISS + Embeddings)             │
    │      • PostgreSQL (postgres-mcp)            │
    │      • Invoice (File-based)                 │
    └─────────────────────────────────────────────┘
    ```
    """)


def render_chat():
    """Render a simple persistent chat UI."""
    render_header()
    st.markdown("---")
    st.markdown("### Chat")
    
    # Show existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message and press Enter"):
        # Display user message and add to history
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Execute via API with status container for long-running operations
        with st.status("Agent processing...", expanded=True) as status:
            try:
                status.write("Sending request to agent...")
                start_time = datetime.now()
                result = execute_agent_request(prompt, parameters={})
                end_time = datetime.now()
                elapsed_ms = (end_time - start_time).total_seconds() * 1000
                st.session_state.last_metrics = result.get("metrics")
                
                # Update status with completion info
                if result.get("status") == "error":
                    status.update(label="Agent error", state="error", expanded=False)
                else:
                    status.update(label=f"Complete ({elapsed_ms:.0f}ms)", state="complete", expanded=False)
                
                # Render assistant response
                content = result.get("response", "No response")
                with st.chat_message("assistant"):
                    st.markdown(content)
                    # Optional: show small metrics summary inline
                    metrics = result.get("metrics", {})
                    if metrics:
                        st.caption(
                            f"Tokens: {metrics.get('tokens_used', 0)} • "
                            f"Tools: {metrics.get('tool_calls_count', 0)} • "
                            f"Exec: {metrics.get('code_exec_time_ms', 0)} ms"
                        )
                st.session_state.messages.append({"role": "assistant", "content": content})
                
                # If output file provided, hint it below the chat
                if result.get("output_file"):
                    st.info(f"Output saved to: {result['output_file']}")
            except Exception as e:
                status.update(label="Error", state="error", expanded=False)
                with st.chat_message("assistant"):
                    st.error(f"Error calling agent: {str(e)}")
                st.code(traceback.format_exc())


def render_bottom_panel():
    """Render optional metrics panel below chat."""
    st.markdown("---")
    st.markdown("### Last Execution Metrics")
    metrics = st.session_state.last_metrics
    if metrics:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Tokens Used", metrics.get("tokens_used", 0))
        with col2:
            st.metric("Tool Calls", metrics.get("tool_calls_count", 0))
        with col3:
            st.metric("Code Exec (ms)", metrics.get("code_exec_time_ms", 0))
        with col4:
            st.metric("Total Time (ms)", metrics.get("total_time_ms", 0))
    else:
        st.info("No executions yet.")


    # Optional quick actions panel (minimal)
    with st.expander("Quick Actions"):
        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input("Weather location", value="San Francisco")
            if st.button("Get Weather"):
                res = get_current_weather(location)
                st.json(res)
        with col2:
            query = st.text_input("RAG search", placeholder="e.g., invoices policy")
            if st.button("Search RAG"):
                res = search_rag(query, top_k=5)
                st.json(res)


# Page: Execution History
def page_execution_history():
    """Render the execution history page."""
    st.markdown('<div class="main-header">Execution History</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">View all past executions and their results</div>', unsafe_allow_html=True)
    
    if not st.session_state.execution_history:
        st.info("No executions yet. Try the Agent Playground to get started!")
        return
    
    def main():
        """Main application entry point."""
        init_session_state()
        render_chat()
        render_bottom_panel()
                # Execute via API
