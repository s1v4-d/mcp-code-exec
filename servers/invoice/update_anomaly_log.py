"""
Update anomaly log.

Tool: update_anomaly_log
Description: Log detected invoice anomalies to the system.
"""

from typing import Dict, Any, List
from servers.client import mcp_client


async def update_anomaly_log(anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Log detected anomalies to the system.
    
    Use this to record invoice anomalies (duplicates, unusual amounts,
    suspicious patterns) for auditing and review.
    
    Args:
        anomalies: List of anomaly records to log. Each record should contain:
            {
                "invoice_id": str,
                "anomaly_type": str,     # e.g., "duplicate", "high_amount", "low_amount"
                "severity": str,         # e.g., "low", "medium", "high"
                "description": str,      # Human-readable description
                "amount": float,         # Invoice amount
                ...                      # Any other relevant fields
            }
    
    Returns:
        Confirmation dictionary with structure:
        {
            "log_id": str,          # Log identifier (LOG-YYYYMMDD-HHMMSS)
            "count": int,           # Number of anomalies logged
            "status": "logged",
            "timestamp": str        # ISO format timestamp
        }
    
    Example:
        >>> # Detect and log duplicates
        >>> invoices = await fetch_invoices()
        >>> import pandas as pd
        >>> df = pd.DataFrame(invoices)
        >>> 
        >>> # Find duplicates
        >>> duplicates = df[df.duplicated(subset=['invoice_id'], keep=False)]
        >>> 
        >>> # Create anomaly records
        >>> anomalies = []
        >>> for _, row in duplicates.iterrows():
        ...     anomalies.append({
        ...         "invoice_id": row['invoice_id'],
        ...         "anomaly_type": "duplicate",
        ...         "severity": "high",
        ...         "description": f"Duplicate invoice ID found",
        ...         "amount": row['amount'],
        ...         "date": row['date']
        ...     })
        >>> 
        >>> # Log them
        >>> result = await update_anomaly_log(anomalies)
        >>> print(f"Logged {result['count']} anomalies with ID: {result['log_id']}")
        
        >>> # Detect high-value anomalies
        >>> mean = df['amount'].mean()
        >>> std = df['amount'].std()
        >>> high_amounts = df[df['amount'] > mean + 3*std]
        >>> 
        >>> anomalies = [{
        ...     "invoice_id": row['invoice_id'],
        ...     "anomaly_type": "high_amount",
        ...     "severity": "medium",
        ...     "description": f"Amount ${row['amount']:,.2f} exceeds 3σ threshold",
        ...     "amount": row['amount']
        ... } for _, row in high_amounts.iterrows()]
        >>> 
        >>> result = await update_anomaly_log(anomalies)
    
    Raises:
        ValueError: If anomalies list is empty
    """
    return await mcp_client.call_tool("update_anomaly_log", {
        "anomalies": anomalies
    })
