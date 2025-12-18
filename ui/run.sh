#!/bin/bash

# Run Streamlit UI for MCP Code Execution POC

echo "Starting MCP Code Execution POC - Streamlit UI"
echo "==============================================="
echo ""
echo "Configuration:"
echo "  - Port: 8501"
echo "  - Server Address: 0.0.0.0"
echo "  - Headless Mode: Enabled"
echo ""
echo "In GitHub Codespaces, the UI will be accessible via:"
echo "  - Forwarded Port: https://<codespace-name>-8501.preview.app.github.dev"
echo ""
echo "Starting Streamlit..."
echo ""

# Navigate to project root
cd "$(dirname "$0")/.."

# Run Streamlit
streamlit run ui/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    --server.enableCORS=true \
    --server.enableXsrfProtection=true
