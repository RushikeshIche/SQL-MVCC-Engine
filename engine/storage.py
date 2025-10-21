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
    
    def create_table(self, table_name: str, columns: List[str], primary_key: str = None):
        """Create a new table"""
        if self.table_exists(table_name):
            raise ValueError(f"Table {table_name} already exists")
        
        self.tables[table_name] = {
            'columns': columns,
            'primary_key': primary_key,
            'records': {},
            'created_at': datetime.now().isoformat()
        }
        self.next_ids[table_name] = 0
        self._save_data()
    
    def get_table_names(self) -> List[str]:
        """Get all table names"""
        return list(self.tables.keys())
    
    def get_next_id(self, table_name: str) -> int:
        # ensure counter exists
        self.next_ids.setdefault(table_name, 0)
        self.next_ids[table_name] += 1
        print(f"[DEBUG] get_next_id -> table: {table_name}, new_id: {self.next_ids[table_name]}", flush=True)
        self._save_data()
        return self.next_ids[table_name]

    
    # def insert_record(self, table_name: str, record: Dict[str, Any]):
    #     """Insert a record into a table"""
    #     if not self.table_exists(table_name):
    #         raise ValueError(f"Table {table_name} does not exist")
        
    #     record_id = record.get('id', self.get_next_id(table_name))
    #     record['id'] = record_id
        
    #     self.tables[table_name]['records'][record_id] = record.copy()
    #     self._save_data()

    def insert_record(self, table_name: str, record: Dict[str, Any]):
        
        if not self.table_exists(table_name):
            raise ValueError(f"Table {table_name} does not exist")

        table_info = self.tables[table_name]
        primary_key = table_info.get('primary_key')

        if primary_key and primary_key in record:
            pk_value = record[primary_key]
            # Ensure pk_value is of a comparable type, converting if necessary
            try:
                if primary_key == 'id':
                    pk_value = int(pk_value)
            except (ValueError, TypeError):
                pass # Keep as string if conversion fails

            for existing_record in table_info['records'].values():
                existing_pk_value = existing_record.get(primary_key)
                
                # Attempt to make types consistent for comparison
                try:
                    if primary_key == 'id':
                        existing_pk_value = int(existing_pk_value)
                except (ValueError, TypeError):
                    pass

                if existing_pk_value == pk_value:
                    raise ValueError(f"Primary key constraint violation: value '{pk_value}' already exists for column '{primary_key}'")

        # The record_id for storage is the 'id' field from the record.
        record_id = record.get('id')
        if record_id is None:
            # This case should ideally not be hit if executor always provides an ID.
            record_id = self.get_next_id(table_name)
            record['id'] = record_id
        
        # Ensure record_id is an integer for dictionary key consistency
        record_id = int(record_id)

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
        
        table_info = self.tables[table_name]
        primary_key = table_info.get('primary_key')
        if primary_key and primary_key in record:
            pk_value = record[primary_key]
            for rid, existing_record in table_info['records'].items():
                if rid != record_id and existing_record.get(primary_key) == pk_value:
                    raise ValueError(f"Primary key constraint violation: value '{pk_value}' already exists for column '{primary_key}'")

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
    
    def record_exists(self, table_name: str, record_id: int) -> bool:
        """Check if a record with a given ID exists."""
        if not self.table_exists(table_name):
            return False
        return record_id in self.tables[table_name]['records']

