import React, { useState } from 'react';
import { Play, FileText } from 'lucide-react';

const QueryEditor = ({ onQueryResult, activeTransaction }) => {
  const [query, setQuery] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);

  const sampleQueries = [
    {
      name: "Create Users Table",
      query: "CREATE TABLE users (id INT, name VARCHAR, email VARCHAR, age INT)"
    },
    {
      name: "Insert Sample Data", 
      query: "INSERT INTO users (id, name, email, age) VALUES (1, 'Alice', 'alice@email.com', 30)"
    },
    {
      name: "Select All Users",
      query: "SELECT * FROM users"
    },
    {
      name: "Begin Transaction",
      query: "BEGIN TRANSACTION"
    }
  ];

  const executeQuery = async () => {
    if (!query.trim()) return;

    setIsExecuting(true);
    try {
      const response = await fetch('http://localhost:8000/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          transaction_id: activeTransaction?.id
        }),
      });

      const result = await response.json();
      onQueryResult(query.trim(), result);
    } catch (error) {
      onQueryResult(query.trim(), {
        success: false,
        error: `Network error: ${error.message}`,
        data: [],
        columns: []
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
      executeQuery();
    }
  };

  return (
    <div className="h-full flex flex-col legacy-panel">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-3 border-b border-oracle-border bg-gray-50">
        <div className="flex items-center space-x-2">
          <button
            onClick={executeQuery}
            disabled={isExecuting}
            className="legacy-button flex items-center space-x-1 disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            <span>Execute</span>
          </button>
          <span className="text-xs text-gray-500 ml-2">
            Ctrl+Enter to execute
          </span>
        </div>
        
        {activeTransaction && (
          <div className="flex items-center space-x-2 text-sm">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-green-700 font-medium">
              Transaction #{activeTransaction.id} Active
            </span>
          </div>
        )}
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Query Input */}
        <div className="flex-1 flex flex-col">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Enter your SQL query here...&#10;Example: SELECT * FROM users WHERE age > 25"
            className="flex-1 p-4 code-editor resize-none border-none focus:outline-none bg-white custom-scrollbar"
            spellCheck="false"
          />
        </div>

        {/* Quick Queries Sidebar */}
        <div className="w-64 border-l border-oracle-border bg-gray-50 flex flex-col">
          <div className="p-3 border-b border-oracle-border">
            <h3 className="font-medium text-sm text-gray-700 flex items-center">
              <FileText className="w-4 h-4 mr-2" />
              Quick Queries
            </h3>
          </div>
          <div className="flex-1 overflow-auto p-2 space-y-2">
            {sampleQueries.map((sample, index) => (
              <button
                key={index}
                onClick={() => setQuery(sample.query)}
                className="w-full text-left p-2 text-sm bg-white rounded border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
              >
                <div className="font-medium text-gray-800">{sample.name}</div>
                <div className="text-xs text-gray-500 mt-1 truncate">
                  {sample.query}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default QueryEditor;