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
        elif query_type == "CREATE_INDEX":
            return self._execute_create_index(parsed_query)
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
        primary_key = parsed_query.get('primary_key')
        
        self.storage.create_table(table_name, columns, primary_key)
        return {'message': f'Table {table_name} created successfully'}
        
    def _execute_create_index(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute CREATE INDEX query"""
        table_name = parsed_query['table_name']
        column = parsed_query['column']
        index_name = parsed_query['index_name']
        
        try:
            self.storage.create_index(table_name, column)
            return {'message': f'Index {index_name} created successfully on {table_name}({column})'}
        except Exception as e:
            raise ValueError(f"Error creating index: {str(e)}")
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
        
        # Get table info to retrieve column names even if table is empty
        if not self.storage.table_exists(table_name):
            raise ValueError(f"Table {table_name} does not exist")
        
        table_info = self.storage.tables[table_name]
        table_columns = table_info.get('columns', [])
        
        # Get records, optimizing with index if possible
        records = self._get_optimized_records(table_name, txn_id, where_clause)
        
        # Apply WHERE clause filtering for conditions not covered by index
        if where_clause:
            records = self._apply_where_clause(records, where_clause)
            
        # Apply Aggregations (GROUP BY, COUNT, SUM, etc.)
        group_by = parsed_query.get('group_by')
        has_agg = any('(' in col and ')' in col for col in columns)
        if group_by or has_agg:
            records = self._apply_aggregations(records, columns, group_by)
            
        # Apply ORDER BY
        order_by = parsed_query.get('order_by')
        if order_by:
            direction = parsed_query.get('order_direction', 'ASC')
            reverse = direction.upper() == 'DESC'
            
            def sort_key(record):
                val = record.get(order_by)
                if val is None:
                    return (0, "")
                try:
                    return (1, float(val))
                except (ValueError, TypeError):
                    return (2, str(val))
                    
            records.sort(key=sort_key, reverse=reverse)
            
        # Apply OFFSET
        offset = parsed_query.get('offset')
        if offset is not None:
            records = records[offset:]
            
        # Apply LIMIT
        limit = parsed_query.get('limit')
        if limit is not None:
            records = records[:limit]
        
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
                # Return table column names even when no records exist
                return {'data': [], 'columns': table_columns, 'affected_rows': 0}
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
        
        # Get table info to check primary key
        if not self.storage.table_exists(table_name):
            raise ValueError(f"Table {table_name} does not exist")
        
        table_info = self.storage.tables[table_name]
        primary_key = table_info.get('primary_key')
        
        # Create record with MVCC metadata
        record = dict(zip(columns, values))

        # If 'id' is not provided in the query, generate one.
        if 'id' not in record:
            record['id'] = self.storage.get_next_id(table_name)
        else:
            # If id is provided, ensure it's an integer and doesn't already exist.
            try:
                provided_id = int(record['id'])
                if self.storage.record_exists(table_name, provided_id):
                    raise ValueError(f"Primary key constraint violation: ID '{provided_id}' already exists in table '{table_name}'")
                record['id'] = provided_id
            except (ValueError, TypeError):
                raise ValueError("ID must be an integer.")
        
        # Add MVCC metadata
        record['_mvcc_created_txn'] = txn_id or 0
        record['_mvcc_created_ts'] = datetime.now().isoformat()
        record['_mvcc_deleted_txn'] = None
        
        # The storage.insert_record will check primary key uniqueness for any primary key column
        self.storage.insert_record(table_name, record)
        return {'message': 'Record inserted successfully', 'affected_rows': 1}
    
    def _execute_update(self, parsed_query: Dict[str, Any], txn_id: int) -> Dict[str, Any]:
        """Execute UPDATE query with MVCC"""
        table_name = parsed_query['table_name']
        set_data = parsed_query['set_data']
        where_clause = parsed_query.get('where')
        
        # Get table info to check primary key
        table_info = self.storage.tables[table_name]
        primary_key = table_info.get('primary_key')
        
        records = self._get_optimized_records(table_name, txn_id, where_clause)
        
        if where_clause:
            records = self._apply_where_clause(records, where_clause)
        
        # Check if updating primary key would violate uniqueness constraint
        if primary_key and primary_key in set_data:
            new_pk_value = set_data[primary_key]
            all_records = self.mvcc.get_visible_records(table_name, txn_id)
            
            for existing_record in all_records:
                # Skip records that we're about to update
                if existing_record in records:
                    continue
                    
                existing_pk_value = existing_record.get(primary_key)
                
                # Compare values
                try:
                    if str(new_pk_value).replace('.', '').replace('-', '').isdigit():
                        new_pk_cmp = float(new_pk_value) if '.' in str(new_pk_value) else int(new_pk_value)
                        existing_pk_cmp = float(existing_pk_value) if '.' in str(existing_pk_value) else int(existing_pk_value)
                        if new_pk_cmp == existing_pk_cmp:
                            raise ValueError(f"Primary key constraint violation: {primary_key}='{new_pk_value}' already exists in table '{table_name}'")
                    else:
                        if str(new_pk_value) == str(existing_pk_value):
                            raise ValueError(f"Primary key constraint violation: {primary_key}='{new_pk_value}' already exists in table '{table_name}'")
                except (ValueError, TypeError) as e:
                    if "Primary key constraint violation" in str(e):
                        raise
                    if str(new_pk_value) == str(existing_pk_value):
                        raise ValueError(f"Primary key constraint violation: {primary_key}='{new_pk_value}' already exists in table '{table_name}'")
        
        updated_count = 0
        for record in records:
            # For MVCC, we create a new version instead of updating in place
            new_record = record.copy()
            for key, value in set_data.items():
                new_record[key] = value

            new_record.pop('id', None)

            self.storage.insert_record(table_name, new_record)
            updated_count += 1
        
        return {'message': f'{updated_count} record(s) updated', 'affected_rows': updated_count}
    
    def _execute_delete(self, parsed_query: Dict[str, Any], txn_id: int) -> Dict[str, Any]:
        """Execute DELETE query with MVCC"""
        table_name = parsed_query['table_name']
        where_clause = parsed_query.get('where')
        
        records = self._get_optimized_records(table_name, txn_id, where_clause)
        
        if where_clause:
            records = self._apply_where_clause(records, where_clause)
        
        deleted_count = 0
        for record in records:
            # Mark record as deleted using MVCC
            record['_mvcc_deleted_txn'] = txn_id or 0
            self.storage.update_record(table_name, record['id'], record)
            deleted_count += 1
        
        return {'message': f'{deleted_count} record(s) deleted', 'affected_rows': deleted_count}
    
    def _get_optimized_records(self, table_name: str, txn_id: int, where_clause: str) -> List[Dict]:
        """Fetch records, using B-Tree index if applicable for basic equality filters."""
        if not where_clause:
            return self.mvcc.get_visible_records(table_name, txn_id)
            
        # Basic parsing to see if we can use an index
        if ' AND ' not in where_clause.upper() and ' OR ' not in where_clause.upper():
            if '=' in where_clause and '!=' not in where_clause and '>=' not in where_clause and '<=' not in where_clause:
                parts = where_clause.split('=')
                if len(parts) == 2:
                    col = parts[0].strip()
                    val = parts[1].strip().strip("'")
                    
                    if table_name in self.storage.indexes and col in self.storage.indexes[table_name]:
                        print(f"[DEBUG] Using BTree index for {table_name}.{col}={val}")
                        btree = self.storage.indexes[table_name][col]
                        
                        try:
                            val_typed = float(val) if '.' in val else int(val)
                        except:
                            val_typed = val
                            
                        record_ids = btree.search(val_typed)
                        if not record_ids:
                            record_ids = btree.search(str(val))
                            
                        if record_ids is not None:
                            raw_records = []
                            for rid in record_ids:
                                rec = self.storage.get_record(table_name, rid)
                                if rec:
                                    raw_records.append(rec)
                                    
                            # Check visibility
                            txn = self.mvcc.transactions.get(txn_id) if txn_id else None
                            # Use string comparison if IsolationLevel enum isn't directly comparable
                            iso_str = str(txn['isolation_level']) if txn else "READ_COMMITTED"
                            
                            if "REPEATABLE_READ" in iso_str or "SERIALIZABLE" in iso_str:
                                # Safe fallback for snapshot isolation
                                return self.mvcc.get_visible_records(table_name, txn_id)
                                
                            visible_records = []
                            for rec in raw_records:
                                if "READ_UNCOMMITTED" in iso_str:
                                    if rec.get('_mvcc_deleted_txn') != txn_id:
                                        visible_records.append(rec)
                                else:
                                    if self.mvcc._is_record_visible(rec, txn_id):
                                        visible_records.append(rec)
                            return visible_records
                            
        return self.mvcc.get_visible_records(table_name, txn_id)

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
            
    def _apply_aggregations(self, records: List[Dict], columns: List[str], group_by: str) -> List[Dict]:
        """Apply GROUP BY and aggregate functions"""
        buckets = {}
        if group_by:
            for rec in records:
                key = rec.get(group_by)
                if key not in buckets:
                    buckets[key] = []
                buckets[key].append(rec)
        else:
            buckets['__all__'] = records
            
        result = []
        for key, group in buckets.items():
            agg_row = {}
            if group_by:
                agg_row[group_by] = key
                
            for col in columns:
                if col == group_by or col == '*':
                    continue
                if '(' in col and ')' in col:
                    func_name = col[:col.index('(')].strip().upper()
                    arg = col[col.index('(')+1:col.index(')')].strip()
                    
                    if func_name == 'COUNT':
                        agg_row[col] = len(group)
                    elif func_name == 'SUM':
                        try:
                            agg_row[col] = sum([float(r.get(arg, 0)) for r in group if r.get(arg) is not None])
                        except ValueError:
                            agg_row[col] = 0
                    elif func_name == 'AVG':
                        try:
                            vals = [float(r.get(arg, 0)) for r in group if r.get(arg) is not None]
                            agg_row[col] = sum(vals) / len(vals) if vals else 0
                        except ValueError:
                            agg_row[col] = 0
                    elif func_name == 'MIN':
                        try:
                            vals = [float(r.get(arg, 0)) for r in group if r.get(arg) is not None]
                            agg_row[col] = min(vals) if vals else None
                        except ValueError:
                            agg_row[col] = None
                    elif func_name == 'MAX':
                        try:
                            vals = [float(r.get(arg, 0)) for r in group if r.get(arg) is not None]
                            agg_row[col] = max(vals) if vals else None
                        except ValueError:
                            agg_row[col] = None
                    else:
                        agg_row[col] = None 
                else:
                    if group:
                        agg_row[col] = group[0].get(col)
                        
            result.append(agg_row)
            
        return result