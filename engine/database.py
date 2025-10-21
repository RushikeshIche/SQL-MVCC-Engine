"""
Database Core - Manages the overall database operations
"""

import threading
from typing import Dict, Any, List
from .parser import SQLParser
from .executor import QueryExecutor
from .mvcc_enhanced import EnhancedMVCCManager
from .storage import StorageEngine

class Database:
    """Main database class that coordinates all components"""
    
    def __init__(self, name: str = "mvcc_db"):
        self.name = name
        self.storage = StorageEngine()
        self.mvcc = EnhancedMVCCManager(self.storage)
        self.parser = SQLParser()
        self.executor = QueryExecutor(self.storage, self.mvcc)
        self.lock = threading.RLock()
        
        # System tables
        self.system_tables = {
            'tables': ['table_name', 'columns', 'created_at'],
            'transactions': ['txn_id', 'status', 'start_time', 'isolation_level']
        }
        
        print(f"Database '{name}' initialized with MVCC support")
    
    def execute(self, query: str, txn_id: int = None) -> Dict[str, Any]:
        """Execute a SQL query with MVCC support"""
        with self.lock:
            try:
                # Parse the query
                parsed_query = self.parser.parse(query)
                
                # Execute with MVCC
                result = self.executor.execute(parsed_query, txn_id)
                
                return {
                    'success': True,
                    'data': result.get('data', []),
                    'message': result.get('message', 'Query executed successfully'),
                    'columns': result.get('columns', []),
                    'txn_id': result.get('txn_id'),
                    'affected_rows': result.get('affected_rows', 0)
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'data': [],
                    'columns': []
                }
    
    def begin_transaction(self, isolation_level: str = "READ_COMMITTED") -> int:
        """Start a new transaction"""
        return self.mvcc.begin_transaction(isolation_level)
    
    def commit_transaction(self, txn_id: int) -> bool:
        """Commit a transaction"""
        return self.mvcc.commit_transaction(txn_id)
    
    def rollback_transaction(self, txn_id: int) -> bool:
        """Rollback a transaction"""
        return self.mvcc.rollback_transaction(txn_id)
    
    def get_transaction_status(self, txn_id: int) -> Dict[str, Any]:
        """Get transaction status"""
        return self.mvcc.get_transaction_status(txn_id)
    def get_table_info(self):
        """Get information about all tables for API"""
        tables = []
        for table_name in self.storage.get_table_names():
            table_info = self.storage.tables[table_name]
            tables.append({
                'name': table_name,
                'columns': table_info['columns'],
                'primary_key': table_info.get('primary_key'),
                'record_count': len(table_info['records']),
                'created_at': table_info['created_at']
            })
        return tables