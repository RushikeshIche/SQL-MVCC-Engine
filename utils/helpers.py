"""
Utility helper functions
"""

import time
import random
import string
from datetime import datetime
from typing import Any

def format_timestamp(timestamp: str = None) -> str:
    """Format timestamp for display"""
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp

def validate_sql_identifier(identifier: str) -> bool:
    """Validate SQL identifier"""
    if not identifier or not identifier.strip():
        return False
    
    # Basic validation - should start with letter, contain only alphanumeric and underscore
    return identifier.replace('_', '').isalnum() and identifier[0].isalpha()

def generate_id(length: int = 8) -> str:
    """Generate a random ID"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def safe_get(data: dict, key: str, default: Any = None) -> Any:
    """Safely get value from dictionary"""
    try:
        return data.get(key, default)
    except:
        return default

def format_query_result(result: dict) -> str:
    """Format query result for display"""
    if not result.get('success'):
        return f"❌ Error: {result.get('error', 'Unknown error')}"
    
    message = result.get('message', 'Query executed successfully')
    affected_rows = result.get('affected_rows', 0)
    
    if affected_rows > 0:
        return f"✅ {message} ({affected_rows} row(s) affected)"
    else:
        return f"✅ {message}"