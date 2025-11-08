#!/usr/bin/env python3
"""
Example script demonstrating Weather API and RAG system usage.

This script shows how to:
1. Get current weather for a city
2. Get weather forecast
3. Add documents to RAG index
4. Search documents
5. Get context for LLM prompts
"""

import requests
import json
from pathlib import Path


BASE_URL = "http://localhost:8000/api/v1"


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_weather():
    """Demonstrate weather API features."""
    print_section("WEATHER API DEMO")
    
    # 1. Get current weather
    print("1. Getting current weather for San Francisco...")
    response = requests.post(f"{BASE_URL}/weather/current", json={
        "city_name": "San Francisco",
        "country_name": "US"
    })
    
    if response.status_code == 200:
        data = response.json()
        weather = data['data']
        print(f"   Location: {data['location']}")
        print(f"   Temperature: {weather['main']['temp']}°F")
        print(f"   Feels like: {weather['main']['feels_like']}°F")
        print(f"   Humidity: {weather['main']['humidity']}%")
        print(f"   Description: {weather['weather'][0]['description']}")
    else:
        print(f"   Error: {response.status_code} - {response.text}")
    
    # 2. Get forecast
    print("\n2. Getting forecast for London, 2 days ahead at 3 PM...")
    response = requests.post(f"{BASE_URL}/weather/forecast", json={
        "city_name": "London",
        "country_name": "UK",
        "days": 2,
        "hour": 15
    })
    
    if response.status_code == 200:
        data = response.json()
        forecast = data['data']
        print(f"   Location: {data['location']}")
        print(f"   Temperature: {forecast['main']['temp']}°F")
        print(f"   Conditions: {forecast['weather'][0]['description']}")
        print(f"   Time: {forecast.get('dt_txt', 'N/A')}")
    else:
        print(f"   Error: {response.status_code} - {response.text}")
    
    # 3. Get geographic data
    print("\n3. Getting geographic data for Tokyo...")
    response = requests.get(f"{BASE_URL}/weather/geo/Tokyo", params={"country": "Japan"})
    
    if response.status_code == 200:
        data = response.json()
        geo = data['data']
        print(f"   Location: {geo.get('name', 'Tokyo')}")
        print(f"   Latitude: {geo['lat']}")
        print(f"   Longitude: {geo['lon']}")
        print(f"   Country: {geo.get('country', 'N/A')}")
    else:
        print(f"   Error: {response.status_code} - {response.text}")


def demo_rag():
    """Demonstrate RAG system features."""
    print_section("RAG SYSTEM DEMO")
    
    # 1. Add documents
    print("1. Adding sample documents to RAG index...")
    documents = [
        "Machine learning is a subset of artificial intelligence that focuses on building systems that learn from data.",
        "Neural networks are computing systems inspired by biological neural networks. They consist of layers of interconnected nodes.",
        "Deep learning uses neural networks with multiple layers to progressively extract higher-level features from raw input.",
        "Natural language processing (NLP) is a branch of AI that helps computers understand and process human language.",
        "Computer vision enables computers to derive meaningful information from digital images and videos."
    ]
    
    response = requests.post(f"{BASE_URL}/rag/documents/add", json={
        "texts": documents,
        "source": "ai-concepts",
        "metadatas": [
            {"topic": "machine-learning"},
            {"topic": "neural-networks"},
            {"topic": "deep-learning"},
            {"topic": "nlp"},
            {"topic": "computer-vision"}
        ]
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: {data['status']}")
        print(f"   Chunks added: {data['chunks_added']}")
        print(f"   Total documents: {data['total_documents']}")
    else:
        print(f"   Error: {response.status_code} - {response.text}")
    
    # 2. Search documents
    print("\n2. Searching for 'neural networks'...")
    response = requests.post(f"{BASE_URL}/rag/search", json={
        "query": "What are neural networks?",
        "k": 2
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Query: {data['query']}")
        print(f"   Found {data['total_results']} results:\n")
        
        for i, result in enumerate(data['results'], 1):
            print(f"   Result {i}:")
            print(f"   Score: {result['score']:.4f}")
            print(f"   Content: {result['content']}")
            print(f"   Topic: {result['metadata'].get('topic', 'N/A')}\n")
    else:
        print(f"   Error: {response.status_code} - {response.text}")
    
    # 3. Get context for LLM
    print("\n3. Getting context for 'deep learning'...")
    response = requests.post(f"{BASE_URL}/rag/context", json={
        "query": "Explain deep learning",
        "k": 3
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Query: {data['query']}")
        print(f"   Documents retrieved: {data['num_documents']}")
        print(f"\n   Context:\n")
        print(f"   {data['context'][:300]}...")
    else:
        print(f"   Error: {response.status_code} - {response.text}")
    
    # 4. Get index statistics
    print("\n4. Getting RAG index statistics...")
    response = requests.get(f"{BASE_URL}/rag/stats")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Total chunks: {data['total_chunks']}")
        print(f"   Sources: {', '.join(data['sources'])}")
        
        if data['source_details']:
            print("\n   Source details:")
            for source, details in data['source_details'].items():
                print(f"     - {source}:")
                print(f"       Documents: {details['document_count']}")
                print(f"       Chunks: {details['chunk_count']}")
    else:
        print(f"   Error: {response.status_code} - {response.text}")


def demo_file_upload():
    """Demonstrate file upload to RAG."""
    print_section("RAG FILE UPLOAD DEMO")
    
    # Create a sample file
    sample_file = Path("/tmp/sample_doc.txt")
    sample_content = """
    Python is a high-level, interpreted programming language known for its simplicity and readability.
    It was created by Guido van Rossum and first released in 1991.
    
    Python is widely used in:
    - Web development (Django, Flask)
    - Data science and machine learning (NumPy, Pandas, Scikit-learn)
    - Automation and scripting
    - Scientific computing
    - Artificial intelligence
    
    The language emphasizes code readability with its notable use of significant whitespace.
    """
    
    sample_file.write_text(sample_content)
    print(f"Created sample file: {sample_file}")
    
    # Upload file
    print("\nUploading file to RAG index...")
    with open(sample_file, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/rag/documents/upload",
            files={"file": f},
            params={"source": "python-intro"}
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: {data['status']}")
        print(f"   Chunks added: {data['chunks_added']}")
        print(f"   Source: {data['source']}")
    else:
        print(f"   Error: {response.status_code} - {response.text}")
    
    # Clean up
    sample_file.unlink()
    print(f"\nCleaned up sample file")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("  MCP Code Execution Agent - Weather & RAG Demo")
    print("="*60)
    print("\nMake sure the server is running on http://localhost:8000")
    print("Start with: python -m app.main")
    
    try:
        # Test connection
        response = requests.get(f"http://localhost:8000/health", timeout=2)
        if response.status_code != 200:
            print("\n❌ Server not responding properly!")
            return
        
        print("✅ Server is running\n")
        
        # Run demos
        demo_weather()
        demo_rag()
        demo_file_upload()
        
        print_section("DEMO COMPLETE")
        print("Check out the API docs at: http://localhost:8000/docs")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server!")
        print("Make sure the server is running: python -m app.main")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
