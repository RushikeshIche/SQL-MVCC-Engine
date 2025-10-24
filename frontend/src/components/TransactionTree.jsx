import React, { useState, useEffect, useRef } from 'react';
import { GitBranch, GitMerge, GitCommit, Circle, CheckCircle, XCircle } from 'lucide-react';

const TransactionTree = () => {
  const [transactions, setTransactions] = useState([]);
  const [treeData, setTreeData] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (transactions.length > 0) {
      generateTreeData();
    }
  }, [transactions]);

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket('ws://localhost:8000/ws/transactions');
      
      ws.onopen = () => {
        console.log('🔌 WebSocket connected for Transaction Tree');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === 'transaction_stats') {
          updateTransactions(message.data);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);
        setTimeout(() => {
          console.log('🔄 Attempting to reconnect...');
          connectWebSocket();
        }, 3000);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setIsConnected(false);
    }
  };

  const updateTransactions = (data) => {
    // Combine all transactions
    const allTransactions = [
      ...data.active_transactions.map(t => ({ ...t, state: 'ACTIVE' })),
      ...data.committed_transactions.map(t => ({ ...t, state: 'COMMITTED' })),
      ...data.aborted_transactions.map(t => ({ ...t, state: 'ABORTED' }))
    ];

    // Sort by transaction ID
    allTransactions.sort((a, b) => a.id - b.id);

    setTransactions(allTransactions);
  };

  const generateTreeData = () => {
    // Generate tree structure for visualization
    // Each transaction gets a node in the tree
    const tree = [];
    const lanes = {}; // Track which lane each transaction is in
    let nextLane = 0;

    transactions.forEach((txn, index) => {
      // Determine position in the tree
      let lane = nextLane;
      
      if (txn.state === 'ACTIVE') {
        // Active transactions branch out
        lane = nextLane;
        lanes[txn.id] = lane;
        nextLane++;
      } else {
        // Committed/aborted transactions merge back
        lane = lanes[txn.id] || 0;
        delete lanes[txn.id];
        if (Object.keys(lanes).length === 0) {
          nextLane = 0; // Reset lanes when no active transactions
        }
      }

      tree.push({
        id: txn.id,
        state: txn.state,
        isolationLevel: txn.isolation_level,
        lane: lane,
        index: index,
        startTime: txn.start_time,
        commitTime: txn.commit_time
      });
    });

    setTreeData(tree);
  };

  const getNodeColor = (state) => {
    switch (state) {
      case 'ACTIVE':
        return '#3b82f6'; // Blue
      case 'COMMITTED':
        return '#10b981'; // Green
      case 'ABORTED':
        return '#ef4444'; // Red
      default:
        return '#6b7280'; // Gray
    }
  };

  const getNodeIcon = (state) => {
    switch (state) {
      case 'ACTIVE':
        return <Circle className="w-5 h-5" fill="currentColor" />;
      case 'COMMITTED':
        return <CheckCircle className="w-5 h-5" />;
      case 'ABORTED':
        return <XCircle className="w-5 h-5" />;
      default:
        return <GitCommit className="w-5 h-5" />;
    }
  };

  const clearTransactionHistory = async () => {
    if (!confirm('Clear all transaction history? This will reset the visualization but not affect your data.')) {
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/transaction/clear-history', {
        method: 'POST'
      });
      
      if (response.ok) {
        setTransactions([]);
        setTreeData([]);
        console.log('✅ Transaction history cleared');
      }
    } catch (error) {
      console.error('Failed to clear history:', error);
      alert('Failed to clear transaction history. Check if backend is running.');
    }
  };

  const renderTree = () => {
    if (treeData.length === 0) {
      return (
        <div className="flex items-center justify-center h-96 text-slate-400">
          <div className="text-center">
            <GitBranch className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>Waiting for transactions...</p>
            <p className="text-sm mt-2">Start a transaction to see the tree visualization</p>
          </div>
        </div>
      );
    }

    const nodeSpacing = 90; // Horizontal spacing between nodes
    const rowSpacing = 100; // Vertical spacing between rows
    const laneSpacing = 70; // Spacing for branched lanes
    const startX = 60;
    const startY = 40;
    
    // Calculate nodes per row based on container width (assuming ~1000px usable width)
    const containerWidth = 1000;
    const nodesPerRow = Math.floor((containerWidth - startX * 2) / nodeSpacing);
    const actualNodesPerRow = Math.max(5, nodesPerRow); // Minimum 5 nodes per row
    
    // Calculate positions for snake pattern
    const positions = treeData.map((node, index) => {
      const rowIndex = Math.floor(index / actualNodesPerRow);
      const colIndex = index % actualNodesPerRow;
      
      // Snake pattern: reverse direction on odd rows
      const isReverseRow = rowIndex % 2 === 1;
      const adjustedColIndex = isReverseRow ? (actualNodesPerRow - 1 - colIndex) : colIndex;
      
      const x = startX + adjustedColIndex * nodeSpacing;
      const baseY = startY + rowIndex * rowSpacing;
      const y = baseY + node.lane * laneSpacing;
      
      return { x, y, rowIndex, colIndex, originalIndex: index };
    });

    const svgWidth = Math.min(containerWidth, startX * 2 + actualNodesPerRow * nodeSpacing);
    const maxRow = Math.max(...positions.map(p => p.rowIndex), 0);
    const maxLane = Math.max(...treeData.map(n => n.lane), 0);
    const svgHeight = startY + (maxRow + 1) * rowSpacing + maxLane * laneSpacing + 100;

    return (
      <div className="w-full overflow-y-auto border-2 border-slate-200 rounded-lg bg-white" style={{ maxHeight: '500px' }}>
        <svg
          ref={canvasRef}
          width={svgWidth}
          height={svgHeight}
          className="block w-full"
        >
          {/* Define arrow markers */}
          <defs>
            <marker
              id="arrowhead-blue"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 10 3, 0 6" fill="#3b82f6" />
            </marker>
            <marker
              id="arrowhead-green"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 10 3, 0 6" fill="#10b981" />
            </marker>
            <marker
              id="arrowhead-red"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 10 3, 0 6" fill="#ef4444" />
            </marker>
          </defs>

          {/* Draw connections between nodes in snake pattern */}
          {positions.map((pos, index) => {
            if (index === 0) return null;
            
            const node = treeData[index];
            const prevNode = treeData[index - 1];
            const prevPos = positions[index - 1];
            
            const color = getNodeColor(node.state);
            const arrowType = node.state === 'ACTIVE' ? 'blue' : node.state === 'COMMITTED' ? 'green' : 'red';
            
            // Check if wrapping to next row
            const isWrapping = pos.rowIndex !== prevPos.rowIndex;
            
            if (isWrapping) {
              // Draw connection from end of previous row to start of current row
              const midY = (prevPos.y + pos.y) / 2;
              const path = `M ${prevPos.x} ${prevPos.y} L ${prevPos.x} ${midY} L ${pos.x} ${midY} L ${pos.x} ${pos.y}`;
              
              return (
                <g key={`wrap-${node.id}`}>
                  <path
                    d={path}
                    stroke={color}
                    strokeWidth="2.5"
                    fill="none"
                    strokeLinecap="round"
                    markerEnd={`url(#arrowhead-${arrowType})`}
                  />
                </g>
              );
            } else {
              // Same row - check for branching
              if (node.lane > prevNode.lane) {
                // Branching out
                const baseY = startY + pos.rowIndex * rowSpacing;
                const midX = (prevPos.x + pos.x) / 2;
                const path = `M ${prevPos.x} ${prevPos.y} L ${midX} ${prevPos.y} L ${midX} ${baseY} L ${midX} ${pos.y} L ${pos.x} ${pos.y}`;
                
                return (
                  <g key={`branch-${node.id}`}>
                    <path
                      d={path}
                      stroke={color}
                      strokeWidth="2"
                      fill="none"
                      strokeLinecap="round"
                      markerEnd={`url(#arrowhead-${arrowType})`}
                    />
                  </g>
                );
              } else if (node.lane < prevNode.lane) {
                // Merging back
                const baseY = startY + pos.rowIndex * rowSpacing;
                const midX = (prevPos.x + pos.x) / 2;
                const path = `M ${prevPos.x} ${prevPos.y} L ${midX} ${prevPos.y} L ${midX} ${baseY} L ${midX} ${pos.y} L ${pos.x} ${pos.y}`;
                
                return (
                  <g key={`merge-${node.id}`}>
                    <path
                      d={path}
                      stroke={color}
                      strokeWidth="2"
                      fill="none"
                      strokeLinecap="round"
                      markerEnd={`url(#arrowhead-${arrowType})`}
                    />
                  </g>
                );
              } else {
                // Straight line
                return (
                  <line
                    key={`line-${node.id}`}
                    x1={prevPos.x}
                    y1={prevPos.y}
                    x2={pos.x}
                    y2={pos.y}
                    stroke={color}
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    markerEnd={`url(#arrowhead-${arrowType})`}
                  />
                );
              }
            }
          })}

          {/* Draw nodes */}
          {positions.map((pos, index) => {
            const node = treeData[index];
            const color = getNodeColor(node.state);

            return (
              <g key={`node-${node.id}`}>
                {/* Node circle */}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="14"
                  fill="white"
                  stroke={color}
                  strokeWidth="3"
                />
                
                {/* Inner dot for state */}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="7"
                  fill={color}
                  opacity="0.8"
                />

                {/* Transaction ID label */}
                <text
                  x={pos.x}
                  y={pos.y + 32}
                  textAnchor="middle"
                  fontSize="11"
                  fontWeight="bold"
                  fill={color}
                >
                  #{node.id}
                </text>

                {/* Isolation level label */}
                <text
                  x={pos.x}
                  y={pos.y + 47}
                  textAnchor="middle"
                  fontSize="9"
                  fill="#6b7280"
                >
                  {node.isolationLevel}
                </text>
              </g>
            );
          })}

          {/* Legend */}
          <g transform={`translate(${startX}, ${svgHeight - 60})`}>
            <text x="0" y="0" fontSize="12" fontWeight="bold" fill="#374151">Legend:</text>
            
            {/* Active */}
            <circle cx="10" cy="20" r="8" fill="white" stroke="#3b82f6" strokeWidth="2" />
            <circle cx="10" cy="20" r="4" fill="#3b82f6" opacity="0.8" />
            <text x="25" y="25" fontSize="11" fill="#374151">Active (Running)</text>

            {/* Committed */}
            <circle cx="150" cy="20" r="8" fill="white" stroke="#10b981" strokeWidth="2" />
            <circle cx="150" cy="20" r="4" fill="#10b981" opacity="0.8" />
            <text x="165" y="25" fontSize="11" fill="#374151">Committed (Success)</text>

            {/* Aborted */}
            <circle cx="310" cy="20" r="8" fill="white" stroke="#ef4444" strokeWidth="2" />
            <circle cx="310" cy="20" r="4" fill="#ef4444" opacity="0.8" />
            <text x="325" y="25" fontSize="11" fill="#374151">Aborted (Rolled Back)</text>
          </g>
        </svg>
      </div>
    );
  };

  return (
    <div className="h-full overflow-y-auto bg-slate-50">
      <div className="max-w-full mx-auto space-y-4 p-4 md:p-6">
        {/* Header */}
        <div className="flex items-start sm:items-center justify-between flex-wrap gap-3">
          <div className="flex items-start sm:items-center space-x-2 sm:space-x-3">
            <GitBranch className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600 flex-shrink-0 mt-1 sm:mt-0" />
            <div className="min-w-0">
              <h2 className="text-lg sm:text-2xl font-bold text-slate-800 break-words">Transaction Tree</h2>
              <p className="text-xs sm:text-sm text-slate-600 break-words">Git-like visualization</p>
            </div>
          </div>
          <div className="flex items-center space-x-2 sm:space-x-4 flex-shrink-0">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
              <span className="text-xs sm:text-sm text-slate-600 whitespace-nowrap">
                {isConnected ? 'Live' : 'Disconnected'}
              </span>
            </div>
            {transactions.length > 0 && (
              <button
                onClick={clearTransactionHistory}
                className="px-3 py-1.5 sm:px-4 sm:py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-xs sm:text-sm font-medium transition-colors flex items-center space-x-1 sm:space-x-2 whitespace-nowrap"
              >
                <XCircle className="w-3 h-3 sm:w-4 sm:h-4" />
                <span>Clear</span>
              </button>
            )}
          </div>
        </div>

        {/* Info Panel */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 sm:p-4">
          <div className="flex items-start space-x-2 sm:space-x-3">
            <GitMerge className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-xs sm:text-sm text-blue-800 min-w-0">
              <p className="font-semibold mb-1">How to Read:</p>
              <ul className="list-disc list-inside space-y-0.5 sm:space-y-1 ml-1 sm:ml-2">
                <li className="break-words"><strong>Branch Out</strong>: Transaction starts (BEGIN)</li>
                <li className="break-words"><strong>Merge Back</strong>: Transaction commits (green)</li>
                <li className="break-words"><strong>Abort</strong>: Transaction rolled back (red)</li>
                <li className="break-words"><strong>Parallel</strong>: Concurrent transactions</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Tree Visualization */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between p-3 sm:p-4 border-b border-slate-200">
            <h3 className="text-base sm:text-lg font-semibold text-slate-800">Transaction Flow</h3>
            <div className="text-xs sm:text-sm text-slate-600 whitespace-nowrap">
              {transactions.length} txn{transactions.length !== 1 ? 's' : ''}
            </div>
          </div>
          <div className="p-2 sm:p-4">
            {renderTree()}
          </div>
        </div>

        {/* Transaction Details */}
        {transactions.length > 0 && (
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
            <div className="flex items-center justify-between p-3 sm:p-4 border-b border-slate-200">
              <h3 className="text-base sm:text-lg font-semibold text-slate-800">Recent Transactions</h3>
              <span className="text-xs sm:text-sm text-slate-600 whitespace-nowrap">Last 6</span>
            </div>
            <div className="p-3 sm:p-4 overflow-hidden">
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 max-h-80 overflow-y-auto pr-1">
                {transactions.slice(-6).reverse().map(txn => (
                  <div
                    key={txn.id}
                    className={`p-3 rounded-lg border-2 min-w-0 ${
                      txn.state === 'ACTIVE'
                        ? 'bg-blue-50 border-blue-300'
                        : txn.state === 'COMMITTED'
                        ? 'bg-green-50 border-green-300'
                        : 'bg-red-50 border-red-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2 gap-2">
                      <span className="font-mono font-bold text-xs sm:text-sm truncate">TXN #{txn.id}</span>
                      <span className={`px-1.5 py-0.5 sm:px-2 sm:py-1 rounded text-xs font-semibold whitespace-nowrap flex-shrink-0 ${
                        txn.state === 'ACTIVE'
                          ? 'bg-blue-200 text-blue-800'
                          : txn.state === 'COMMITTED'
                          ? 'bg-green-200 text-green-800'
                          : 'bg-red-200 text-red-800'
                      }`}>
                        {txn.state}
                      </span>
                    </div>
                    <div className="text-xs text-slate-600 space-y-0.5">
                      <div className="truncate">
                        <span className="font-semibold">Isolation:</span> {txn.isolation_level}
                      </div>
                      <div className="truncate">
                        <span className="font-semibold">Started:</span> {new Date(txn.start_time).toLocaleTimeString()}
                      </div>
                      {txn.commit_time && (
                        <div className="truncate">
                          <span className="font-semibold">Done:</span> {new Date(txn.commit_time).toLocaleTimeString()}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TransactionTree;

