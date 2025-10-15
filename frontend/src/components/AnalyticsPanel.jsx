import React from 'react';
import { BarChart3, Clock, Database, Zap } from 'lucide-react';

const AnalyticsPanel = () => {
  const analytics = {
    totalQueries: 47,
    successfulQueries: 42,
    failedQueries: 5,
    averageExecutionTime: 0.023,
    mostUsedTable: 'users',
    busiestHour: '10:00-11:00'
  };

  const successRate = ((analytics.successfulQueries / analytics.totalQueries) * 100).toFixed(1);

  return (
    <div className="h-full legacy-panel">
      <div className="p-4 border-b border-oracle-border bg-gray-50">
        <h2 className="font-semibold text-gray-800 flex items-center">
          <BarChart3 className="w-5 h-5 mr-2" />
          Performance Analytics
        </h2>
      </div>

      <div className="p-6 space-y-6">
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
                <div className="text-2xl font-bold text-gray-800">{analytics.averageExecutionTime}s</div>
                <div className="text-sm text-gray-600">Avg Execution Time</div>
              </div>
              <Clock className="w-8 h-8 text-purple-500" />
            </div>
          </div>

          <div className="bg-white border border-oracle-border rounded p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xl font-bold text-gray-800">{analytics.mostUsedTable}</div>
                <div className="text-sm text-gray-600">Most Used Table</div>
              </div>
              <BarChart3 className="w-8 h-8 text-orange-500" />
            </div>
          </div>
        </div>

        {/* Query Distribution */}
        <div className="bg-white border border-oracle-border rounded p-4">
          <h3 className="font-semibold text-gray-800 mb-3">Query Distribution</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>SELECT</span>
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '60%' }}></div>
              </div>
              <span className="text-gray-600">60%</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>INSERT</span>
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '25%' }}></div>
              </div>
              <span className="text-gray-600">25%</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>UPDATE</span>
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div className="bg-yellow-500 h-2 rounded-full" style={{ width: '10%' }}></div>
              </div>
              <span className="text-gray-600">10%</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>Other</span>
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div className="bg-gray-500 h-2 rounded-full" style={{ width: '5%' }}></div>
              </div>
              <span className="text-gray-600">5%</span>
            </div>
          </div>
        </div>

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