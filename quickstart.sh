#!/bin/bash

# Quick Start Script for MCP Code Execution PoC

echo "================================================"
echo "MCP Code Execution Agent - Quick Start"
echo "================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the agent-mcp-codeexec-poc directory"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.10"

echo "✓ Checking Python version..."
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $REQUIRED_VERSION or higher required. Found: $PYTHON_VERSION"
    exit 1
fi
echo "  Found Python $PYTHON_VERSION"

# Check if uv is installed
echo ""
echo "✓ Checking for uv..."
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo ""
    echo "   Install uv with:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "   Or visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi
echo "  Found uv $(uv --version)"

# Sync dependencies
echo ""
echo "✓ Syncing dependencies with uv..."
uv sync

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "✓ Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your OPENAI_API_KEY"
    echo ""
    echo "   1. Open .env in your editor"
    echo "   2. Replace 'your-openai-api-key-here' with your actual key"
    echo "   3. Save the file"
    echo ""
    read -p "Press Enter after you've added your API key..."
fi

# Check if API key is set
if ! grep -q "sk-" .env 2>/dev/null; then
    echo ""
    echo "⚠️  Warning: OPENAI_API_KEY may not be set correctly in .env"
    echo "   Make sure you've added your API key that starts with 'sk-'"
    echo ""
fi

echo ""
echo "================================================"
echo "Setup Complete! Choose how to run:"
echo "================================================"
echo ""
echo "Option 1: Run Demo Script (No API server needed)"
echo "   uv run python demo.py"
echo ""
echo "Option 2: Start API Server"
echo "   uv run fastapi dev app/main.py"
echo "   Then visit: http://127.0.0.1:8000/docs"
echo ""
echo "Option 3: Run Tests"
echo "   uv run pytest"
echo ""
echo "================================================"
echo ""

# Ask what to run
read -p "What would you like to do? (1/2/3/q to quit): " choice

case $choice in
    1)
        echo ""
        echo "Running demo..."
        uv run python demo.py
        ;;
    2)
        echo ""
        echo "Starting API server..."
        echo "Visit http://127.0.0.1:8000/docs for interactive API documentation"
        uv run fastapi dev app/main.py
        ;;
    3)
        echo ""
        echo "Running tests..."
        uv run pytest -v
        ;;
    q|Q)
        echo "Goodbye!"
        ;;
    *)
        echo "Invalid choice. Run one of the commands above manually."
        ;;
esac
