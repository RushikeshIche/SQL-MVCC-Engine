import React, { useState, useEffect } from 'react';
import { Database, History, BarChart3, List } from 'lucide-react';
import QueryEditor from './components/QueryEditor';
import QueryHistory from './components/QueryHistory';
import SchemaExplorer from './components/SchemaExplorer';
import AnalyticsPanel from './components/AnalyticsPanel';
import TransactionPanel from './components/TransactionPanel';
import ResultTable from './components/ResultTable';
import Transactions from './components/Transactions';

function App() {
  const [activeTab, setActiveTab] = useState('editor');
  const [queryResult, setQueryResult] = useState(null);
  const [tables, setTables] = useState([]);
  const [activeTransaction, setActiveTransaction] = useState(null);
  const [queryHistory, setQueryHistory] = useState([]);
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    fetchTables();
  }, []);

  const fetchTables = async () => {
    try {
      const response = await fetch('http://localhost:8000/tables');
      const data = await response.json();
      setTables(data);
    } catch (error) {
      console.error('Failed to fetch tables:', error);
    }
  };

  const handleQueryResult = (query, result) => {
    setQueryResult(result);
    setQueryHistory(prevHistory => [
      {
        id: prevHistory.length + 1,
        query,
        ...result,
        timestamp: new Date().toISOString(),
      },
      ...prevHistory
    ]);
    if (result.success) {
      fetchTables();
    }
  };

  const handleTransactionUpdate = (transaction) => {
    // Record transaction lifecycle events (start / end) for the Transactions tab
    const now = new Date().toISOString();
    // transaction may be:
    // - null -> no active transaction
    // - { id, status: 'active'|'ended'|'aborted', isolationLevel? }

    if (!transaction) {
      // Clearing active transaction on backend-side null; mark previous as ended
      if (activeTransaction) {
        const prevId = activeTransaction.id;
        setTransactions(prev => prev.map(t => t.id === prevId ? ({
          ...t,
          end: now,
          status: 'ended',
          duration: t.start ? ((new Date(now) - new Date(t.start)) / 1000) : undefined,
        }) : t));
      }
      setActiveTransaction(null);
      return;
    }

    // If update contains status only for an existing active transaction
    if (transaction && transaction.status && activeTransaction && transaction.id === activeTransaction.id) {
      const status = transaction.status;
      if (status === 'ended') {
        setTransactions(prev => prev.map(t => t.id === transaction.id ? ({
          ...t,
          end: now,
          status: 'ended',
          duration: t.start ? ((new Date(now) - new Date(t.start)) / 1000) : undefined,
        }) : t));
        setActiveTransaction(null);
        return;
      }
      if (status === 'aborted') {
        setTransactions(prev => prev.map(t => t.id === transaction.id ? ({
          ...t,
          end: now,
          status: 'aborted',
          duration: t.start ? ((new Date(now) - new Date(t.start)) / 1000) : undefined,
        }) : t));
        setActiveTransaction(null);
        return;
      }
      // If status is 'active' just ensure we have it recorded
    }

    // If a transaction object arrives and there was no active transaction -> record start
    if (transaction && !activeTransaction) {
      setTransactions(prev => [
        {
          id: transaction.id,
          start: now,
          end: null,
          status: transaction.status || 'active',
          isolationLevel: transaction.isolationLevel || null,
        },
        ...prev,
      ]);
      setActiveTransaction(transaction);
      return;
    }

    // If a new transaction arrives while another is active (rare) treat as new start and close previous
    if (transaction && activeTransaction && transaction.id !== activeTransaction.id) {
      // Mark previous as ended
      const prevId = activeTransaction.id;
      setTransactions(prev => prev.map(t => t.id === prevId ? ({
        ...t,
        end: now,
        status: 'ended',
        duration: t.start ? ((new Date(now) - new Date(t.start)) / 1000) : undefined,
      }) : t));

      // Add new
      setTransactions(prev => [
        {
          id: transaction.id,
          start: now,
          end: null,
          status: transaction.status || 'active',
          isolationLevel: transaction.isolationLevel || null,
        },
        ...prev,
      ]);
      setActiveTransaction(transaction);
      return;
    }

    // Default: set activeTransaction to incoming object
    setActiveTransaction(transaction);
  };

  return (
    <div className="h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="bg-slate-900 text-white px-4 py-2 border-b border-slate-300">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Database className="w-6 h-6 text-blue-400" />
            <h1 className="text-lg font-bold">SQL MVCC Engine</h1>
            <span className="text-sm text-slate-300">Multi-Version Concurrency Control Database</span>
          </div>
          <TransactionPanel 
            onTransactionUpdate={handleTransactionUpdate}
            activeTransaction={activeTransaction}
          />
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Schema Explorer */}
        <div className="w-64 bg-white border-r border-slate-300 flex flex-col">
          <div className="p-3 border-b border-slate-300 bg-slate-50">
            <h2 className="font-semibold text-sm text-slate-700 flex items-center">
              <Database className="w-4 h-4 mr-2" />
              Schema Explorer
            </h2>
          </div>
          <div className="flex-1 overflow-auto">
            <SchemaExplorer tables={tables} />
          </div>
        </div>

        {/* Main Area */}
        <div className="flex-1 flex flex-col">
          {/* Top Section - Tabs */}
          <div className="border-b border-slate-300 bg-white">
              <div className="flex items-center justify-between">
                <div className="flex">
                  {[
                    { id: 'editor', label: 'Query Editor', icon: BarChart3 },
                    { id: 'history', label: 'History & Analytics', icon: History },
                  ].map(tab => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center px-4 py-2 border-b-2 text-sm font-medium ${
                        activeTab === tab.id
                          ? 'border-blue-600 text-blue-600'
                          : 'border-transparent text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      <tab.icon className="w-4 h-4 mr-2" />
                      {tab.label}
                    </button>
                  ))}
                </div>

                {/* Right-aligned tab(s) */}
                <div className="flex">
                  <button
                    onClick={() => setActiveTab('transactions')}
                    className={`flex items-center px-4 py-2 border-b-2 text-sm font-medium ${
                      activeTab === 'transactions'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    <List className="w-4 h-4 mr-2" />
                    Transactions
                  </button>
                </div>
              </div>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden">
            {activeTab === 'editor' && (
              <QueryEditor 
                onQueryResult={handleQueryResult}
                activeTransaction={activeTransaction}
              />
            )}
            {activeTab === 'history' && (
              <div className="flex h-full">
                <div className="w-1/2 border-r border-slate-300">
                  <QueryHistory history={queryHistory} />
                </div>
                <div className="w-1/2">
                  <AnalyticsPanel history={queryHistory} />
                </div>
              </div>
            )}
            {activeTab === 'transactions' && (
              <div className="flex h-full">
                <div className="w-full">
                  <Transactions transactions={transactions} />
                </div>
              </div>
            )}
          </div>

          {/* Results Panel */}
          {queryResult && activeTab === 'editor' && (
            <div className="border-t border-slate-300 bg-white">
              <ResultTable result={queryResult} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;