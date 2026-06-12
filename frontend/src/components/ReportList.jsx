import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import { FileText, ChevronRight } from 'lucide-react';

export default function ReportList({ reports, onSelectReport, selectedId }) {
  if (!reports || reports.length === 0) {
    return (
      <div className="glass-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '40px 20px', color: 'var(--text-secondary)' }}>
        <FileText size={48} style={{ opacity: 0.2, marginBottom: '16px' }} />
        <p>No reports generated yet.</p>
        <p style={{ fontSize: '13px', marginTop: '8px' }}>Trigger the pipeline to generate your first intelligence report.</p>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <FileText size={20} color="var(--accent-teal)" />
        <h3 style={{ fontSize: '16px' }}>Intelligence Archive</h3>
      </div>
      
      <div style={{ flex: 1, overflowY: 'auto', paddingRight: '4px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {reports.map((report) => {
          const isSelected = selectedId === report.id;
          
          let riskColor = 'var(--status-neutral)';
          let riskBg = 'rgba(245, 158, 11, 0.1)';
          if (report.risk_level === 'low') { riskColor = 'var(--status-positive)'; riskBg = 'rgba(16, 185, 129, 0.1)'; }
          if (report.risk_level === 'high') { riskColor = 'var(--status-negative)'; riskBg = 'rgba(239, 68, 68, 0.1)'; }
          if (report.risk_level === 'critical') { riskColor = '#dc2626'; riskBg = 'rgba(220, 38, 38, 0.2)'; }

          return (
            <div 
              key={report.id}
              onClick={() => onSelectReport(report.id)}
              style={{
                padding: '16px',
                borderRadius: '12px',
                background: isSelected ? 'rgba(255, 255, 255, 0.05)' : 'var(--bg-tertiary)',
                border: `1px solid ${isSelected ? 'var(--border-glow-focus)' : 'rgba(255, 255, 255, 0.05)'}`,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              className="glass-card-interactive"
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  {formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}
                </span>
                <span style={{ 
                  fontSize: '11px', 
                  fontWeight: 600, 
                  color: riskColor, 
                  background: riskBg,
                  padding: '2px 8px',
                  borderRadius: '12px',
                  textTransform: 'uppercase'
                }}>
                  {report.risk_level} Risk
                </span>
              </div>
              
              <h4 style={{ fontSize: '14px', marginBottom: '6px', color: isSelected ? '#fff' : 'var(--text-primary)', lineHeight: 1.4 }}>
                {report.title}
              </h4>
              
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {report.summary || 'No summary available.'}
              </p>
              
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
                <ChevronRight size={16} color={isSelected ? 'var(--accent-blue)' : 'var(--text-muted)'} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
