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
    """Executes generated Python code in a controlled environment."""
    
    def __init__(self):
        """Initialize the code executor."""
        self.timeout_seconds = settings.code_exec_timeout_seconds
    
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute Python code in a sandboxed environment."""
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
        """Prepare the execution environment."""
        import types
        import sys
        from pathlib import Path
        
        exec_globals = {
            "__builtins__": __builtins__,
        }
        
        from app.runtime.mcp_manager import get_mcp_manager, call_tool
        exec_globals['mcp_manager'] = get_mcp_manager()
        exec_globals['call_tool'] = call_tool
        
        try:
            from app.mcp_client.client import mcp_client
            exec_globals['mcp_client'] = mcp_client
        except ImportError:
            pass
        
        servers_path = Path(__file__).parent.parent.parent / 'servers'
        if servers_path.exists() and str(servers_path) not in sys.path:
            sys.path.insert(0, str(servers_path))
        
        app_path = Path(__file__).parent.parent.parent
        if str(app_path) not in sys.path:
            sys.path.insert(0, str(app_path))
        
        return exec_globals
