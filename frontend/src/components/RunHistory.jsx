import React, { useState, useEffect } from 'react';
import { getRuns } from '../lib/api';
import { Activity, Check, X, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export default function RunHistory() {
  const [runs, setRuns] = useState([]);

  useEffect(() => {
    getRuns(10).then(setRuns).catch(console.error);
  }, []);

  return (
    <div className="glass-panel col-6">
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
        <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.1)' }}>
          <Activity size={20} color="var(--accent-blue)" />
        </div>
        <div>
          <h3 style={{ fontSize: '18px' }}>Execution Logs</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Recent pipeline activity</p>
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-muted)' }}>
              <th style={{ textAlign: 'left', padding: '8px 4px', fontWeight: 500 }}>Time</th>
              <th style={{ textAlign: 'left', padding: '8px 4px', fontWeight: 500 }}>Type</th>
              <th style={{ textAlign: 'left', padding: '8px 4px', fontWeight: 500 }}>Status</th>
              <th style={{ textAlign: 'right', padding: '8px 4px', fontWeight: 500 }}>Duration</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '10px 4px', color: 'var(--text-primary)' }}>
                  {run.started_at ? formatDistanceToNow(new Date(run.started_at), { addSuffix: true }) : 'Unknown'}
                </td>
                <td style={{ padding: '10px 4px', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                  {run.trigger_type}
                </td>
                <td style={{ padding: '10px 4px' }}>
                  {run.status === 'complete' && <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--status-positive)' }}><Check size={14}/> Success</span>}
                  {run.status === 'failed' && <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--status-negative)' }}><X size={14}/> Failed</span>}
                  {run.status === 'running' && <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--accent-blue)' }}><Clock size={14}/> Running</span>}
                </td>
                <td style={{ padding: '10px 4px', textAlign: 'right', color: 'var(--text-muted)' }}>
                  {run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : '-'}
                </td>
              </tr>
            ))}
            {runs.length === 0 && (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>No run history available.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
