import React from 'react';
import { Clock, PlayCircle, CheckCircle, XCircle } from 'lucide-react';

const Transactions = ({ transactions }) => {
  const formatTime = (iso) => iso ? new Date(iso).toLocaleString() : '-';

  return (
    <div className="h-full legacy-panel">
      <div className="p-4 border-b border-oracle-border bg-gray-50 flex items-center justify-between">
        <div className="flex items-center">
          <PlayCircle className="w-5 h-5 mr-2 text-blue-500" />
          <h2 className="font-semibold text-gray-800">Transactions</h2>
        </div>
        <div className="text-sm text-gray-600">Showing recent transaction activity</div>
      </div>

      <div className="overflow-auto custom-scrollbar h-full p-4 space-y-3">
        {transactions.length === 0 && (
          <div className="p-8 text-center text-gray-500">No transactions yet. Begin a transaction to see it listed here.</div>
        )}

        {transactions.map((t, idx) => (
          <div key={`${t.id}-${idx}`} className="bg-white border border-oracle-border rounded p-4 shadow-sm">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center">
                  <span className="text-blue-600 font-medium">#{t.id}</span>
                </div>
                <div>
                  <div className="text-sm font-semibold text-gray-800">Transaction #{t.id}</div>
                  <div className="text-xs text-gray-500">Isolation: {t.isolationLevel || 'default'}</div>
                </div>
              </div>

              <div className="text-right text-sm">
                <div className="flex items-center justify-end space-x-2">
                  {t.end ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <PlayCircle className="w-4 h-4 text-blue-500" />
                  )}
                  <span className="text-gray-600">{t.status}</span>
                </div>
                <div className="text-xs text-gray-500 mt-1">{t.start ? formatTime(t.start) : '-'}</div>
                <div className="text-xs text-gray-500">{t.end ? formatTime(t.end) : 'In progress'}</div>
              </div>
            </div>

            {/* Sequence removed by request - no visual element here */}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Transactions;
