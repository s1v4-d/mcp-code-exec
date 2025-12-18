"""Runtime Harness for Safe Code Execution."""

import asyncio
import signal
import sys
import io
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import redirect_stdout, redirect_stderr


class ExecutionTimeout(Exception):
    """Raised when code execution exceeds time limit."""
    pass


class ExecutionHarness:
    """Secure runtime harness for executing agent-generated code."""
    
    def __init__(
        self,
        timeout_seconds: int = 30,
        workspace_dir: str = "workspace",
        allowed_modules: Optional[list] = None,
    ):
        """Initialize execution harness.
        
        Args:
            timeout_seconds: Maximum execution time
            workspace_dir: Working directory for file operations
            allowed_modules: List of allowed import modules (None = use defaults)
        """
        self.timeout_seconds = timeout_seconds
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)
        
        # Store original signal handlers for restoration
        self._original_sigint = None
        self._original_sigterm = None
        self._shutdown_requested = False
        
        # Default allowed modules (can be extended)
        self.allowed_modules = allowed_modules or [
            'json', 'datetime', 'typing', 're', 'math', 'statistics',
            'pandas', 'numpy', 'collections', 'itertools', 'functools',
            'pathlib', 'csv', 'os', 'sys', 'asyncio'
        ]
    
    async def execute_async(self, code: str) -> Dict[str, Any]:
        """Execute code asynchronously with timeout.
        
        Args:
            code: Python code to execute
            
        Returns:
            Execution result dictionary with keys:
                - success: bool
                - output: str (captured stdout)
                - error: Optional[str]
                - execution_time_ms: int
        """
        try:
            # Ensure MCP manager is initialized before execution
            await self._ensure_mcp_initialized()
            
            # Run execution with asyncio timeout instead of signals
            return await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, self.execute_sync_no_signal, code),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            return {
                "success": False,
                "output": "",
                "error": f"Execution timeout after {self.timeout_seconds} seconds",
                "execution_time_ms": self.timeout_seconds * 1000
            }
    
    async def _ensure_mcp_initialized(self):
        """Ensure MCP manager is initialized."""
        from app.runtime.mcp_manager import get_mcp_manager, ConnectionState
        
        manager = get_mcp_manager()
        if manager._state == ConnectionState.UNINITIALIZED:
            await manager.load_config()
    
    def execute_sync(self, code: str) -> Dict[str, Any]:
        """Execute code synchronously with timeout protection."""
        start_time = time.time()
        
        # Prepare result structure
        result = {
            "success": False,
            "output": "",
            "error": None,
            "execution_time_ms": 0
        }
        
        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Save original signal handlers (only works in main thread)
        old_alarm_handler = None
        try:
            if hasattr(signal, 'SIGALRM'):
                old_alarm_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
            # Also set up SIGINT/SIGTERM handlers for graceful shutdown
            self._setup_shutdown_handlers()
        except ValueError:
            # Not in main thread, skip signal handling
            pass
        
        try:
            # Set timeout alarm (only if in main thread)
            if old_alarm_handler is not None and hasattr(signal, 'SIGALRM'):
                signal.alarm(self.timeout_seconds)
            
            # Check if shutdown requested before executing
            if self._shutdown_requested:
                result["error"] = "Execution cancelled: shutdown requested"
                return result
            
            # Prepare execution environment
            exec_globals = self._prepare_environment()
            
            # Execute with captured output
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, exec_globals)
            
            # Success
            result["success"] = True
            result["output"] = stdout_capture.getvalue()
            
        except ExecutionTimeout:
            result["error"] = f"Execution timeout after {self.timeout_seconds} seconds"
            result["output"] = stdout_capture.getvalue()
        
        except KeyboardInterrupt:
            result["error"] = "Execution interrupted by user (SIGINT)"
            result["output"] = stdout_capture.getvalue()
            
        except ImportError as e:
            result["error"] = f"Import error: {str(e)}\nAllowed modules: {', '.join(self.allowed_modules)}"
            result["output"] = stdout_capture.getvalue()
            
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            result["output"] = stdout_capture.getvalue()
            
        finally:
            # Cancel timeout and restore handlers (only if in main thread)
            if old_alarm_handler is not None and hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_alarm_handler)
            self._restore_shutdown_handlers()
            
            # Record execution time
            result["execution_time_ms"] = int((time.time() - start_time) * 1000)
        
        # Append stderr if present
        stderr_output = stderr_capture.getvalue()
        if stderr_output:
            result["output"] += f"\n[STDERR]\n{stderr_output}"
        
        return result
    
    def execute_sync_no_signal(self, code: str) -> Dict[str, Any]:
        """Execute code synchronously without signal handling (thread-safe).
        
        Supports both sync and async code execution.
        
        Args:
            code: Python code to execute
            
        Returns:
            Execution result dictionary
        """
        start_time = time.time()
        
        # Prepare result structure
        result = {
            "success": False,
            "output": "",
            "error": None,
            "execution_time_ms": 0
        }
        
        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            # Prepare execution environment
            exec_globals = self._prepare_environment()
            
            # Execute with captured output
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Check if code contains async/await OR mcp_client.call_tool
                # mcp_client.call_tool is now async and needs to be awaited
                needs_async = (
                    'await ' in code or 
                    'async ' in code or 
                    'mcp_client.call_tool' in code
                )
                
                if needs_async:
                    # Wrap code in async main function
                    wrapped_code = f"""
import asyncio

async def __async_main__():
{chr(10).join('    ' + line for line in code.split(chr(10)))}

asyncio.run(__async_main__())
"""
                    exec(wrapped_code, exec_globals)
                else:
                    exec(code, exec_globals)
            
            # Success
            result["success"] = True
            result["output"] = stdout_capture.getvalue()
            
        except ImportError as e:
            result["error"] = f"Import error: {str(e)}\nAllowed modules: {', '.join(self.allowed_modules)}"
            result["output"] = stdout_capture.getvalue()
            
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            result["output"] = stdout_capture.getvalue()
            
        finally:
            # Record execution time
            result["execution_time_ms"] = int((time.time() - start_time) * 1000)
        
        # Append stderr if present
        stderr_output = stderr_capture.getvalue()
        if stderr_output:
            result["output"] += f"\n[STDERR]\n{stderr_output}"
        
        return result
    
    def _timeout_handler(self, signum, frame):
        """Signal handler for timeout (SIGALRM)."""
        raise ExecutionTimeout("Code execution timed out")
    
    def _shutdown_handler(self, signum, frame):
        """Signal handler for graceful shutdown (SIGINT/SIGTERM).
        
        Sets shutdown flag but doesn't raise immediately,
        allowing cleanup to complete.
        """
        self._shutdown_requested = True
        signal_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else str(signum)
        raise KeyboardInterrupt(f"Shutdown requested via {signal_name}")
    
    def _setup_shutdown_handlers(self):
        """Set up SIGINT/SIGTERM handlers for graceful shutdown."""
        try:
            # Save original handlers
            self._original_sigint = signal.signal(signal.SIGINT, self._shutdown_handler)
            self._original_sigterm = signal.signal(signal.SIGTERM, self._shutdown_handler)
        except (ValueError, OSError):
            # Not in main thread or signal not supported
            pass
    
    def _restore_shutdown_handlers(self):
        """Restore original SIGINT/SIGTERM handlers."""
        try:
            if self._original_sigint is not None:
                signal.signal(signal.SIGINT, self._original_sigint)
            if self._original_sigterm is not None:
                signal.signal(signal.SIGTERM, self._original_sigterm)
        except (ValueError, OSError):
            pass
    
    def _prepare_environment(self) -> Dict[str, Any]:
        """Prepare execution environment with allowed modules.
        
        Returns:
            Dictionary of globals for exec()
        """
        # Start with safe builtins
        exec_globals = {
            "__builtins__": self._get_safe_builtins(),
            "__name__": "__main__",
        }
        
        # Import allowed modules
        for module_name in self.allowed_modules:
            try:
                if module_name == 'pandas':
                    import pandas as pd
                    exec_globals['pd'] = pd
                    exec_globals['pandas'] = pd
                elif module_name == 'numpy':
                    import numpy as np
                    exec_globals['np'] = np
                    exec_globals['numpy'] = np
                elif module_name == 'pathlib':
                    from pathlib import Path
                    exec_globals['Path'] = Path
                    exec_globals['pathlib'] = __import__('pathlib')
                elif module_name == 'asyncio':
                    import asyncio
                    exec_globals['asyncio'] = asyncio
                else:
                    exec_globals[module_name] = __import__(module_name)
            except ImportError:
                pass  # Module not available
        
        # Add servers path for tool imports
        servers_path = Path(__file__).parent.parent.parent / 'servers'
        if servers_path.exists() and str(servers_path) not in sys.path:
            sys.path.insert(0, str(servers_path))
        
        # Add tool discovery
        from servers.discovery import tool_discovery
        exec_globals['tool_discovery'] = tool_discovery
        
        # Add MCP client (legacy support)
        from app.mcp_client.client import mcp_client
        exec_globals['mcp_client'] = mcp_client
        
        return exec_globals
    
    def _get_safe_builtins(self) -> Dict[str, Any]:
        """Get restricted builtin functions.
        
        Returns:
            Dictionary of safe builtins
        """
        safe_builtins = {
            # Type constructors
            'str': str, 'int': int, 'float': float, 'bool': bool,
            'list': list, 'dict': dict, 'set': set, 'tuple': tuple,
            'bytes': bytes, 'bytearray': bytearray,
            
            # Functions
            'print': print, 'len': len, 'range': range,
            'abs': abs, 'min': min, 'max': max, 'sum': sum,
            'sorted': sorted, 'reversed': reversed,
            'enumerate': enumerate, 'zip': zip,
            'map': map, 'filter': filter, 'all': all, 'any': any,
            'round': round, 'pow': pow, 'divmod': divmod,
            
            # Type checking
            'isinstance': isinstance, 'issubclass': issubclass,
            'hasattr': hasattr, 'getattr': getattr, 'setattr': setattr,
            'delattr': delattr, 'type': type, 'id': id,
            'callable': callable, 'dir': dir, 'vars': vars,
            
            # File I/O (restricted to workspace)
            'open': self._safe_open,
            
            # Exceptions
            'Exception': Exception,
            'ValueError': ValueError, 'TypeError': TypeError,
            'KeyError': KeyError, 'IndexError': IndexError,
            'AttributeError': AttributeError, 'RuntimeError': RuntimeError,
            'ImportError': ImportError, 'OSError': OSError,
            
            # Other utilities
            'format': format, 'repr': repr, 'ascii': ascii,
            'ord': ord, 'chr': chr, 'hex': hex, 'oct': oct, 'bin': bin,
            'hash': hash, 'slice': slice, 'complex': complex,
            
            # Allow imports
            '__import__': __import__,
        }
        
        return safe_builtins
    
    def _safe_open(self, filename, mode='r', **kwargs):
        """Safe file open restricted to workspace directory.
        
        Args:
            filename: File path
            mode: File mode
            **kwargs: Additional arguments for open()
            
        Returns:
            File handle
            
        Raises:
            PermissionError: If file is outside workspace
        """
        file_path = Path(filename).resolve()
        workspace_path = self.workspace_dir.resolve()
        
        # Ensure file is within workspace
        try:
            file_path.relative_to(workspace_path)
        except ValueError:
            raise PermissionError(
                f"File access denied: '{filename}' is outside workspace directory. "
                f"Only files in '{workspace_path}' are accessible."
            )
        
        # Create parent directory if needed (for write modes)
        if 'w' in mode or 'a' in mode or 'x' in mode:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        return open(file_path, mode, **kwargs)
    
    def validate_code(self, code: str) -> tuple[bool, str]:
        """Validate code before execution.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for dangerous patterns
        dangerous_patterns = [
            ('subprocess', 'subprocess module not allowed'),
            ('eval(', 'eval() not allowed'),
            ('compile(', 'compile() not allowed'),
            ('__builtins__', 'direct __builtins__ access not allowed'),
        ]
        
        for pattern, message in dangerous_patterns:
            if pattern in code:
                return False, message
        
        # Try to compile
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
        
        return True, ""
