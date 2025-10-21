"""
Configuration settings for SQL MVCC Engine
"""

import os
from typing import Dict, Any

class Config:
    """Configuration class for SQL MVCC Engine"""
    
    # Database settings
    DATABASE_NAME = "mvcc_database"
    DATA_DIRECTORY = "data"
    MAX_TABLE_SIZE = 100000  # Maximum records per table
    
    # MVCC settings
    DEFAULT_ISOLATION_LEVEL = "READ_COMMITTED"
    MAX_CONCURRENT_TRANSACTIONS = 100
    VERSION_RETENTION_DAYS = 7
    
    # UI settings
    DEFAULT_PAGE_TITLE = "SQL MVCC Engine"
    DEFAULT_PAGE_ICON = "🔍"
    QUERY_HISTORY_SIZE = 1000
    MAX_DISPLAY_RECORDS = 1000
    
    # Performance settings
    ENABLE_QUERY_CACHE = True
    CACHE_SIZE = 1000
    AUTO_COMMIT_TIMEOUT = 300  # seconds
    
    # Security settings
    ENABLE_SQL_INJECTION_PROTECTION = True
    MAX_QUERY_LENGTH = 10000
    
    @classmethod
    def get_database_path(cls) -> str:
        """Get database storage path"""
        return os.path.join(cls.DATA_DIRECTORY, f"{cls.DATABASE_NAME}.pkl")
    
    @classmethod
    def get_log_path(cls) -> str:
        """Get log file path"""
        return os.path.join("logs", "mvcc_engine.log")
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'database_name': cls.DATABASE_NAME,
            'data_directory': cls.DATA_DIRECTORY,
            'default_isolation_level': cls.DEFAULT_ISOLATION_LEVEL,
            'max_concurrent_transactions': cls.MAX_CONCURRENT_TRANSACTIONS,
            'version_retention_days': cls.VERSION_RETENTION_DAYS,
            'enable_query_cache': cls.ENABLE_QUERY_CACHE,
            'cache_size': cls.CACHE_SIZE
        }

# Development configuration
class DevelopmentConfig(Config):
    """Development configuration"""
    ENABLE_DEBUG_LOGGING = True
    AUTO_COMMIT_TIMEOUT = 60

# Production configuration  
class ProductionConfig(Config):
    """Production configuration"""
    ENABLE_DEBUG_LOGGING = False
    MAX_CONCURRENT_TRANSACTIONS = 1000

# Current configuration
current_config = DevelopmentConfig()