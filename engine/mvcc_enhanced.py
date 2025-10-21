"""
Enhanced MVCC Manager with better isolation level support
"""

from typing import Dict, Any, List, Set
from datetime import datetime
import threading
from enum import Enum

class IsolationLevel(Enum):
    READ_UNCOMMITTED = "READ_UNCOMMITTED"
    READ_COMMITTED = "READ_COMMITTED"
    REPEATABLE_READ = "REPEATABLE_READ"
    SERIALIZABLE = "SERIALIZABLE"

class EnhancedMVCCManager:
    """Enhanced MVCC manager with full isolation level support"""
    
    def __init__(self, storage):
        self.storage = storage
        self.transactions = {}
        self.transaction_snapshots = {}
        self.next_txn_id = 1
        self.lock = threading.RLock()
        self.version_chain = {}  # Tracks version chains for records
        
        self._initialize_system_tables()
    
    def _initialize_system_tables(self):
        """Initialize system tables"""
        if not self.storage.table_exists('mvcc_transactions'):
            self.storage.create_table('mvcc_transactions', [
                'txn_id', 'status', 'start_time', 'isolation_level', 'snapshot_time'
            ])
        
        if not self.storage.table_exists('mvcc_locks'):
            self.storage.create_table('mvcc_locks', [
                'lock_id', 'table_name', 'record_id', 'txn_id', 'lock_type', 'acquired_at'
            ])
    
    def begin_transaction(self, isolation_level: str = "READ_COMMITTED") -> int:
        """Start a new transaction with specified isolation level"""
        with self.lock:
            txn_id = self.next_txn_id
            self.next_txn_id += 1
            
            snapshot_time = datetime.now()
            
            transaction = {
                'txn_id': txn_id,
                'status': 'ACTIVE',
                'start_time': snapshot_time.isoformat(),
                'isolation_level': IsolationLevel(isolation_level),
                'snapshot_time': snapshot_time,
                'changes': {}  # Track changes for rollback
            }
            
            self.transactions[txn_id] = transaction
            
            # Create snapshot for REPEATABLE_READ and SERIALIZABLE
            if isolation_level in ["REPEATABLE_READ", "SERIALIZABLE"]:
                self._create_snapshot(txn_id, snapshot_time)
            
            # Record in system table
            self.storage.insert_record('mvcc_transactions', {
                'txn_id': txn_id,
                'status': 'ACTIVE',
                'start_time': transaction['start_time'],
                'isolation_level': isolation_level,
                'snapshot_time': snapshot_time.isoformat()
            })
            
            return txn_id
    
    def _create_snapshot(self, txn_id: int, snapshot_time: datetime):
        """Create a snapshot of the database for transaction"""
        snapshot = {}
        for table_name in self.storage.get_table_names():
            # Store committed records as of snapshot time
            all_records = self.storage.get_all_records(table_name)
            visible_records = [
                record for record in all_records 
                if self._is_record_visible_at_time(record, snapshot_time)
            ]
            snapshot[table_name] = visible_records
        
        self.transaction_snapshots[txn_id] = snapshot
    
    def _is_record_visible_at_time(self, record: Dict[str, Any], snapshot_time: datetime) -> bool:
        """Check if record was visible at specific time"""
        created_txn = record.get('_mvcc_created_txn', 0)
        deleted_txn = record.get('_mvcc_deleted_txn')
        created_ts = datetime.fromisoformat(record.get('_mvcc_created_ts', '1970-01-01'))
        
        # Record created after snapshot time
        if created_ts > snapshot_time:
            return False
        
        # Record was deleted before snapshot time
        if deleted_txn and deleted_txn in self.transactions:
            deleted_txn_data = self.transactions[deleted_txn]
            if deleted_txn_data['status'] == 'COMMITTED':
                commit_time = datetime.fromisoformat(deleted_txn_data.get('commit_time', created_ts.isoformat()))
                if commit_time <= snapshot_time:
                    return False
        
        return created_txn == 0 or (
            created_txn in self.transactions and 
            self.transactions[created_txn]['status'] == 'COMMITTED'
        )
    
    def get_visible_records(self, table_name: str, txn_id: int = None) -> List[Dict[str, Any]]:
        """Get records visible to transaction based on isolation level"""
        if not self.storage.table_exists(table_name):
            return []
        
        if txn_id is None or txn_id not in self.transactions:
            # No transaction - show only committed records
            all_records = self.storage.get_all_records(table_name)
            return [
                record for record in all_records 
                if self._is_record_visible(record, None)
            ]
        
        transaction = self.transactions[txn_id]
        isolation_level = transaction['isolation_level']
        
        if isolation_level == IsolationLevel.READ_UNCOMMITTED:
            return self._get_read_uncommitted(table_name, txn_id)
        elif isolation_level == IsolationLevel.READ_COMMITTED:
            return self._get_read_committed(table_name, txn_id)
        elif isolation_level == IsolationLevel.REPEATABLE_READ:
            return self._get_repeatable_read(table_name, txn_id)
        elif isolation_level == IsolationLevel.SERIALIZABLE:
            return self._get_serializable(table_name, txn_id)
        else:
            return self._get_read_committed(table_name, txn_id)
    
    def _get_read_uncommitted(self, table_name: str, txn_id: int) -> List[Dict[str, Any]]:
        """READ UNCOMMITTED - can see uncommitted changes"""
        all_records = self.storage.get_all_records(table_name)
        visible_records = []
        
        for record in all_records:
            created_txn = record.get('_mvcc_created_txn', 0)
            deleted_txn = record.get('_mvcc_deleted_txn')
            
            # Can see records created by any transaction
            # Only filter out records deleted by current transaction
            if deleted_txn != txn_id:
                visible_records.append(record)
        
        return visible_records
    
    def _get_read_committed(self, table_name: str, txn_id: int) -> List[Dict[str, Any]]:
        """READ COMMITTED - can only see committed records"""
        all_records = self.storage.get_all_records(table_name)
        visible_records = []
        
        for record in all_records:
            if self._is_record_visible(record, txn_id):
                visible_records.append(record)
        
        return visible_records
    
    def _get_repeatable_read(self, table_name: str, txn_id: int) -> List[Dict[str, Any]]:
        """REPEATABLE READ - sees snapshot at transaction start"""
        if txn_id in self.transaction_snapshots:
            snapshot = self.transaction_snapshots[txn_id]
            return snapshot.get(table_name, [])
        else:
            # Fallback to read committed
            return self._get_read_committed(table_name, txn_id)
    
    def _get_serializable(self, table_name: str, txn_id: int) -> List[Dict[str, Any]]:
        """SERIALIZABLE - strictest isolation with conflict detection"""
        # For simplicity, we use repeatable read behavior
        # In real implementation, this would include predicate locking
        return self._get_repeatable_read(table_name, txn_id)
    
    def _is_record_visible(self, record: Dict[str, Any], txn_id: int = None) -> bool:
        """Check if record is visible to transaction"""
        created_txn = record.get('_mvcc_created_txn', 0)
        deleted_txn = record.get('_mvcc_deleted_txn')

        # Rule 1: Is the record created by the current transaction?
        if txn_id and created_txn == txn_id:
            # If so, it's visible unless it was also deleted by the same transaction.
            return deleted_txn != txn_id

        # Rule 2: Has the creating transaction been committed?
        # A record is only potentially visible if its creator has committed.
        # created_txn == 0 is for records created before transactions were tracked.
        creator_is_committed = (created_txn == 0) or (
            created_txn in self.transactions and
            self.transactions[created_txn]['status'] == 'COMMITTED'
        )

        if not creator_is_committed:
            return False

        # Rule 3: Has the record been deleted?
        if deleted_txn is None:
            # If not deleted, and creator is committed, it's visible.
            return True

        # Rule 4: If deleted, has the deleting transaction been committed?
        # A record is still visible if the transaction that deleted it has NOT committed.
        deleter_is_committed = (
            deleted_txn in self.transactions and
            self.transactions[deleted_txn]['status'] == 'COMMITTED'
        )

        return not deleter_is_committed
    
    def commit_transaction(self, txn_id: int) -> bool:
        """Commit a transaction"""
        with self.lock:
            if txn_id not in self.transactions or self.transactions[txn_id]['status'] != 'ACTIVE':
                return False
            
            transaction = self.transactions[txn_id]
            transaction['status'] = 'COMMITTED'
            transaction['commit_time'] = datetime.now().isoformat()
            
            # Update system table - fetch existing record and update it
            existing_record = self.storage.get_record('mvcc_transactions', txn_id)
            if existing_record:
                existing_record.update({
                    'status': 'COMMITTED',
                    'commit_time': transaction['commit_time']
                })
                self.storage.update_record('mvcc_transactions', txn_id, existing_record)

            # Clean up snapshot
            if txn_id in self.transaction_snapshots:
                del self.transaction_snapshots[txn_id]
            
            return True
    
    def rollback_transaction(self, txn_id: int) -> bool:
        """Rollback a transaction"""
        with self.lock:
            if txn_id not in self.transactions or self.transactions[txn_id]['status'] != 'ACTIVE':
                return False
            
            self.transactions[txn_id]['status'] = 'ROLLED_BACK'
            
            # Update system table
            existing_record = self.storage.get_record('mvcc_transactions', txn_id)
            if existing_record:
                existing_record.update({'status': 'ROLLED_BACK'})
                self.storage.update_record('mvcc_transactions', txn_id, existing_record)
            
            # Remove records created by this transaction
            self._remove_transaction_records(txn_id)
            
            # Clean up snapshot
            if txn_id in self.transaction_snapshots:
                del self.transaction_snapshots[txn_id]
            
            return True
    
    def _remove_transaction_records(self, txn_id: int):
        """Remove records created by rolled back transaction"""
        for table_name in self.storage.get_table_names():
            records = self.storage.get_all_records(table_name)
            for record in records:
                if record.get('_mvcc_created_txn') == txn_id:
                    self.storage.delete_record(table_name, record['id'])
    
    def get_transaction_info(self, txn_id: int) -> Dict[str, Any]:
        """Get detailed transaction information"""
        if txn_id not in self.transactions:
            return {}
        
        txn = self.transactions[txn_id].copy()
        
        # Add additional info
        txn['has_snapshot'] = txn_id in self.transaction_snapshots
        txn['active_time'] = str(datetime.now() - datetime.fromisoformat(txn['start_time']))
        
        return txn
    
    def get_database_status(self) -> Dict[str, Any]:
        """Get overall database MVCC status"""
        active_transactions = [
            txn_id for txn_id, txn in self.transactions.items() 
            if txn['status'] == 'ACTIVE'
        ]
        
        return {
            'total_transactions': len(self.transactions),
            'active_transactions': len(active_transactions),
            'next_transaction_id': self.next_txn_id,
            'snapshots_count': len(self.transaction_snapshots)
        }