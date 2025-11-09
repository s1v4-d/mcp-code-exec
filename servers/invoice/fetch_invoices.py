"""
Fetch invoice data.

Tool: fetch_invoices
Description: Retrieve invoice records for analysis.
"""

from typing import Dict, Any, List
from servers.client import mcp_client


async def fetch_invoices(month: str = "current_month", limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch invoice data for a specified month.
    
    Args:
        month: Month to fetch, one of:
            - "current_month": Current month's invoices
            - "last_month": Previous month's invoices
            - "YYYY-MM": Specific month (e.g., "2025-01")
            Default: "current_month"
        limit: Maximum number of invoices to return (default: 100)
    
    Returns:
        List of invoice dictionaries, each with structure:
        {
            "invoice_id": str,      # Unique invoice ID
            "customer_id": str,     # Customer identifier
            "amount": float,        # Invoice amount
            "date": str,            # Invoice date (YYYY-MM-DD)
            "status": str,          # "paid", "pending", or "overdue"
            "category": str         # "services", "products", "consulting", or "license"
        }
        
        Note: Mock data includes intentional duplicates and anomalies
        for testing detection algorithms.
    
    Example:
        >>> # Fetch current month's invoices
        >>> invoices = await fetch_invoices()
        >>> print(f"Retrieved {len(invoices)} invoices")
        
        >>> # Fetch specific month with limit
        >>> invoices = await fetch_invoices(month="2025-01", limit=50)
        
        >>> # Analyze invoice data
        >>> import pandas as pd
        >>> df = pd.DataFrame(invoices)
        >>> print(f"Total amount: ${df['amount'].sum():,.2f}")
        >>> print(f"Average amount: ${df['amount'].mean():,.2f}")
        
        >>> # Find duplicates
        >>> duplicates = df[df.duplicated(subset=['invoice_id'], keep=False)]
        >>> print(f"Found {len(duplicates)} duplicate invoices")
        
        >>> # Find anomalies (unusually high/low amounts)
        >>> mean = df['amount'].mean()
        >>> std = df['amount'].std()
        >>> anomalies = df[(df['amount'] > mean + 3*std) | (df['amount'] < mean - 3*std)]
    """
    return await mcp_client.call_tool("fetch_invoices", {
        "month": month,
        "limit": limit
    })
