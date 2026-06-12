import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import AgentStatus from './components/AgentStatus';
import SentimentChart from './components/SentimentChart';
import ReportList from './components/ReportList';
import ReportDetail from './components/ReportDetail';
import ConfigPanel from './components/ConfigPanel';
import ManualTrigger from './components/ManualTrigger';
import RunHistory from './components/RunHistory';
import CostTracker from './components/CostTracker';
import { getReports, getSentimentHistory, getConfig, getStats, getHealth } from './lib/api';
import { Shield, RefreshCw, AlertOctagon } from 'lucide-react';

export default function App() {
  const [reports, setReports] = useState([]);
  const [tickers, setTickers] = useState([]);
  const [history, setHistory] = useState(null);
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  
  const [selectedReportId, setSelectedReportId] = useState(null);
  
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const loadDashboardData = async () => {
    try {
      const [reportsData, historyData, configData, statsData, healthData] = await Promise.all([
        getReports(),
        getSentimentHistory(),
        getConfig(),
        getStats(),
        getHealth()
      ]);
      
      setReports(reportsData);
      if (reportsData.length > 0 && !selectedReportId) {
        setSelectedReportId(reportsData[0].id);
      }
      
      setHistory(historyData.history);
      setTickers(configData.tickers);
      setStats(statsData);
      setHealth(healthData);
      setError('');
    } catch (e) {
      console.error(e);
      setError('Could not connect to the Sentinel backend server. Please verify it is running.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleRefresh = async () => {
    setIsLoading(true);
    await loadDashboardData();
  };

  if (isLoading && reports.length === 0) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', gap: '16px' }}>
        <Shield className="animate-spin" style={{ width: '64px', height: '64px', color: 'var(--accent-blue)' }} />
        <p style={{ color: 'var(--text-secondary)', fontSize: '16px', letterSpacing: '0.05em' }} className="animate-pulse">
          Initializing Sentinel Operations Control...
        </p>
      </div>
    );
  }

  return (
    <div style={{ paddingBottom: '48px' }}>
      {/* Top Floating Control Bar */}
      <div style={{ background: 'rgba(9, 13, 22, 0.8)', borderBottom: '1px solid rgba(255, 255, 255, 0.05)', backdropFilter: 'blur(8px)', position: 'sticky', top: 0, zIndex: 100 }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '13px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: health?.status === 'healthy' ? 'var(--status-positive)' : 'var(--status-negative)' }}></span>
            Secured Sandbox Environment
          </span>
          
          <button 
            onClick={handleRefresh}
            style={{
              background: 'transparent',
              border: '1px solid var(--border-glow)',
              color: 'var(--text-secondary)',
              padding: '6px 14px',
              borderRadius: '8px',
              fontSize: '13px',
              boxShadow: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
            className="glass-card-interactive"
          >
            <RefreshCw style={{ width: '12px', height: '12px' }} />
            Sync Dashboard
          </button>
        </div>
      </div>

      <div className="dashboard-grid">
        
        {/* Error Alert Box */}
        {error && (
          <div className="col-full" style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--status-negative)', background: 'rgba(239, 68, 68, 0.08)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
            <AlertOctagon style={{ flexShrink: 0 }} />
            <div>
              <p style={{ fontWeight: 600 }}>Connection Error</p>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>{error}</p>
            </div>
          </div>
        )}

        <AgentStatus stats={stats} health={health} />
        
        <Dashboard reports={reports} tickers={tickers} history={history} />

        <SentimentChart history={history} tickers={tickers} />

        <ConfigPanel 
          tickers={tickers} 
          onConfigUpdated={async (updatedTickers) => {
            setTickers(updatedTickers);
            await handleRefresh();
          }} 
        />
        
        {/* Row 3 */}
        <div className="col-4" style={{ height: '600px' }}>
          <ReportList reports={reports} selectedId={selectedReportId} onSelectReport={setSelectedReportId} />
        </div>
        
        <div className="col-8" style={{ height: '600px' }}>
          <ReportDetail reportId={selectedReportId} />
        </div>

        {/* Row 4 */}
        <ManualTrigger onPipelineSuccess={handleRefresh} />
        <CostTracker stats={stats} />
        <RunHistory />

      </div>

      <footer style={{ maxWidth: '1400px', margin: '40px auto 0 auto', padding: '0 24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
        <p>© 2026 Business Intelligence Sentinel. Systems Integration Portfolio Case.</p>
        <p style={{ marginTop: '4px', fontSize: '12px', color: 'rgba(255,255,255,0.15)' }}>Powered by PyTorch, Hugging Face Transformers, FastAPI, and React.</p>
      </footer>
    </div>
  );
}
