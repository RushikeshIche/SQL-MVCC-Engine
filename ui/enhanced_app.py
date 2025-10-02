"""
Enhanced Streamlit UI with additional features
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from engine.database import Database
from engine.mvcc_enhanced import EnhancedMVCCManager, IsolationLevel
from utils.helpers import format_timestamp, format_query_result

class EnhancedSQLApp:
    """Enhanced SQL MVCC Engine UI"""
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize session state"""
        if 'db' not in st.session_state:
            st.session_state.db = Database("MVCC_Enhanced")
            # Replace with enhanced MVCC manager
            st.session_state.db.mvcc = EnhancedMVCCManager(st.session_state.db.storage)
        
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        
        if 'active_transaction' not in st.session_state:
            st.session_state.active_transaction = None
        
        if 'show_advanced' not in st.session_state:
            st.session_state.show_advanced = False
        
        if 'isolation_level' not in st.session_state:
            st.session_state.isolation_level = "READ_COMMITTED"
    
    def setup_sidebar(self):
        """Setup the sidebar with controls"""
        with st.sidebar:
            st.title("MVCC Controls")
            
            # Transaction Management
            self.setup_transaction_controls()
            
            # Isolation Level Selection
            self.setup_isolation_controls()
            
            # Database Operations
            self.setup_database_controls()
            
            # MVCC Monitoring
            self.setup_monitoring_controls()
    
    def setup_transaction_controls(self):
        """Setup transaction controls"""
        st.header("Transaction Management")
        
        isolation_level = st.session_state.isolation_level
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("BEGIN TXN", use_container_width=True, 
                        help=f"Start transaction with {isolation_level} isolation"):
                txn_id = st.session_state.db.begin_transaction(isolation_level)
                st.session_state.active_transaction = txn_id
                st.success(f"TXN {txn_id} started!")
                st.rerun()
        
        with col2:
            if st.button("Status", use_container_width=True,
                        disabled=not st.session_state.active_transaction):
                if st.session_state.active_transaction:
                    status = st.session_state.db.mvcc.get_transaction_info(
                        st.session_state.active_transaction
                    )
                    st.json(status)
        
        col3, col4 = st.columns(2)
        
        with col3:
            if st.button("COMMIT", use_container_width=True,
                        disabled=not st.session_state.active_transaction):
                result = st.session_state.db.commit_transaction(st.session_state.active_transaction)
                if result:
                    st.success(f"TXN {st.session_state.active_transaction} committed!")
                    st.session_state.active_transaction = None
                else:
                    st.error("Commit failed!")
                st.rerun()
        
        with col4:
            if st.button("ROLLBACK", use_container_width=True,
                        disabled=not st.session_state.active_transaction):
                result = st.session_state.db.rollback_transaction(st.session_state.active_transaction)
                if result:
                    st.success(f"TXN {st.session_state.active_transaction} rolled back!")
                    st.session_state.active_transaction = None
                else:
                    st.error("Rollback failed!")
                st.rerun()
        
        # Transaction status display
        self.display_transaction_status()
    
    def setup_isolation_controls(self):
        """Setup isolation level controls"""
        st.header("Isolation Level")
        
        isolation_levels = {
            "READ UNCOMMITTED": "READ_UNCOMMITTED",
            "READ COMMITTED": "READ_COMMITTED", 
            "REPEATABLE READ": "REPEATABLE_READ",
            "SERIALIZABLE": "SERIALIZABLE"
        }
        
        selected = st.selectbox(
            "Choose Isolation Level:",
            options=list(isolation_levels.keys()),
            index=1,  # READ COMMITTED as default
            help="Select the transaction isolation level"
        )
        
        st.session_state.isolation_level = isolation_levels[selected]
        
        # Isolation level explanations
        with st.expander("Isolation Level Info"):
            st.markdown("""
            **READ UNCOMMITTED:** 
            - Can see uncommitted changes from other transactions
            - Lowest isolation, highest concurrency
            
            **READ COMMITTED:**
            - Can only see committed changes
            - Default in most databases
            
            **REPEATABLE READ:**
            - Sees snapshot at transaction start
            - Prevents non-repeatable reads
            
            **SERIALIZABLE:**
            - Strictest isolation
            - Prevents phantom reads
            """)
    
    def setup_database_controls(self):
        """Setup database controls"""
        st.header("Database Operations")
        
        if st.button("Refresh Schema", use_container_width=True):
            st.rerun()
        
        if st.button("Clear History", use_container_width=True):
            st.session_state.query_history = []
            st.success("History cleared!")
            st.rerun()
        
        if st.button("DB Status", use_container_width=True):
            status = st.session_state.db.mvcc.get_database_status()
            st.json(status)
    
    def setup_monitoring_controls(self):
        """Setup monitoring controls"""
        st.header("Monitoring")
        
        st.session_state.show_advanced = st.checkbox(
            "Show Advanced MVCC Info", 
            value=st.session_state.show_advanced
        )
        
        if st.button("System Tables", use_container_width=True):
            self.show_system_tables()
    
    def display_transaction_status(self):
        """Display current transaction status"""
        st.divider()
        
        if st.session_state.active_transaction:
            txn_info = st.session_state.db.mvcc.get_transaction_info(
                st.session_state.active_transaction
            )
            
            st.markdown(f"""
            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 10px; border-left: 5px solid #4CAF50;">
                <h4 style="margin: 0; color: #2E7D32;">Active Transaction</h4>
                <p style="margin: 5px 0;"><strong>ID:</strong> {txn_info['txn_id']}</p>
                <p style="margin: 5px 0;"><strong>Isolation:</strong> {txn_info['isolation_level'].value}</p>
                <p style="margin: 5px 0;"><strong>Started:</strong> {format_timestamp(txn_info['start_time'])}</p>
                <p style="margin: 5px 0;"><strong>Duration:</strong> {txn_info['active_time']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background-color: #ffebee; padding: 15px; border-radius: 10px; border-left: 5px solid #f44336;">
                <h4 style="margin: 0; color: #c62828;">No Active Transaction</h4>
                <p style="margin: 5px 0;">Start a transaction to enable MVCC features</p>
            </div>
            """, unsafe_allow_html=True)
    
    def show_system_tables(self):
        """Show system tables information"""
        try:
            # Get transactions table
            txn_records = st.session_state.db.storage.get_all_records('mvcc_transactions')
            if txn_records:
                st.subheader("System: MVCC Transactions")
                txn_df = pd.DataFrame(txn_records)
                st.dataframe(txn_df, use_container_width=True)
        except:
            pass
    
    def setup_main_content(self):
        """Setup the main content area"""
        st.title("SQL MVCC Engine")
        st.markdown("**Multi-Version Concurrency Control Database Management System**")
        
        # Create tabs for different functionalities
        tab1, tab2, tab3, tab4 = st.tabs([
            "Query Editor", 
            "Schema Explorer", 
            "Query History", 
            "MVCC Analytics"
        ])
        
        with tab1:
            self.setup_query_editor()
        
        with tab2:
            self.setup_schema_explorer()
        
        with tab3:
            self.setup_query_history()
        
        with tab4:
            self.setup_analytics()
    
    def setup_query_editor(self):
        """Setup the query editor tab"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("SQL Query Editor")
            
            # Query input with syntax highlighting
            query = st.text_area(
                "Enter SQL Query:",
                height=200,
                value=st.session_state.get('last_query', ''),
                placeholder="""Enter your SQL query here...
