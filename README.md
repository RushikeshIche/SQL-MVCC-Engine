#  SQL MVCC Engine

A comprehensive Database Management System with Multi-Version Concurrency Control (MVCC) implementation in Python, featuring a modern web-based UI.

## 🚀 Features

### Core Database
- **SQL Parser**: Supports CREATE, SELECT, INSERT, UPDATE, DELETE operations
- **Transaction Management**: BEGIN, COMMIT, ROLLBACK support
- **Data Persistence**: Automatic saving and loading of database state

### MVCC Implementation
- **Multi-Version Concurrency Control**: Maintains multiple versions of records
- **Transaction Isolation**: READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE
- **Version Control**: Track record versions with transaction visibility
- **Concurrent Access**: Safe concurrent read/write operations
- **Rollback Support**: Automatic cleanup of aborted transactions

### Modern UI
- **Streamlit-based Interface**: Clean, responsive web UI
- **Query Editor**: Syntax-highlighted SQL editor with history
- **Schema Explorer**: Visual table structure and data browser
- **Performance Analytics**: Query performance monitoring and charts
- **Concurrency Demo**: Interactive MVCC demonstration

## 🛠️ Installation

### Quick Start
```bash
# Clone or download the project
git clone <repository-url>
cd sql_mvcc_engine

# Run setup script
python setup.py

# Start the application
streamlit run ui/enhanced_app.py