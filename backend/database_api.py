"""
Database API wrapper for the MVCC Engine
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from engine.database import Database

class DatabaseAPI:
    def __init__(self):
        self.db = Database("mvcc_database")
        self.query_history = []
    
    def execute_query(self, query: str, txn_id: int = None):
        """Execute query and maintain history"""
        result = self.db.execute(query, txn_id)
        
        # Add to history
        self.query_history.append({
            'query': query,
            'success': result['success'],
            'timestamp': self._get_timestamp(),
            'execution_time': 0.0,  # Would be calculated in main API
            'transaction_id': txn_id
        })
        
        # Keep only last 100 queries
        if len(self.query_history) > 100:
            self.query_history.pop(0)
            
        return result
    
    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()