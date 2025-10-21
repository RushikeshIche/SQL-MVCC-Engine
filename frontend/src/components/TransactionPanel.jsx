import React, { useState } from 'react';
import { Play, Square, RotateCcw, Settings } from 'lucide-react';

const TransactionPanel = ({ onTransactionUpdate, activeTransaction }) => {
  const [isolationLevel, setIsolationLevel] = useState('READ_COMMITTED');

  const isolationLevels = [
    { value: 'READ_UNCOMMITTED', label: 'Read Uncommitted' },
    { value: 'READ_COMMITTED', label: 'Read Committed' },
    { value: 'REPEATABLE_READ', label: 'Repeatable Read' },
    { value: 'SERIALIZABLE', label: 'Serializable' }
  ];

  const beginTransaction = async () => {
    try {
      const response = await fetch('http://localhost:8000/transaction/begin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          isolation_level: isolationLevel
        }),
      });

      const result = await response.json();
      // Mark new transaction as active on the frontend
      onTransactionUpdate({
        id: result.transaction_id,
        status: 'active',
        isolationLevel: isolationLevel
      });
    } catch (error) {
      console.error('Failed to begin transaction:', error);
    }
  };

  const commitTransaction = async () => {
    if (!activeTransaction) return;

    try {
      const response = await fetch(`http://localhost:8000/transaction/${activeTransaction.id}/commit`, {
        method: 'POST',
      });

      const result = await response.json();
      if (result.success) {
        // Signal that the active transaction has ended (committed)
        onTransactionUpdate({ id: activeTransaction.id, status: 'ended' });

      }
    } catch (error) {
      console.error('Failed to commit transaction:', error);
    }
  };

  const rollbackTransaction = async () => {
    if (!activeTransaction) return;

    try {
      const response = await fetch(`http://localhost:8000/transaction/${activeTransaction.id}/rollback`, {
        method: 'POST',
      });

      const result = await response.json();
      if (result.success) {
        // Signal that the active transaction has been aborted (rolled back)
        onTransactionUpdate({ id: activeTransaction.id, status: 'aborted' });

      }
    } catch (error) {
      console.error('Failed to rollback transaction:', error);
    }
  };

  return (
    <div className="flex items-center space-x-3">
      {/* Isolation Level Selector */}
      <div className="flex items-center space-x-2">
        <Settings className="w-4 h-4 text-gray-400" />
        <select
          value={isolationLevel}
          onChange={(e) => setIsolationLevel(e.target.value)}
          disabled={!!activeTransaction}
          className="text-sm border text-black border-gray-300 rounded px-2 py-1 bg-white disabled:bg-gray-100 disabled:text-gray-500"
        >
          {isolationLevels.map(level => (
            <option key={level.value} value={level.value}>
              {level.label}
            </option>
          ))}
        </select>
      </div>

      {/* Transaction Controls */}
      {!activeTransaction ? (
        <button
          onClick={beginTransaction}
          className="legacy-button flex items-center space-x-1"
        >
          <Play className="w-4 h-4" />
          <span>Begin TXN</span>
        </button>
      ) : (
        <div className="flex items-center space-x-2">
          <button
            onClick={commitTransaction}
            className="legacy-button flex items-center space-x-1 bg-green-600 border-green-700 hover:bg-green-700"
          >
            <Square className="w-4 h-4" />
            <span>Commit</span>
          </button>
          <button
            onClick={rollbackTransaction}
            className="legacy-button-secondary flex items-center space-x-1"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Rollback</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default TransactionPanel;