#!/usr/bin/env python3
"""
Test script for MCP agent with Weather and RAG tools.

This demonstrates the agent's ability to generate code that uses
Weather API and RAG tools through the MCP client.
"""

import asyncio
import requests
import json
from pathlib import Path


BASE_URL = "http://localhost:8000/api/v1"


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def check_server():
    """Check if the server is running."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print("❌ Server returned error")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server!")
        print("Please start the server with: python -m app.main")
        return False


def test_weather_tool():
    """Test agent using weather tool."""
    print_section("TEST 1: Agent Using Weather Tool")
    
    request = {
        "request": "Get the current weather for Tokyo, Japan and tell me the temperature and conditions",
        "parameters": {}
    }
    
    print(f"Request: {request['request']}\n")
    
    response = requests.post(f"{BASE_URL}/agent", json=request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Summary: {result['summary']}\n")
        print(f"Metrics:")
        print(f"  - Model: {result['metrics']['model_name']}")
        print(f"  - Tokens: {result['metrics']['tokens_used']}")
        print(f"  - Tool calls: {result['metrics']['tool_calls_count']}")
        print(f"  - Execution time: {result['metrics']['code_exec_time_ms']}ms")
        
        if result.get('code_output'):
            print(f"\nAgent Output:\n{result['code_output']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def test_weather_forecast():
    """Test agent using weather forecast."""
    print_section("TEST 2: Agent Using Weather Forecast")
    
    request = {
        "request": "Get the weather forecast for London, UK for 2 days from now at 3 PM. Tell me what the temperature and conditions will be.",
        "parameters": {}
    }
    
    print(f"Request: {request['request']}\n")
    
    response = requests.post(f"{BASE_URL}/agent", json=request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Summary: {result['summary']}\n")
        
        if result.get('code_output'):
            print(f"Agent Output:\n{result['code_output']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def test_rag_tool():
    """Test agent using RAG tool."""
    print_section("TEST 3: Agent Using RAG Tool")
    
    request = {
        "request": """Add these facts to the knowledge base: 
        1. Python is a high-level programming language created by Guido van Rossum.
        2. Machine learning is a subset of artificial intelligence.
        3. FAISS is a library for efficient similarity search.
        Then search for 'What is Python?' and show me the results.""",
        "parameters": {}
    }
    
    print(f"Request: {request['request']}\n")
    
    response = requests.post(f"{BASE_URL}/agent", json=request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Summary: {result['summary']}\n")
        
        if result.get('code_output'):
            print(f"Agent Output:\n{result['code_output']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def test_combined_weather_rag():
    """Test agent using both weather and RAG tools together."""
    print_section("TEST 4: Agent Using Weather + RAG Together")
    
    request = {
        "request": """Do the following:
        1. Get current weather for Paris, France
        2. Store the weather information in the RAG knowledge base with source 'weather-paris'
        3. Then search the knowledge base for 'Paris weather' and show what was stored
        This demonstrates combining weather data collection with knowledge storage.""",
        "parameters": {}
    }
    
    print(f"Request: {request['request']}\n")
    
    response = requests.post(f"{BASE_URL}/agent", json=request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Summary: {result['summary']}\n")
        
        if result.get('code_output'):
            print(f"Agent Output:\n{result['code_output']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def test_rag_file_and_search():
    """Test agent adding file to RAG and searching."""
    print_section("TEST 5: Agent Using RAG File Upload and Search")
    
    # Create a sample file in workspace
    workspace_path = Path("workspace")
    workspace_path.mkdir(exist_ok=True)
    
    sample_file = workspace_path / "ai_concepts.txt"
    sample_content = """
    Artificial Intelligence (AI) is the simulation of human intelligence by machines.
    
    Neural networks are computing systems inspired by biological neural networks.
    They consist of interconnected nodes organized in layers.
    
    Deep learning is a subset of machine learning that uses neural networks
    with multiple layers to progressively extract higher-level features.
    
    Natural Language Processing (NLP) enables computers to understand,
    interpret, and generate human language.
    """
    
    sample_file.write_text(sample_content)
    print(f"Created sample file: {sample_file}\n")
    
    request = {
        "request": f"""Add the file '{sample_file}' to the RAG index with source 'ai-concepts'. 
        Then search for 'What is deep learning?' and show the most relevant result.""",
        "parameters": {}
    }
    
    print(f"Request: {request['request']}\n")
    
    response = requests.post(f"{BASE_URL}/agent", json=request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Summary: {result['summary']}\n")
        
        if result.get('code_output'):
            print(f"Agent Output:\n{result['code_output']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def test_rag_stats():
    """Test agent getting RAG statistics."""
    print_section("TEST 6: Agent Getting RAG Statistics")
    
    request = {
        "request": "Show me the current statistics of the RAG index including total documents and all sources.",
        "parameters": {}
    }
    
    print(f"Request: {request['request']}\n")
    
    response = requests.post(f"{BASE_URL}/agent", json=request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Summary: {result['summary']}\n")
        
        if result.get('code_output'):
            print(f"Agent Output:\n{result['code_output']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def test_multi_city_weather():
    """Test agent getting weather for multiple cities."""
    print_section("TEST 7: Agent Getting Multi-City Weather Report")
    
    request = {
        "request": """Get current weather for these cities:
        - New York, US
        - London, UK
        - Tokyo, Japan
        
        Create a summary comparing their temperatures and save it to workspace/weather_comparison.txt""",
        "parameters": {}
    }
    
    print(f"Request: {request['request']}\n")
    
    response = requests.post(f"{BASE_URL}/agent", json=request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Summary: {result['summary']}\n")
        print(f"Output file: {result.get('output_file', 'None')}")
        
        if result.get('code_output'):
            print(f"\nAgent Output:\n{result['code_output']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("  MCP Agent Tests - Weather & RAG Tools")
    print("="*70)
    print("\nThis script tests the agent's ability to generate code that uses")
    print("Weather and RAG tools through the MCP client interface.\n")
    
    if not check_server():
        return
    
    print("\n⚠️  Note: These tests require:")
    print("  1. OPEN_WEATHER_API_KEY set in .env")
    print("  2. Server running with: python -m app.main")
    print("  3. First RAG query may be slow (downloads embedding model)")
    
    input("\nPress Enter to continue with tests...")
    
    # Run tests
    tests = [
        ("Weather - Current", test_weather_tool),
        ("Weather - Forecast", test_weather_forecast),
        ("RAG - Add & Search", test_rag_tool),
        ("Combined - Weather + RAG", test_combined_weather_rag),
        ("RAG - File Upload & Search", test_rag_file_and_search),
        ("RAG - Statistics", test_rag_stats),
        ("Weather - Multi-City", test_multi_city_weather),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            test_func()
            results.append((name, "✅ PASSED"))
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            results.append((name, f"❌ FAILED: {str(e)[:50]}"))
        
        input("\nPress Enter to continue to next test...")
    
    # Summary
    print_section("TEST SUMMARY")
    for name, status in results:
        print(f"{status} - {name}")
    
    print("\n" + "="*70)
    print("  Tests Complete!")
    print("="*70)
    print("\n💡 Check the workspace/ directory for generated files")
    print("💡 Check the logs/ directory for execution metrics")
    print("💡 Visit http://localhost:8000/docs for API documentation\n")


if __name__ == "__main__":
    main()
