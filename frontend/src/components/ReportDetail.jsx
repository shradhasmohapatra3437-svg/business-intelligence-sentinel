import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { getReport } from '../lib/api';
import { Loader, Download } from 'lucide-react';

export default function ReportDetail({ reportId }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (reportId) {
      setLoading(true);
      getReport(reportId).then(data => {
        setReport(data);
        setLoading(false);
      }).catch(err => {
        console.error(err);
        setLoading(false);
      });
    }
  }, [reportId]);

  if (loading) {
    return (
      <div className="glass-panel" style={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <Loader className="animate-spin" size={32} color="var(--accent-blue)" />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="glass-panel" style={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', color: 'var(--text-muted)' }}>
        Select a report from the archive to view details.
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        <div>
          <h2 style={{ fontSize: '20px', color: '#fff' }}>{report.title}</h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Generated {new Date(report.created_at).toLocaleString()}
          </p>
        </div>
        <button style={{ background: 'transparent', border: '1px solid var(--border-glow)', padding: '6px 12px', fontSize: '13px', display: 'flex', gap: '6px', alignItems: 'center' }}>
          <Download size={14} /> Export
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', paddingRight: '12px' }}>
        <div className="markdown-body">
          <ReactMarkdown>{report.content_markdown}</ReactMarkdown>
        </div>
        
        {/* Source attribution block */}
        <div style={{ marginTop: '40px', padding: '16px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <h4 style={{ fontSize: '14px', marginBottom: '8px', color: 'var(--text-secondary)' }}>Data Sources & Models</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {report.sources_used?.map((src, i) => (
              <span key={i} style={{ fontSize: '11px', background: 'var(--bg-tertiary)', padding: '4px 8px', borderRadius: '4px', color: 'var(--text-muted)' }}>
                {src}
              </span>
            ))}
          </div>
          <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-muted)' }}>
            Tokens consumed: {report.token_usage?.total_tokens?.toLocaleString() || 'Unknown'} 
            (Prompt: {report.token_usage?.prompt_tokens?.toLocaleString() || 0} | 
            Completion: {report.token_usage?.completion_tokens?.toLocaleString() || 0})
          </div>
        </div>
      </div>
    </div>
  );
}
