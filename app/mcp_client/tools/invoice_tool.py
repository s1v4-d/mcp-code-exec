"""Invoice tool for MCP - Example implementation."""

from typing import Dict, Any, List
import random
from datetime import datetime, timedelta


class InvoiceTool:
    """
    Example MCP tool for invoice operations.
    
    In production, this would connect to a real invoice system.
    For the PoC, we generate mock data.
    """
    
    def fetch_invoices(self, month: str = "current_month", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch invoice data.
        
        Args:
            month: Month to fetch ('current_month', 'last_month', or 'YYYY-MM')
            limit: Maximum number of invoices to return
            
        Returns:
            List of invoice records
        """
        print(f"[MCP Tool] Fetching invoices for {month} (limit: {limit})")
        
        # Generate mock invoice data
        invoices = []
        base_date = datetime.now()
        
        if month == "last_month":
            base_date = base_date - timedelta(days=30)
        
        for i in range(limit):
            invoice_id = f"INV-{base_date.year}-{i+1:05d}"
            
            # Intentionally create some duplicates and anomalies
            if i % 20 == 0 and i > 0:
                # Duplicate - same ID as previous
                invoice_id = f"INV-{base_date.year}-{i:05d}"
            
            amount = round(random.uniform(100, 10000), 2)
            
            # Create anomalies
            if i % 15 == 0:
                amount = round(random.uniform(50000, 100000), 2)  # Unusually high
            if i % 25 == 0:
                amount = round(random.uniform(1, 10), 2)  # Unusually low
            
            invoice = {
                "invoice_id": invoice_id,
                "customer_id": f"CUST-{random.randint(1, 50):04d}",
                "amount": amount,
                "date": (base_date - timedelta(days=random.randint(0, 28))).strftime("%Y-%m-%d"),
                "status": random.choice(["paid", "pending", "overdue"]),
                "category": random.choice(["services", "products", "consulting", "license"])
            }
            invoices.append(invoice)
        
        return invoices
    
    def update_anomaly_log(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Log detected anomalies.
        
        Args:
            anomalies: List of anomaly records
            
        Returns:
            Confirmation with log ID
        """
        print(f"[MCP Tool] Logging {len(anomalies)} anomalies")
        
        log_id = f"LOG-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        return {
            "log_id": log_id,
            "count": len(anomalies),
            "status": "logged",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get tool definitions for MCP registration.
        
        Returns:
            Dictionary of tool definitions
        """
        return {
            "fetch_invoices": {
                "description": "Fetch invoice data for a specified month. Returns list of invoice records.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "month": {
                            "type": "string",
                            "description": "Month to fetch: 'current_month', 'last_month', or 'YYYY-MM'",
                            "default": "current_month"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of invoices to return",
                            "default": 100
                        }
                    }
                },
                "function": self.fetch_invoices
            },
            "update_anomaly_log": {
                "description": "Log detected anomalies to the system. Returns confirmation with log ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "anomalies": {
                            "type": "array",
                            "description": "List of anomaly records to log",
                            "items": {"type": "object"}
                        }
                    },
                    "required": ["anomalies"]
                },
                "function": self.update_anomaly_log
            }
        }