Examples:
CREATE TABLE users (id INT, name VARCHAR, email VARCHAR, age INT);
INSERT INTO users (id, name, email, age) VALUES (1, 'Alice', 'alice@email.com', 30);
SELECT * FROM users;
BEGIN TRANSACTION;
UPDATE users SET age = 31 WHERE name = 'Alice';
COMMIT;""",
                key="query_editor"
            )
            
            # Quick action buttons
            col1a, col1b, col1c, col1d = st.columns(4)
            
            with col1a:
                execute_btn = st.button("Execute", use_container_width=True)
            with col1b:
                explain_btn = st.button("Explain", use_container_width=True)
            with col1c:
                format_btn = st.button("Format", use_container_width=True)
            with col1d:
                clear_btn = st.button("Clear", use_container_width=True)
            
            if format_btn and query:
                # Simple formatting
                formatted_query = self.format_sql_query(query)
                st.session_state.last_query = formatted_query
                st.rerun()
            
            if clear_btn:
                st.session_state.last_query = ""
                st.rerun()
            
            if execute_btn and query:
                self.execute_query(query)
            
            if explain_btn and query:
                self.explain_query(query)
        
        with col2:
            st.subheader("Quick Queries")
            self.setup_quick_queries()
    
    def setup_quick_queries(self):
        """Setup quick query templates"""
        templates = {
            "Create Users Table": "CREATE TABLE users (id INT, name VARCHAR, email VARCHAR, age INT)",
            "Create Products Table": "CREATE TABLE products (id INT, name VARCHAR, price DECIMAL, category VARCHAR)",
            "Insert Sample Data": "INSERT INTO users (id, name, email, age) VALUES (1, 'Alice', 'alice@email.com', 30), (2, 'Bob', 'bob@email.com', 25)",
            "Select with WHERE": "SELECT * FROM users WHERE age > 25",
            "Begin Transaction": "BEGIN TRANSACTION",
            "Complex Join": "SELECT u.name, p.name as product_name FROM users u, products p WHERE u.id = p.user_id",
            "Update with Condition": "UPDATE users SET age = age + 1 WHERE age < 30",
            "Delete with Condition": "DELETE FROM users WHERE age > 100"
        }
        
        for name, template in templates.items():
            if st.button(name, use_container_width=True, key=f"template_{name}"):
                st.session_state.last_query = template
                st.rerun()
    
    def format_sql_query(self, query: str) -> str:
        """Simple SQL formatting"""
        # Basic formatting - can be enhanced with sqlparse library
        formatted = query.upper()
        
        # Add newlines after keywords
        keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'TABLE', 'VALUES']
        for keyword in keywords:
            formatted = formatted.replace(keyword, f'\n{keyword}')
        
        return formatted.strip()
    
    def execute_query(self, query: str):
        """Execute SQL query"""
        with st.spinner("Executing query..."):
            try:
                start_time = datetime.now()
                
                # Execute with active transaction if exists
                txn_id = st.session_state.active_transaction
                result = st.session_state.db.execute(query, txn_id)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Add to history
                history_entry = {
                    'timestamp': start_time.isoformat(),
                    'query': query,
                    'success': result['success'],
                    'message': result.get('message', '') or result.get('error', ''),
                    'execution_time': execution_time,
                    'transaction': txn_id,
                    'affected_rows': result.get('affected_rows', 0)
                }
                
                st.session_state.query_history.insert(0, history_entry)
                
                # Display results
                self.display_query_result(result, execution_time)
                
            except Exception as e:
                st.error(f"❌ Execution error: {str(e)}")
    
    def display_query_result(self, result: dict, execution_time: float):
        """Display query execution results"""
        if result['success']:
            st.success(f"✅ {result['message']}")
            
            # Show execution info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Execution Time", f"{execution_time:.3f}s")
            with col2:
                st.metric("Affected Rows", result.get('affected_rows', 0))
            with col3:
                st.metric("Transaction", result.get('txn_id', 'None'))
            
            # Show data if available
            if result['data']:
                st.subheader("Query Results")
                df = pd.DataFrame(result['data'])
                st.dataframe(df, use_container_width=True)
                
                # Show quick statistics for numeric columns
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    with st.expander("Quick Stats"):
                        st.write(df[numeric_cols].describe())
            
            # Show MVCC details if enabled
            if st.session_state.show_advanced:
                with st.expander("MVCC Details"):
                    st.json(result)
        
        else:
            st.error(f"❌ {result.get('error', 'Unknown error')}")
    
    def explain_query(self, query: str):
        """Explain query execution plan"""
        st.info("Query Explanation")
        
        try:
            # Simple explanation based on query type
            if query.upper().startswith('SELECT'):
                st.markdown("""
                **Execution Plan:**
                - Parse SELECT query
                - Apply MVCC visibility rules
                - Filter records based on WHERE clause
                - Project selected columns
                - Return results
                """)
            elif query.upper().startswith('INSERT'):
                st.markdown("""
                **Execution Plan:**
                - Parse INSERT query  
                - Validate table existence
                - Create new record with MVCC metadata
                - Store record in version chain
                - Return success message
                """)
            elif query.upper().startswith('UPDATE'):
                st.markdown("""
                **Execution Plan:**
                - Parse UPDATE query
                - Find visible records using MVCC
                - Create new versions for updated records
                - Update MVCC metadata
                - Return affected rows count
                """)
            elif query.upper().startswith('CREATE'):
                st.markdown("""
                **Execution Plan:**
                - Parse CREATE TABLE query
                - Validate table doesn't exist
                - Create table schema
                - Initialize storage structures
                - Return success message
                """)
        except:
            st.warning("Could not generate explanation for this query type")
    
    def setup_schema_explorer(self):
        """Setup schema explorer tab"""
        st.subheader("Database Schema Explorer")
        
        tables = st.session_state.db.storage.get_table_names()
        
        if not tables:
            st.info("No tables in database. Create a table to get started!")
            return
        
        # Table selection
        selected_table = st.selectbox("Select Table:", tables)
        
        if selected_table:
            self.display_table_info(selected_table)
    
    def display_table_info(self, table_name: str):
        """Display detailed table information"""
        table_info = st.session_state.db.storage.tables[table_name]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Columns", len(table_info['columns']))
        with col2:
            st.metric("Records", len(table_info['records']))
        with col3:
            st.metric("Created", format_timestamp(table_info['created_at']))
        
        # Column information
        st.subheader("Columns")
        col_df = pd.DataFrame({
            'Column Name': table_info['columns'],
            'Type': 'VARCHAR'  # Simplified type system
        })
        st.dataframe(col_df, use_container_width=True, hide_index=True)
        
        # Sample data
        st.subheader("Sample Data")
        records = list(table_info['records'].values())[:10]  # First 10 records
        if records:
            # Filter out MVCC internal fields for display
            display_records = []
            for record in records:
                display_record = {k: v for k, v in record.items() if not k.startswith('_mvcc_')}
                display_records.append(display_record)
            
            if display_records:
                st.dataframe(display_records, use_container_width=True)
        
        # MVCC information
        if st.session_state.show_advanced:
            with st.expander("MVCC Table Info"):
                st.json(table_info)
    
    def setup_query_history(self):
        """Setup query history tab"""
        st.subheader("Query History")
        
        if not st.session_state.query_history:
            st.info("No query history yet. Execute some queries to see them here!")
            return
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            show_successful = st.checkbox("Show Successful", value=True)
        with col2:
            show_failed = st.checkbox("Show Failed", value=True)
        
        # Filter history
        filtered_history = [
            entry for entry in st.session_state.query_history
            if (show_successful and entry['success']) or (show_failed and not entry['success'])
        ]
        
        if not filtered_history:
            st.warning("No queries match the current filters!")
            return
        
        # Display history
        for i, entry in enumerate(filtered_history[:20]):  # Show last 20 entries
            self.display_history_entry(entry, i)
    
    def display_history_entry(self, entry: dict, index: int):
        """Display a single history entry"""
        timestamp = format_timestamp(entry['timestamp'])
        success = entry['success']
        
        if success:
            bg_color = "#e8f5e8"
            border_color = "#4CAF50"
            icon = "✅"
        else:
            bg_color = "#ffebee"
            border_color = "#f44336"
            icon = "❌"
        
        with st.container():
            st.markdown(f"""
            <div style="background-color: {bg_color};color:black; padding: 15px; border-radius: 10px; border-left: 5px solid {border_color}; margin: 10px 0;">
                <div style="display: flex; justify-content: between; align-items: center;">
                    <h4 style="margin: 0; color: {border_color};">{icon} Query #{index + 1}</h4>
                    <span style="font-size: 0.8em; color: #666;">{timestamp}</span>
                </div>
                <div style="background-color: white;color: black; padding: 10px; border-radius: 5px; margin: 10px 0; font-family: monospace;">
                    {entry['query']}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span><strong>Result:</strong> {entry['message']}</span>
                    <span style="font-size: 0.8em;">
                        Txn: {entry['transaction'] or 'None'} | 
                        Time: {entry['execution_time']:.3f}s | 
                        Rows: {entry.get('affected_rows', 0)}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def setup_analytics(self):
        """Setup analytics tab"""
        st.subheader("MVCC Analytics")
        
        if not st.session_state.query_history:
            st.info("Execute some queries to see analytics!")
            return
        
        # Create analytics
        self.create_performance_charts()
        self.create_query_analysis()
    
        def create_performance_charts(self):
            """Create performance analysis charts"""
            # Execution time analysis
            successful_queries = [q for q in st.session_state.query_history if q['success']]
            
            if successful_queries:
                df = pd.DataFrame(successful_queries)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Execution time over time
                    fig = px.line(df, x='timestamp', y='execution_time', 
                                title="Query Execution Time Over Time")
                    fig.update_layout(xaxis_title="Time", yaxis_title="Execution Time (s)")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Query type distribution
                    df['query_type'] = df['query'].str.split().str[0].str.upper()
                    type_counts = df['query_type'].value_counts()
                    
                    fig = px.pie(values=type_counts.values, names=type_counts.index,
                                title="Query Type Distribution")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Advanced analytics
                col3, col4 = st.columns(2)
                
                with col3:
                    # Success rate over time
                    daily_stats = []
                    dates = pd.date_range(df['timestamp'].min().date(), datetime.now().date())
                    
                    for date in dates:
                        day_queries = [q for q in st.session_state.query_history 
                                    if pd.to_datetime(q['timestamp']).date() == date.date()]
                        if day_queries:
                            successful = sum(1 for q in day_queries if q['success'])
                            total = len(day_queries)
                            daily_stats.append({
                                'date': date,
                                'success_rate': (successful / total) * 100,
                                'total_queries': total
                            })
                    
                    if daily_stats:
                        daily_df = pd.DataFrame(daily_stats)
                        fig = px.bar(daily_df, x='date', y='success_rate',
                                    title="Daily Success Rate")
                        fig.update_layout(xaxis_title="Date", yaxis_title="Success Rate (%)")
                        st.plotly_chart(fig, use_container_width=True)
                
                with col4:
                    # Query performance by type
                    performance_by_type = df.groupby('query_type').agg({
                        'execution_time': ['mean', 'max', 'min'],
                        'affected_rows': 'sum'
                    }).round(4)
                    
                    if not performance_by_type.empty:
                        st.subheader("Performance by Query Type")
                        st.dataframe(performance_by_type, use_container_width=True)

    def create_query_analysis(self):
        """Create detailed query analysis"""
        st.subheader("Query Performance Analysis")
        
        if not st.session_state.query_history:
            return
        
        # Create analysis metrics
        total_queries = len(st.session_state.query_history)
        successful_queries = sum(1 for q in st.session_state.query_history if q['success'])
        failed_queries = total_queries - successful_queries
        avg_execution_time = np.mean([q.get('execution_time', 0) for q in st.session_state.query_history])
        total_rows_affected = sum(q.get('affected_rows', 0) for q in st.session_state.query_history)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Queries", total_queries)
        with col2:
            st.metric("Success Rate", f"{(successful_queries/total_queries)*100:.1f}%")
        with col3:
            st.metric("Avg Execution Time", f"{avg_execution_time:.3f}s")
        with col4:
            st.metric("Total Rows Affected", total_rows_affected)
        
        # Query patterns analysis
        st.subheader("Query Patterns")
        
        # Most frequent queries
        query_texts = [q['query'].strip().upper() for q in st.session_state.query_history]
        query_patterns = {}
        
        for query in query_texts:
            # Extract pattern (first few words)
            words = query.split()
            if len(words) >= 2:
                pattern = ' '.join(words[:2])
                query_patterns[pattern] = query_patterns.get(pattern, 0) + 1
        
        if query_patterns:
            patterns_df = pd.DataFrame({
                'Pattern': list(query_patterns.keys()),
                'Count': list(query_patterns.values())
            }).sort_values('Count', ascending=False)
            
            fig = px.bar(patterns_df.head(10), x='Pattern', y='Count',
                        title="Most Frequent Query Patterns")
            st.plotly_chart(fig, use_container_width=True)

    def setup_concurrency_demo(self):
        """Setup concurrency demonstration"""
        st.subheader("MVCC Concurrency Demo")
        
        st.markdown("""
        **Demonstrate MVCC in action:**
        
        1. Start two transactions in different sessions
        2. Make changes in one transaction
        3. Observe isolation in the other transaction
        4. Commit/Rollback to see final state
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Start Demo Session 1", use_container_width=True):
                txn1 = st.session_state.db.begin_transaction("REPEATABLE_READ")
                st.session_state.demo_txn1 = txn1
                st.success(f"Demo Session 1 started with TXN {txn1}")
            
            if hasattr(st.session_state, 'demo_txn1'):
                st.info(f"Demo Session 1 Active: TXN {st.session_state.demo_txn1}")
                
                demo_query = st.text_area(
                    "Session 1 Query:",
                    value="SELECT * FROM users",
                    key="demo_session1"
                )
                
                if st.button("Execute in Session 1", key="exec_demo1"):
                    result = st.session_state.db.execute(demo_query, st.session_state.demo_txn1)
                    self.display_demo_result(result, "Session 1")
        
        with col2:
            if st.button("Start Demo Session 2", use_container_width=True):
                txn2 = st.session_state.db.begin_transaction("REPEATABLE_READ")
                st.session_state.demo_txn2 = txn2
                st.success(f"Demo Session 2 started with TXN {txn2}")
            
            if hasattr(st.session_state, 'demo_txn2'):
                st.info(f"Demo Session 2 Active: TXN {st.session_state.demo_txn2}")
                
                demo_query = st.text_area(
                    "Session 2 Query:",
                    value="SELECT * FROM users", 
                    key="demo_session2"
                )
                
                if st.button("Execute in Session 2", key="exec_demo2"):
                    result = st.session_state.db.execute(demo_query, st.session_state.demo_txn2)
                    self.display_demo_result(result, "Session 2")
        
        # Demo controls
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Commit Session 1", 
                        disabled=not hasattr(st.session_state, 'demo_txn1')):
                st.session_state.db.commit_transaction(st.session_state.demo_txn1)
                del st.session_state.demo_txn1
                st.success("Session 1 committed!")
        
        with col2:
            if st.button("Rollback Session 1",
                        disabled=not hasattr(st.session_state, 'demo_txn1')):
                st.session_state.db.rollback_transaction(st.session_state.demo_txn1)
                del st.session_state.demo_txn1
                st.success("Session 1 rolled back!")
        
        with col3:
            if st.button("Commit Session 2",
                        disabled=not hasattr(st.session_state, 'demo_txn2')):
                st.session_state.db.commit_transaction(st.session_state.demo_txn2)
                del st.session_state.demo_txn2
                st.success("Session 2 committed!")
        
        with col4:
            if st.button("Rollback Session 2",
                        disabled=not hasattr(st.session_state, 'demo_txn2')):
                st.session_state.db.rollback_transaction(st.session_state.demo_txn2)
                del st.session_state.demo_txn2
                st.success("Session 2 rolled back!")

    def display_demo_result(self, result: dict, session_name: str):
        """Display demo execution results"""
        if result['success']:
            st.success(f"{session_name}: {result['message']}")
            
            if result['data']:
                st.dataframe(pd.DataFrame(result['data']), use_container_width=True)
        else:
            st.error(f"{session_name}: {result.get('error', 'Unknown error')}")

    def run(self):
        """Run the enhanced application"""
        # Custom CSS for better styling
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.3rem;
            color: #ff7f0e;
            margin-bottom: 1rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #1f77b4;
        }
        .transaction-active {
            background: linear-gradient(45deg, #e8f5e8, #c8e6c9);
            padding: 15px;
            border-radius: 10px;
            border: 2px solid #4caf50;
        }
        .transaction-inactive {
            background: linear-gradient(45deg, #ffebee, #ffcdd2);
            padding: 15px;
            border-radius: 10px;
            border: 2px solid #f44336;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Setup the application
        self.setup_sidebar()
        self.setup_main_content()
        
        # Add concurrency demo in a separate section
        st.markdown("---")
        self.setup_concurrency_demo()

def main():
    """Main entry point for the enhanced application"""
    try:
        app = EnhancedSQLApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please refresh the page to restart the application.")

if __name__ == "__main__":
    main()