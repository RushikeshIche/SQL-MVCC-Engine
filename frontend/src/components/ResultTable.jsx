import React from 'react';
import { CheckCircle, XCircle, Clock, Database } from 'lucide-react';

const ResultTable = ({ result }) => {
  if (!result) return null;

  return (
    <div className="max-h-80 flex flex-col">
      {/* Result Header */}
      <div className={`p-3 border-b ${
        result.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {result.success ? (
              <CheckCircle className="w-5 h-5 text-green-600" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600" />
            )}
            <div>
              <div className="font-medium text-sm">
                {result.success ? 'Query executed successfully' : 'Query failed'}
              </div>
              <div className="text-xs text-gray-600">
                {result.message || result.error}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            {result.execution_time > 0 && (
              <div className="flex items-center space-x-1">
                <Clock className="w-4 h-4" />
                <span>{result.execution_time.toFixed(3)}s</span>
              </div>
            )}
            {result.affected_rows > 0 && (
              <div className="flex items-center space-x-1">
                <Database className="w-4 h-4" />
                <span>{result.affected_rows} row(s) affected</span>
              </div>
            )}
            {result.transaction_id && (
              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                TXN #{result.transaction_id}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Results Table */}
      {result.success && result.columns && result.columns.length > 0 && (
        <div className="flex-1 overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                {result.columns.map((column, index) => (
                  <th key={index} className="text-left p-2 border-b font-medium text-gray-700">
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.data && result.data.length > 0 ? (
                result.data.map((row, rowIndex) => (
                  <tr key={rowIndex} className="border-b hover:bg-gray-50">
                    {result.columns.map((column, colIndex) => (
                      <td key={colIndex} className="p-2 text-gray-600">
                        {String(row[column] || '')}
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={result.columns.length} className="p-4 text-center text-gray-500">
                    <div className="flex flex-col items-center">
                      <Database className="w-8 h-8 mb-2 text-gray-300" />
                      <div>No records in table</div>
                      <div className="text-sm">Table structure is displayed above</div>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* No Results Message (for queries that don't return columns) */}
      {result.success && (!result.columns || result.columns.length === 0) && (
        <div className="flex-1 flex items-center justify-center text-gray-500">
          <div className="text-center">
            <Database className="w-8 h-8 mx-auto mb-2 text-gray-300" />
            <div>Query executed successfully</div>
            <div className="text-sm">No data to display</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultTable;