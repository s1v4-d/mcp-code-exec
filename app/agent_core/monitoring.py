"""Monitoring and metrics collection."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from app.config import settings


class Metrics:
    """Collects and persists execution metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.start_time = None
        self.end_time = None
        self.data = {}
    
    def start(self):
        """Start timing."""
        self.start_time = datetime.now()
    
    def end(self):
        """End timing."""
        self.end_time = datetime.now()
    
    def record(self, **kwargs):
        """
        Record metric data.
        
        Args:
            **kwargs: Metric key-value pairs
        """
        self.data.update(kwargs)
    
    def get_total_time_ms(self) -> int:
        """
        Calculate total execution time.
        
        Returns:
            Total time in milliseconds
        """
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() * 1000)
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metrics to dictionary.
        
        Returns:
            Dictionary of metrics
        """
        metrics_dict = {
            "timestamp": self.start_time.isoformat() if self.start_time else None,
            "total_time_ms": self.get_total_time_ms(),
            **self.data
        }
        
        # Calculate token efficiency metrics (as per Anthropic paper)
        if "tokens_used" in self.data:
            # Estimate what tokens would have been with full tool loading
            # Assuming ~10 tools x ~500 tokens each = ~5000 tokens baseline
            tools_available = self.data.get("tools_available", 10)
            estimated_full_load = tools_available * 500  # Rough estimate
            
            tokens_used = self.data["tokens_used"]
            if tokens_used > 0:
                tokens_saved = max(0, estimated_full_load - tokens_used)
                efficiency_pct = (tokens_saved / estimated_full_load * 100) if estimated_full_load > 0 else 0
                
                metrics_dict["token_efficiency"] = {
                    "tokens_used": tokens_used,
                    "estimated_full_load_tokens": estimated_full_load,
                    "tokens_saved": tokens_saved,
                    "efficiency_percentage": round(efficiency_pct, 1),
                    "tools_available": tools_available,
                    "tools_loaded_estimated": self.data.get("tools_loaded", "unknown")
                }
        
        return metrics_dict
    
    def save_to_log(self, additional_data: Dict[str, Any] = None):
        """
        Save metrics to log file.
        
        Args:
            additional_data: Additional data to include in log
        """
        log_data = self.to_dict()
        
        if additional_data:
            log_data.update(additional_data)
        
        # Generate log filename
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S") if self.start_time else "unknown"
        log_file = settings.logs_path / f"run_{timestamp}.json"
        
        # Save to file
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"[Monitoring] Metrics saved to {log_file}")
        
        return str(log_file)


class MonitoringCollector:
    """Singleton for collecting monitoring data across the application."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MonitoringCollector, cls).__new__(cls)
            cls._instance.runs = []
        return cls._instance
    
    def add_run(self, metrics: Dict[str, Any]):
        """
        Add a run to the monitoring history.
        
        Args:
            metrics: Metrics dictionary from a run
        """
        self.runs.append(metrics)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics across all runs.
        
        Returns:
            Dictionary with summary stats
        """
        if not self.runs:
            return {"total_runs": 0}
        
        total_runs = len(self.runs)
        successful_runs = sum(1 for r in self.runs if r.get("status") == "success")
        failed_runs = total_runs - successful_runs
        
        total_tokens = sum(r.get("tokens_used", 0) for r in self.runs)
        avg_exec_time = sum(r.get("code_exec_time_ms", 0) for r in self.runs) / total_runs if total_runs > 0 else 0
        
        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "total_tokens_used": total_tokens,
            "avg_execution_time_ms": round(avg_exec_time, 2),
            "success_rate": round(successful_runs / total_runs * 100, 2) if total_runs > 0 else 0
        }


# Global monitoring instance
monitoring = MonitoringCollector()
