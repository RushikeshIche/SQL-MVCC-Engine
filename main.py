#!/usr/bin/env python3
"""
SQL MVCC Engine - Main Entry Point
A simple DBMS with MVCC support and modern UI
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.enhanced_app import main as ui_main
from engine.database import Database

def main():
    """Main entry point for the SQL MVCC Engine"""
    print("Starting SQL MVCC Engine...")
    print("MVCC Features:")
    print("- Transaction Isolation")
    print("- Version Control")
    print("- Concurrent Access")
    print("- Rollback Support")
    print()
    
    ui_main()

if __name__ == "__main__":
    main()