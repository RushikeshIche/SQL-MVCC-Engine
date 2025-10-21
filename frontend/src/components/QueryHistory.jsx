import React from 'react';
import { Clock, CheckCircle, XCircle, Copy } from 'lucide-react';

const QueryHistory = ({ history }) => {
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="h-full legacy-panel">
      <div className="p-4 border-b border-oracle-border bg-gray-50">
        <h2 className="font-semibold text-gray-800 flex items-center">
          <Clock className="w-5 h-5 mr-2" />
          Query History
        </h2>
      </div>
      
      <div className="overflow-auto custom-scrollbar h-full">
        {history.map((item) => (
          <div
            key={item.id}
            className={`border-b border-oracle-border p-4 ${
              item.success ? 'bg-white' : 'bg-red-50'
            }`}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-2">
                {item.success ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-500" />
                )}
                <span className="text-sm text-gray-500">
                  {formatTime(item.timestamp)}
                </span>
                {item.transaction_id && (
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    TXN #{item.transaction_id}
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <span>{item.execution_time.toFixed(4)}s</span>
                <button
                  onClick={() => copyToClipboard(item.query)}
                  className="p-1 hover:bg-gray-200 rounded"
                >
                  <Copy className="w-3 h-3" />
                </button>
              </div>
            </div>
            
            <div className="code-editor text-sm bg-gray-100 p-3 rounded border">
              {item.query}
            </div>
            
            {!item.success && item.error && (
              <div className="mt-2 text-sm text-red-600 bg-red-100 p-2 rounded">
                Error: {item.error}
              </div>
            )}
          </div>
        ))}
        
        {history.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            No query history yet. Execute some queries to see them here.
          </div>
        )}
      </div>
    </div>
  );
};

export default QueryHistory;