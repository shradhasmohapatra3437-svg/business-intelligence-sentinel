import React from 'react';
import { Shield, CheckCircle, AlertOctagon, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export default function AgentStatus({ stats, health }) {
  const isHealthy = health?.status === 'healthy';
  const lastRun = stats?.token_usage_history?.[0]?.date;
  
  let statusColor = 'var(--status-negative)';
  let StatusIcon = AlertOctagon;
  let statusText = 'System Offline';
  
  if (isHealthy) {
    statusColor = 'var(--status-positive)';
    StatusIcon = CheckCircle;
    statusText = 'System Healthy';
  }

  return (
    <div className="glass-panel col-full" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', padding: '20px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ position: 'relative' }}>
          <Shield style={{ color: statusColor, width: '36px', height: '36px' }} />
          {isHealthy && (
            <span style={{
              position: 'absolute',
              top: '-2px',
              right: '-2px',
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: statusColor,
              boxShadow: `0 0 10px ${statusColor}`,
            }} className="animate-pulse" />
          )}
        </div>
        <div>
          <h2 style={{ fontSize: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            Agent Status: <span style={{ color: statusColor }}>{statusText}</span>
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
            FinBERT: {health?.models?.finbert === 'loaded' ? 'Loaded' : 'Fallback'} • 
            DeBERTa: {health?.models?.absa === 'loaded' ? 'Loaded' : 'Fallback'}
          </p>
        </div>
      </div>
      
      <div style={{ display: 'flex', gap: '24px' }}>
        <div>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Last Run</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px', fontSize: '15px' }}>
            <Clock size={16} color="var(--text-secondary)" />
            {lastRun ? formatDistanceToNow(new Date(lastRun), { addSuffix: true }) : 'Never'}
          </div>
        </div>
        
        <div>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Success Rate</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px', fontSize: '15px' }}>
            <span style={{ color: stats?.success_rate > 90 ? 'var(--status-positive)' : 'var(--status-neutral)' }}>
              {stats?.success_rate || 0}%
            </span>
          </div>
        </div>
        
        <div>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Avg Duration</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px', fontSize: '15px' }}>
            {stats?.avg_duration_seconds || 0}s
          </div>
        </div>
      </div>
    </div>
  );
}
