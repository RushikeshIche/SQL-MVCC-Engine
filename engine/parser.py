"""
SQL Parser - Parses SQL queries into executable commands
"""

import re
from typing import Dict, Any, List, Tuple
from enum import Enum

class QueryType(Enum):
    CREATE = "CREATE"
    CREATE_INDEX = "CREATE_INDEX"
    SELECT = "SELECT" 
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    DROP = "DROP"  
    BEGIN = "BEGIN"
    COMMIT = "COMMIT"
    ROLLBACK = "ROLLBACK"
    UNKNOWN = "UNKNOWN"

class SQLParser:
    """Simple SQL parser for basic SQL operations"""
    
    def __init__(self):
        self.patterns = {
            QueryType.CREATE: re.compile(r'CREATE TABLE (\w+)\s*\((.*)\)', re.IGNORECASE),
            QueryType.CREATE_INDEX: re.compile(r'CREATE INDEX (\w+) ON (\w+)\s*\((.*?)\)', re.IGNORECASE),
            QueryType.SELECT: re.compile(r'^SELECT\s+(.*)', re.IGNORECASE | re.DOTALL),
            QueryType.INSERT: re.compile(r'INSERT INTO (\w+)\s*\((.*?)\)\s*VALUES\s*\((.*)\)', re.IGNORECASE),
            QueryType.UPDATE: re.compile(r'UPDATE (\w+)\s+SET\s+(.*?)(?:\s+WHERE\s+(.*))?', re.IGNORECASE),
            QueryType.DELETE: re.compile(r'DELETE FROM (\w+)(?:\s+WHERE\s+(.*))?', re.IGNORECASE),
            QueryType.BEGIN: re.compile(r'BEGIN(?:\s+TRANSACTION)?', re.IGNORECASE),
            QueryType.COMMIT: re.compile(r'COMMIT(?:\s+TRANSACTION)?', re.IGNORECASE),
            QueryType.ROLLBACK: re.compile(r'ROLLBACK(?:\s+TRANSACTION)?', re.IGNORECASE),
            # ADD THIS LINE ↓
            QueryType.DROP: re.compile(r'DROP TABLE (\w+)', re.IGNORECASE),
        }
    
    def parse(self, query: str) -> Dict[str, Any]:
        """Parse SQL query and return structured data"""
        query = query.strip().rstrip(';')
        
        for query_type, pattern in self.patterns.items():
            match = pattern.match(query)
            if match:
                return self._parse_query_type(query_type, match, query)
        
        raise ValueError(f"Unsupported or invalid SQL query: {query}")
    
    def _parse_query_type(self, query_type: QueryType, match: re.Match, original_query: str) -> Dict[str, Any]:
        base_result = {
            'type': query_type.value,
            'original_query': original_query
        }
        
        try:
            if query_type == QueryType.CREATE:
                table_name, columns_str = match.groups()
                
                primary_key = None
                pk_match = re.search(r'PRIMARY KEY\s*\((.*?)\)', columns_str, re.IGNORECASE)
                if pk_match:
                    primary_key = pk_match.group(1).strip()
                    columns_str = columns_str[:pk_match.start()] + columns_str[pk_match.end():]

                columns = []
                column_defs = [c.strip() for c in columns_str.split(',') if c.strip()]

                for col_def in column_defs:
                    if 'PRIMARY KEY' in col_def.upper():
                        if primary_key:
                            raise ValueError("Multiple primary keys defined.")
                        parts = col_def.split()
                        column_name = parts[0]
                        primary_key = column_name
                        columns.append(column_name)
                    else:
                        columns.append(col_def.split()[0])

                # Filter out empty strings that might result from splitting
                columns = [c for c in columns if c]

                return {**base_result, 'table_name': table_name, 'columns': columns, 'primary_key': primary_key}
            elif query_type == QueryType.CREATE_INDEX:
                index_name, table_name, column_name = match.groups()
                return {
                    **base_result,
                    'index_name': index_name.strip(),
                    'table_name': table_name.strip(),
                    'column': column_name.strip()
                }
            elif query_type == QueryType.DROP:
                table_name = match.groups()[0]
                return {**base_result, 'table_name': table_name}
            
            elif query_type == QueryType.SELECT:
                rest = match.group(1)
                
                parts = re.split(r'\s+FROM\s+', rest, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) != 2:
                    raise ValueError("Invalid SELECT query: missing FROM clause")
                
                columns_str = parts[0].strip()
                rest_from = parts[1].strip()
                
                result = {
                    **base_result,
                    'columns': [col.strip() for col in columns_str.split(',')],
                    'where': None,
                    'order_by': None,
                    'order_direction': 'ASC',
                    'limit': None,
                    'offset': None
                }
                
                table_match = re.match(r'^(\w+)', rest_from)
                if not table_match:
                    raise ValueError("Invalid SELECT query: missing table name")
                result['table_name'] = table_match.group(1)
                
                remaining = rest_from[table_match.end():].strip()
                
                def extract_clause(keyword, text):
                    pattern = r'\s+' + keyword + r'\s+(.*?)(?=\s+(WHERE|GROUP BY|ORDER BY|LIMIT|OFFSET)|$)'
                    m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                    if m:
                        return m.group(1).strip()
                    return None
                    
                result['where'] = extract_clause('WHERE', ' ' + remaining)
                
                order_by_clause = extract_clause('ORDER BY', ' ' + remaining)
                if order_by_clause:
                    parts = order_by_clause.split()
                    if len(parts) > 1 and parts[-1].upper() in ['ASC', 'DESC']:
                        result['order_direction'] = parts[-1].upper()
                        result['order_by'] = ' '.join(parts[:-1]).strip()
                    else:
                        result['order_by'] = order_by_clause
                        
                limit_clause = extract_clause('LIMIT', ' ' + remaining)
                if limit_clause:
                    result['limit'] = int(limit_clause)
                    
                offset_clause = extract_clause('OFFSET', ' ' + remaining)
                if offset_clause:
                    result['offset'] = int(offset_clause)
                
                return result
            
            elif query_type == QueryType.INSERT:
                table_name, columns_str, values_str = match.groups()
                columns = [col.strip() for col in columns_str.split(',')] if columns_str else []
                values = [val.strip().strip("'") for val in values_str.split(',')]
                return {
                    **base_result,
                    'table_name': table_name,
                    'columns': columns,
                    'values': values
                }
            
            elif query_type == QueryType.UPDATE:
                table_name, set_clause, where_clause = match.groups()
                set_pairs = [pair.strip().split('=') for pair in set_clause.split(',')]
                set_data = {pair[0].strip(): pair[1].strip().strip("'") for pair in set_pairs}
                return {
                    **base_result,
                    'table_name': table_name,
                    'set_data': set_data,
                    'where': where_clause.strip() if where_clause else None
                }
            
            elif query_type == QueryType.DELETE:
                table_name, where_clause = match.groups()
                return {
                    **base_result,
                    'table_name': table_name,
                    'where': where_clause.strip() if where_clause else None
                }
            
            elif query_type in [QueryType.BEGIN, QueryType.COMMIT, QueryType.ROLLBACK]:
                return base_result
                
        except Exception as e:
            raise ValueError(f"Error parsing {query_type.value} query: {str(e)}")
        
        return base_result