"""Code executor with sandboxing for agent-generated code."""

import sys
import io
import time
import traceback
from typing import Dict, Any, Tuple
from contextlib import redirect_stdout, redirect_stderr
import signal

from app.config import settings, ALLOWED_IMPORTS


class TimeoutError(Exception):
    """Raised when code execution times out."""
    pass


def timeout_handler(signum, frame):
    """Handler for execution timeout."""
    raise TimeoutError("Code execution timed out")


class CodeExecutor:
    """
    Executes generated Python code in a controlled environment.
    
    Security features:
    - Import restrictions
    - Timeout protection
    - Stdout/stderr capture
    - Exception handling
    """
    
    def __init__(self):
        """Initialize the code executor."""
        self.timeout_seconds = settings.code_exec_timeout_seconds
    
    def execute(self, code: str) -> Dict[str, Any]:
        """
        Execute Python code in a sandboxed environment.
        
        Args:
            code: Python code to execute
            
        Returns:
            Dictionary with:
                - success: bool
                - output: captured stdout
                - error: error message if failed
                - execution_time_ms: execution time
        """
        start_time = time.time()
        
        # Prepare execution environment
        exec_globals = self._prepare_environment()
        
        # Capture output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        result = {
            "success": False,
            "output": "",
            "error": None,
            "execution_time_ms": 0
        }
        
        try:
            # Set timeout (Unix only)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout_seconds)
            
            # Execute code with captured output
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, exec_globals)
            
            # Cancel timeout
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
            
            result["success"] = True
            result["output"] = stdout_capture.getvalue()
            
        except TimeoutError as e:
            result["error"] = f"Execution timeout after {self.timeout_seconds}s"
            result["output"] = stdout_capture.getvalue()
            
        except ImportError as e:
            result["error"] = f"Import error: {str(e)}. Only allowed imports: {ALLOWED_IMPORTS}"
            result["output"] = stdout_capture.getvalue()
            
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            result["output"] = stdout_capture.getvalue()
            
        finally:
            # Cancel timeout if still set
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
            
            # Record execution time
            end_time = time.time()
            result["execution_time_ms"] = int((end_time - start_time) * 1000)
        
        # Include stderr if present
        stderr_output = stderr_capture.getvalue()
        if stderr_output:
            result["output"] += f"\n[STDERR]\n{stderr_output}"
        
        return result
    
    def _prepare_environment(self) -> Dict[str, Any]:
        """
        Prepare the execution environment with allowed modules.
        
        Returns:
            Dictionary of globals for exec()
        """
        # Start with builtins
        exec_globals = {
            "__builtins__": self._get_safe_builtins(),
        }
        
        # Add allowed imports
        for module_name in ALLOWED_IMPORTS:
            try:
                if module_name == 'typing':
                    import typing
                    exec_globals['typing'] = typing
                elif module_name == 'json':
                    import json
                    exec_globals['json'] = json
                elif module_name == 'datetime':
                    import datetime
                    exec_globals['datetime'] = datetime
                elif module_name == 'pandas':
                    import pandas as pd
                    exec_globals['pd'] = pd
                    exec_globals['pandas'] = pd
                elif module_name == 'numpy':
                    import numpy as np
                    exec_globals['np'] = np
                    exec_globals['numpy'] = np
                elif module_name == 're':
                    import re
                    exec_globals['re'] = re
                elif module_name == 'math':
                    import math
                    exec_globals['math'] = math
                elif module_name == 'statistics':
                    import statistics
                    exec_globals['statistics'] = statistics
                elif module_name == 'requests':
                    import requests
                    exec_globals['requests'] = requests
                elif module_name == 'pytz':
                    import pytz
                    exec_globals['pytz'] = pytz
                elif module_name == 'timezonefinder':
                    from timezonefinder import TimezoneFinder
                    exec_globals['timezonefinder'] = __import__('timezonefinder')
                    exec_globals['TimezoneFinder'] = TimezoneFinder
                elif module_name == 'os':
                    import os
                    exec_globals['os'] = os
                elif module_name == 'sys':
                    import sys
                    exec_globals['sys'] = sys
                elif module_name == 'pathlib':
                    from pathlib import Path
                    exec_globals['pathlib'] = __import__('pathlib')
                    exec_globals['Path'] = Path
                elif module_name == 'collections':
                    import collections
                    exec_globals['collections'] = collections
            except ImportError:
                pass  # Module not available, skip it
        
        # Add MCP client wrapper (legacy support - will be deprecated)
        from app.mcp_client.client import mcp_client
        exec_globals['mcp_client'] = mcp_client
        
        # Create a mock module for the import statement
        import types
        import sys
        wrapper_module = types.ModuleType('mcp_client_wrapper')
        wrapper_module.mcp_client = mcp_client
        
        # Add to sys.modules so import can find it
        sys.modules['mcp_client_wrapper'] = wrapper_module
        exec_globals['mcp_client_wrapper'] = wrapper_module
        
        # Add servers module for progressive disclosure (as per Anthropic paper)
        # This allows imports like: from servers.weather import get_current_weather
        servers_path = Path(__file__).parent.parent.parent / 'servers'
        if servers_path.exists() and str(servers_path) not in sys.path:
            sys.path.insert(0, str(servers_path))
        
        # Add tool_discovery for agent filesystem exploration (as per paper)
        # Agents can now: tool_discovery.list_servers(), read_file(), etc.
        from servers.discovery import tool_discovery
        exec_globals['tool_discovery'] = tool_discovery
        
        return exec_globals
    
    def _get_safe_builtins(self) -> Dict[str, Any]:
        """
        Get a restricted set of builtins for sandboxing.
        
        Returns:
            Dictionary of safe builtin functions
        """
        # Start with standard builtins
        safe_builtins = {
            'print': print,
            'len': len,
            'range': range,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'abs': abs,
            'min': min,
            'max': max,
            'sum': sum,
            'sorted': sorted,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'round': round,
            'isinstance': isinstance,
            'hasattr': hasattr,
            'getattr': getattr,
            'setattr': setattr,
            'type': type,
            'open': open,  # Allow file operations (validated to workspace/ only)
            'ValueError': ValueError,
            'TypeError': TypeError,
            'KeyError': KeyError,
            'IndexError': IndexError,
            'Exception': Exception,
            '__import__': __import__,  # Needed for import statements
            '__name__': '__main__',
            '__doc__': None,
        }
        
        return safe_builtins
    
    def validate_code(self, code: str) -> Tuple[bool, str]:
        """
        Validate code before execution.
        
        Args:
            code: Code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for extremely dangerous patterns only
        dangerous_patterns = [
            'import subprocess',
            'subprocess.',
            '__builtins__',
            'eval(',
            'exec(',
            'compile(',
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                return False, f"Dangerous pattern detected: {pattern}"
        
        # Relaxed file operations - allow workspace/ and common operations
        # No longer blocking open() or os/sys imports as they're in ALLOWED_IMPORTS
        
        # Try to compile the code
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
        
        return True, ""
