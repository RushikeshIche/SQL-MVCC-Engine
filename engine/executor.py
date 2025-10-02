"""
Query Executor - Executes parsed queries with MVCC
"""

from typing import Dict, Any, List
from datetime import datetime
import re

class QueryExecutor:
    """Executes SQL queries with MVCC support"""
    
    def __init__(self, storage, mvcc_manager):
        self.storage = storage
        self.mvcc = mvcc_manager
    
    def execute(self, parsed_query: Dict[str, Any], txn_id: int = None) -> Dict[str, Any]:
        """Execute a parsed query"""
        query_type = parsed_query['type']
        
        if query_type == "CREATE":
            return self._execute_create(parsed_query)
        elif query_type == "SELECT":
            return self._execute_select(parsed_query, txn_id)
        elif query_type == "INSERT":
            return self._execute_insert(parsed_query, txn_id)
        elif query_type == "UPDATE":
            return self._execute_update(parsed_query, txn_id)
        elif query_type == "DELETE":
            return self._execute_delete(parsed_query, txn_id)
        elif query_type == "DROP":
            return self._execute_drop(parsed_query)
        elif query_type == "BEGIN":
            new_txn_id = self.mvcc.begin_transaction()
            return {'message': f'Transaction {new_txn_id} started', 'txn_id': new_txn_id}
        elif query_type == "COMMIT":
            if txn_id:
                success = self.mvcc.commit_transaction(txn_id)
                return {'message': f'Transaction {txn_id} committed', 'success': success}
            else:
                return {'message': 'No active transaction', 'success': False}
        elif query_type == "ROLLBACK":
            if txn_id:
                success = self.mvcc.rollback_transaction(txn_id)
                return {'message': f'Transaction {txn_id} rolled back', 'success': success}
            else:
                return {'message': 'No active transaction', 'success': False}
        else:
            raise ValueError(f"Unsupported query type: {query_type}")
    
    def _execute_create(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute CREATE TABLE query"""
        table_name = parsed_query['table_name']
        columns = parsed_query['columns']
        
        self.storage.create_table(table_name, columns)
        return {'message': f'Table {table_name} created successfully'}
    def _execute_drop(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute DROP TABLE query"""
        table_name = parsed_query['table_name']
        
        if not self.storage.table_exists(table_name):
            raise ValueError(f"Table {table_name} does not exist")
        
        # Remove the table from storage
        self.storage.drop_table(table_name)
        
        return {'message': f'Table {table_name} dropped successfully'}
    
    def _execute_select(self, parsed_query: Dict[str, Any], txn_id: int) -> Dict[str, Any]:
        """Execute SELECT query with MVCC"""
        table_name = parsed_query['table_name']
        columns = parsed_query['columns']
        where_clause = parsed_query.get('where')
        
        # Get visible records based on MVCC
        records = self.mvcc.get_visible_records(table_name, txn_id)
        
        # Apply WHERE clause filtering
        if where_clause:
            records = self._apply_where_clause(records, where_clause)
        
        # Select specific columns
        if columns[0] == '*':
            if records:
                all_columns = list(records[0].keys())
                # Remove MVCC internal fields for display
                display_columns = [col for col in all_columns if not col.startswith('_mvcc_')]
                result_data = [{col: record.get(col) for col in display_columns} for record in records]
                return {
                    'data': result_data,
                    'columns': display_columns,
                    'affected_rows': len(result_data)
                }
            else:
                return {'data': [], 'columns': [], 'affected_rows': 0}
        else:
            result_data = [{col: record.get(col) for col in columns} for record in records]
            return {
                'data': result_data,
                'columns': columns,
                'affected_rows': len(result_data)
            }
    
    def _execute_insert(self, parsed_query: Dict[str, Any], txn_id: int) -> Dict[str, Any]:
        """Execute INSERT query with MVCC"""
        table_name = parsed_query['table_name']
        columns = parsed_query['columns']
        values = parsed_query['values']
        
        # Create record with MVCC metadata
        record = dict(zip(columns, values))
        record_id = self.storage.get_next_id(table_name)
        record['id'] = record_id
        
        # Add MVCC metadata
        record['_mvcc_created_txn'] = txn_id or 0
        record['_mvcc_created_ts'] = datetime.now().isoformat()
        record['_mvcc_deleted_txn'] = None
        
        self.storage.insert_record(table_name, record)
        return {'message': 'Record inserted successfully', 'affected_rows': 1}
    
    def _execute_update(self, parsed_query: Dict[str, Any], txn_id: int) -> Dict[str, Any]:
        """Execute UPDATE query with MVCC"""
        table_name = parsed_query['table_name']
        set_data = parsed_query['set_data']
        where_clause = parsed_query.get('where')
        
        records = self.mvcc.get_visible_records(table_name, txn_id)
        
        if where_clause:
            records = self._apply_where_clause(records, where_clause)
        
        updated_count = 0
        for record in records:
            # For MVCC, we create a new version instead of updating in place
            new_record = record.copy()
            for key, value in set_data.items():
                new_record[key] = value
            
            # Update MVCC metadata
            new_record['_mvcc_created_txn'] = txn_id or 0
            new_record['_mvcc_created_ts'] = datetime.now().isoformat()
            
            self.storage.insert_record(table_name, new_record)
            updated_count += 1
        
        return {'message': f'{updated_count} record(s) updated', 'affected_rows': updated_count}
    
    def _execute_delete(self, parsed_query: Dict[str, Any], txn_id: int) -> Dict[str, Any]:
        """Execute DELETE query with MVCC"""
        table_name = parsed_query['table_name']
        where_clause = parsed_query.get('where')
        
        records = self.mvcc.get_visible_records(table_name, txn_id)
        
        if where_clause:
            records = self._apply_where_clause(records, where_clause)
        
        deleted_count = 0
        for record in records:
            # Mark record as deleted using MVCC
            record['_mvcc_deleted_txn'] = txn_id or 0
            self.storage.update_record(table_name, record['id'], record)
            deleted_count += 1
        
        return {'message': f'{deleted_count} record(s) deleted', 'affected_rows': deleted_count}
    
    def _apply_where_clause(self, records: List[Dict], where_clause: str) -> List[Dict]:
        """Apply WHERE clause filtering to records"""
        if not where_clause:
            return records
        
        def evaluate_condition(record, condition):
            # Simple condition evaluator for basic comparisons
            operators = ['=', '!=', '>', '<', '>=', '<=']
            for op in operators:
                if op in condition:
                    left, right = condition.split(op, 1)
                    left = left.strip()
                    right = right.strip().strip("'")
                    
                    left_val = record.get(left, '')
                    right_val = right
                    
                    # Try to convert to numbers if possible
                    try:
                        left_val = float(left_val) if '.' in str(left_val) else int(left_val)
                        right_val = float(right_val) if '.' in right_val else int(right_val)
                    except (ValueError, TypeError):
                        pass
                    
                    if op == '=':
                        return str(left_val) == str(right_val)
                    elif op == '!=':
                        return str(left_val) != str(right_val)
                    elif op == '>':
                        return left_val > right_val
                    elif op == '<':
                        return left_val < right_val
                    elif op == '>=':
                        return left_val >= right_val
                    elif op == '<=':
                        return left_val <= right_val
            
            return False
        
        # Handle AND conditions
        if ' AND ' in where_clause.upper():
            conditions = [cond.strip() for cond in where_clause.upper().split(' AND ')]
            return [record for record in records if all(evaluate_condition(record, cond) for cond in conditions)]
        
        # Handle OR conditions
        elif ' OR ' in where_clause.upper():
            conditions = [cond.strip() for cond in where_clause.upper().split(' OR ')]
            return [record for record in records if any(evaluate_condition(record, cond) for cond in conditions)]
        
        # Single condition
        else:
            return [record for record in records if evaluate_condition(record, where_clause)]