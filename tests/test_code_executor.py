"""Test code executor."""

import pytest
from app.agent_core.code_executor import CodeExecutor


def test_simple_code_execution():
    """Test executing simple Python code."""
    executor = CodeExecutor()
    
    code = """
print("Hello from code executor")
result = 2 + 2
print(f"2 + 2 = {result}")
"""
    
    result = executor.execute(code)
    
    assert result["success"] is True
    assert "Hello from code executor" in result["output"]
    assert "2 + 2 = 4" in result["output"]
    assert result["execution_time_ms"] > 0


def test_code_with_pandas():
    """Test code using pandas."""
    executor = CodeExecutor()
    
    code = """
import pandas as pd

data = {'name': ['Alice', 'Bob'], 'age': [25, 30]}
df = pd.DataFrame(data)
print(f"Created DataFrame with {len(df)} rows")
"""
    
    result = executor.execute(code)
    
    assert result["success"] is True
    assert "Created DataFrame with 2 rows" in result["output"]


def test_code_validation():
    """Test code validation catches dangerous patterns."""
    executor = CodeExecutor()
    
    dangerous_code = """
import os
os.system('ls')
"""
    
    is_valid, error = executor.validate_code(dangerous_code)
    assert is_valid is False
    assert "import os" in error


def test_syntax_error():
    """Test handling of syntax errors."""
    executor = CodeExecutor()
    
    invalid_code = """
print("missing closing quote)
"""
    
    result = executor.execute(invalid_code)
    assert result["success"] is False
    assert result["error"] is not None


if __name__ == "__main__":
    test_simple_code_execution()
    test_code_with_pandas()
    test_code_validation()
    test_syntax_error()
    print("All code executor tests passed!")
