import React from 'react';
import { BarChart3, Clock, Database, Zap } from 'lucide-react';

const AnalyticsPanel = ({ history }) => {
  const analytics = {
    totalQueries: history.length,
    successfulQueries: history.filter(h => h.success).length,
    failedQueries: history.filter(h => !h.success).length,
    averageExecutionTime: history.length > 0
      ? history.reduce((acc, h) => acc + h.execution_time, 0) / history.length
      : 0,
  };

  const successRate = analytics.totalQueries > 0
    ? ((analytics.successfulQueries / analytics.totalQueries) * 100).toFixed(1)
    : '0.0';

  const getQueryDistribution = () => {
    const distribution = {
      SELECT: 0,
      INSERT: 0,
      UPDATE: 0,
      CREATE: 0,
      DELETE: 0,
      Other: 0,
    };

    history.forEach(item => {
      const query = item.query.trim().toUpperCase();
      if (query.startsWith('SELECT')) distribution.SELECT++;
      else if (query.startsWith('INSERT')) distribution.INSERT++;
      else if (query.startsWith('UPDATE')) distribution.UPDATE++;
      else if (query.startsWith('CREATE')) distribution.CREATE++;
      else if (query.startsWith('DELETE')) distribution.DELETE++;
      else distribution.Other++;
    });

    return Object.entries(distribution)
      .map(([type, count]) => ({
        type,
        count,
        percentage: analytics.totalQueries > 0 ? (count / analytics.totalQueries) * 100 : 0,
      }))
      .filter(item => item.count > 0)
      .sort((a, b) => b.count - a.count);
  };

  const queryDistribution = getQueryDistribution();

  return (
    <div className="h-full legacy-panel">
      <div className="p-4 border-b border-oracle-border bg-gray-50">
        <h2 className="font-semibold text-gray-800 flex items-center">
          <BarChart3 className="w-5 h-5 mr-2" />
          Performance Analytics
        </h2>
      </div>

      <div className="p-6 space-y-6 overflow-auto h-full">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white border border-oracle-border rounded p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-800">{analytics.totalQueries}</div>
                <div className="text-sm text-gray-600">Total Queries</div>
              </div>
              <Database className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white border border-oracle-border rounded p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-green-600">{successRate}%</div>
                <div className="text-sm text-gray-600">Success Rate</div>
              </div>
              <Zap className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-white border border-oracle-border rounded p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-800">{analytics.averageExecutionTime.toFixed(4)}s</div>
                <div className="text-sm text-gray-600">Avg Execution Time</div>
              </div>
              <Clock className="w-8 h-8 text-purple-500" />
            </div>
          </div>
          
          <div className="bg-white border border-oracle-border rounded p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-red-600">{analytics.failedQueries}</div>
                <div className="text-sm text-gray-600">Failed Queries</div>
              </div>
              <BarChart3 className="w-8 h-8 text-red-500" />
            </div>
          </div>
        </div>

        {/* Query Distribution */}
        {history.length > 0 && (
          <div className="bg-white border border-oracle-border rounded p-4">
            <h3 className="font-semibold text-gray-800 mb-3">Query Distribution</h3>
            <div className="space-y-2">
              {queryDistribution.map(item => (
                <div key={item.type} className="flex items-center justify-between text-sm">
                  <span>{item.type}</span>
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${item.percentage}%` }}></div>
                  </div>
                  <span className="text-gray-600">{item.percentage.toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Performance Tips */}
        <div className="bg-blue-50 border border-blue-200 rounded p-4">
          <h3 className="font-semibold text-blue-800 mb-2">Performance Tips</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Use WHERE clauses to limit result sets</li>
            <li>• Consider transactions for multiple related operations</li>
            <li>• Use specific column names instead of SELECT *</li>
            <li>• Monitor query execution times in history</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPanel;