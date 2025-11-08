"""Demo script to test the agent without API calls."""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agent_core.orchestrator import AgentOrchestrator
from app.config import settings


async def run_demo():
    """Run a demo of the agent."""
    print("=" * 80)
    print("MCP Code Execution Agent - Demo")
    print("=" * 80)
    print()
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    
    # Example requests
    examples = [
        {
            "request": "Fetch invoice data for last month (limit 50), find duplicate invoices and anomalies (amounts > $50000 or < $50), then save the results to a CSV file",
            "parameters": {"month": "last_month", "limit": 50}
        },
        {
            "request": "Get invoices from current month (limit 30), calculate the total amount by category, and summarize the findings",
            "parameters": {"month": "current_month", "limit": 30}
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{'=' * 80}")
        print(f"Example {i}: {example['request']}")
        print(f"Parameters: {example['parameters']}")
        print(f"{'=' * 80}\n")
        
        try:
            result = await orchestrator.execute(
                user_request=example['request'],
                parameters=example['parameters']
            )
            
            print(f"\n✅ Status: {result['status']}")
            print(f"📝 Summary: {result['summary']}")
            
            if result.get('output_file'):
                print(f"📁 Output File: {result['output_file']}")
            
            print(f"\n📊 Metrics:")
            for key, value in result['metrics'].items():
                print(f"   {key}: {value}")
            
            if result.get('code_output'):
                print(f"\n📜 Code Output:")
                print(result['code_output'])
            
            if result.get('error'):
                print(f"\n❌ Error: {result['error']}")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        if i < len(examples):
            print("\n" + "." * 80)
            await asyncio.sleep(2)  # Brief pause between examples
    
    print(f"\n{'=' * 80}")
    print("Demo Complete!")
    print(f"{'=' * 80}")
    print(f"\nCheck the following directories:")
    print(f"  - Logs: {settings.logs_path}")
    print(f"  - Workspace: {settings.workspace_path}")


if __name__ == "__main__":
    # Check if OpenAI key is set
    if not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here":
        print("❌ Error: Please set OPENAI_API_KEY in .env file")
        print("\nCopy .env.example to .env and add your OpenAI API key:")
        print("  cp .env.example .env")
        print("  # Edit .env and add your API key")
        sys.exit(1)
    
    asyncio.run(run_demo())
