import React from 'react';
import { Activity, TrendingUp, AlertTriangle, FileText } from 'lucide-react';

export default function Dashboard({ reports, tickers, history }) {
  // Compute some quick aggregate metrics
  const latestReport = reports && reports.length > 0 ? reports[0] : null;
  const totalTracked = tickers ? tickers.length : 0;
  
  let riskColor = 'var(--status-neutral)';
  if (latestReport?.risk_level === 'low') riskColor = 'var(--status-positive)';
  if (latestReport?.risk_level === 'high') riskColor = 'var(--status-negative)';
  if (latestReport?.risk_level === 'critical') riskColor = '#dc2626';

  return (
    <>
      <div className="glass-panel col-3">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.05)' }}>
            <Activity size={20} color="var(--text-secondary)" />
          </div>
          <h3 style={{ fontSize: '15px' }}>Current Risk Level</h3>
        </div>
        <p style={{ fontSize: '28px', color: riskColor, textTransform: 'capitalize', fontWeight: 600 }}>
          {latestReport ? latestReport.risk_level : 'Unknown'}
        </p>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>Based on latest pipeline run</p>
      </div>

      <div className="glass-panel col-3">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.1)' }}>
            <TrendingUp size={20} color="var(--accent-blue)" />
          </div>
          <h3 style={{ fontSize: '15px' }}>Tracked Assets</h3>
        </div>
        <p style={{ fontSize: '28px', color: 'var(--text-primary)' }}>{totalTracked}</p>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>Active Watchlist Entities</p>
      </div>

      <div className="glass-panel col-3">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.1)' }}>
            <AlertTriangle size={20} color="var(--status-neutral)" />
          </div>
          <h3 style={{ fontSize: '15px' }}>Material Events</h3>
        </div>
        <p style={{ fontSize: '28px', color: 'var(--text-primary)' }}>
          {latestReport?.key_findings?.filter(f => f.finding?.includes('8-K')).length || 0}
        </p>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>Recent 8-K filings detected</p>
      </div>

      <div className="glass-panel col-3">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(20, 184, 166, 0.1)' }}>
            <FileText size={20} color="var(--accent-teal)" />
          </div>
          <h3 style={{ fontSize: '15px' }}>Reports Archived</h3>
        </div>
        <p style={{ fontSize: '28px', color: 'var(--text-primary)' }}>{reports ? reports.length : 0}</p>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>Total generated reports</p>
      </div>
    </>
  );
}
