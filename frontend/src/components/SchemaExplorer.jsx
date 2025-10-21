import React from 'react';
import { Database, Table, ChevronRight, ChevronDown } from 'lucide-react';

const SchemaExplorer = ({ tables }) => {
  const [expandedTables, setExpandedTables] = React.useState({});

  const toggleTable = (tableName) => {
    setExpandedTables(prev => ({
      ...prev,
      [tableName]: !prev[tableName]
    }));
  };

  return (
    <div className="p-3">
      <div className="mb-4">
        <div className="flex items-center text-sm font-medium text-gray-700 mb-2">
          <Database className="w-4 h-4 mr-2" />
          Database Tables
          <span className="ml-2 bg-gray-200 text-gray-700 px-2 py-0.5 rounded text-xs">
            {tables.length}
          </span>
        </div>
      </div>

      <div className="space-y-1">
        {tables.map((table) => (
          <div key={table.name} className="border border-gray-200 rounded">
            <button
              onClick={() => toggleTable(table.name)}
              className="w-full flex items-center justify-between p-2 hover:bg-gray-50 text-left"
            >
              <div className="flex items-center space-x-2">
                {expandedTables[table.name] ? (
                  <ChevronDown className="w-3 h-3 text-gray-500" />
                ) : (
                  <ChevronRight className="w-3 h-3 text-gray-500" />
                )}
                <Table className="w-4 h-4 text-blue-500" />
                <span className="font-medium text-sm">{table.name}</span>
              </div>
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {table.record_count} rows
              </span>
            </button>
            
            {expandedTables[table.name] && (
              <div className="bg-gray-50 border-t border-gray-200 p-2">
                <div className="text-xs font-medium text-gray-600 mb-1">Columns:</div>
                <div className="space-y-1">
                  {table.columns.map((column, index) => (
                    <div key={index} className="flex items-center text-sm text-gray-700">
                      <div className="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
                      {column}
                      {column === table.primary_key && (
                        <span className="ml-2 text-xs text-yellow-800 bg-yellow-200 px-1 rounded">
                          PK
                        </span>
                      )}
                    </div>
                  ))}
                </div>
                <div className="mt-2 text-xs text-gray-500">
                  Created: {new Date(table.created_at).toLocaleDateString()}
                </div>
              </div>
            )}
          </div>
        ))}
        
        {tables.length === 0 && (
          <div className="text-center py-8 text-gray-500 text-sm">
            <Table className="w-8 h-8 mx-auto mb-2 text-gray-300" />
            <div>No tables found</div>
            <div className="text-xs mt-1">Create a table to get started</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SchemaExplorer;