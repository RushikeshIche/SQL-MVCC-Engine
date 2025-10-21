"""
Storage Engine - Handles data persistence
"""

import os
import json
import pickle
from typing import Dict, Any, List
from datetime import datetime

class StorageEngine:
    """Simple storage engine for table data"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.tables = {}
        self.next_ids = {}
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load existing table data from disk"""
        try:
            data_file = os.path.join(self.data_dir, "database.pkl")
            if os.path.exists(data_file):
                with open(data_file, 'rb') as f:
                    data = pickle.load(f)
                    self.tables = data.get('tables', {})
                    self.next_ids = data.get('next_ids', {})
        except Exception as e:
            print(f"Warning: Could not load existing data: {e}")
            self.tables = {}
            self.next_ids = {}
    
    def _save_data(self):
        """Save table data to disk"""
        try:
            data_file = os.path.join(self.data_dir, "database.pkl")
            with open(data_file, 'wb') as f:
                pickle.dump({
                    'tables': self.tables,
                    'next_ids': self.next_ids
                }, f)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        return table_name in self.tables
    
    def create_table(self, table_name: str, columns: List[str]):
        """Create a new table"""
        if self.table_exists(table_name):
            raise ValueError(f"Table {table_name} already exists")
        
        self.tables[table_name] = {
            'columns': columns,
            'records': {},
            'created_at': datetime.now().isoformat()
        }
        self.next_ids[table_name] = 1
        self._save_data()
    
    def get_table_names(self) -> List[str]:
        """Get all table names"""
        return list(self.tables.keys())
    
    def get_next_id(self, table_name: str) -> int:
        """Get next available ID for a table"""
        if table_name not in self.next_ids:
            self.next_ids[table_name] = 1
        else:
            self.next_ids[table_name] += 1
        return self.next_ids[table_name]
    
    def insert_record(self, table_name: str, record: Dict[str, Any]):
        """Insert a record into a table"""
        if not self.table_exists(table_name):
            raise ValueError(f"Table {table_name} does not exist")
        
        record_id = record.get('id', self.get_next_id(table_name))
        record['id'] = record_id
        
        self.tables[table_name]['records'][record_id] = record.copy()
        self._save_data()
    
    def get_all_records(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all records from a table"""
        if not self.table_exists(table_name):
            return []
        
        return list(self.tables[table_name]['records'].values())
    
    def update_record(self, table_name: str, record_id: int, record: Dict[str, Any]):
        """Update a record in a table"""
        if not self.table_exists(table_name):
            raise ValueError(f"Table {table_name} does not exist")
        
        if record_id not in self.tables[table_name]['records']:
            raise ValueError(f"Record {record_id} not found in table {table_name}")
        
        self.tables[table_name]['records'][record_id] = record.copy()
        self._save_data()
    
    def delete_record(self, table_name: str, record_id: int):
        """Delete a record from a table"""
        if not self.table_exists(table_name):
            raise ValueError(f"Table {table_name} does not exist")
        
        if record_id in self.tables[table_name]['records']:
            del self.tables[table_name]['records'][record_id]
            self._save_data()
    def drop_table(self, table_name: str):
        """Drop a table and all its data"""
        if not self.table_exists(table_name):
            raise ValueError(f"Table {table_name} does not exist")
        
        # Remove the table and its next_id counter
        del self.tables[table_name]
        if table_name in self.next_ids:
            del self.next_ids[table_name]
        
        self._save_data()
        return True