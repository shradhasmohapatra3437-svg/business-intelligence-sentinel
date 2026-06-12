import React from 'react';
import { Database, Zap } from 'lucide-react';

export default function CostTracker({ stats }) {
  const history = stats?.token_usage_history || [];
  
  // Calculate totals
  const totalTokens = history.reduce((sum, item) => sum + item.total_tokens, 0);
  
  // Rough estimate: Groq Llama 3 70B is free, but if it were paid (e.g. $0.59/1M tokens prompt, $0.79/1M completion)
  // We'll show a "Value Saved" metric instead of cost, since we are using free tiers.
  const valueSaved = (totalTokens / 1000000) * 0.70;

  return (
    <div className="glass-panel col-6">
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
        <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.1)' }}>
          <Database size={20} color="var(--status-positive)" />
        </div>
        <div>
          <h3 style={{ fontSize: '18px' }}>Token Usage & Value</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Resource monitoring for LLM operations</p>
        </div>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
        <div style={{ background: 'var(--bg-tertiary)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-glow)' }}>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Tokens (Last 14)</p>
          <h2 style={{ fontSize: '28px', color: 'var(--text-primary)', marginTop: '4px' }}>{totalTokens.toLocaleString()}</h2>
        </div>
        <div style={{ background: 'var(--bg-tertiary)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Estimated Value Saved</p>
          <h2 style={{ fontSize: '28px', color: 'var(--status-positive)', marginTop: '4px' }}>${valueSaved.toFixed(4)}</h2>
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-muted)' }}>
              <th style={{ textAlign: 'left', padding: '8px 4px', fontWeight: 500 }}>Run Date</th>
              <th style={{ textAlign: 'right', padding: '8px 4px', fontWeight: 500 }}>Prompt</th>
              <th style={{ textAlign: 'right', padding: '8px 4px', fontWeight: 500 }}>Completion</th>
              <th style={{ textAlign: 'right', padding: '8px 4px', fontWeight: 500 }}>Model</th>
            </tr>
          </thead>
          <tbody>
            {history.slice(0, 5).map((row, i) => (
              <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '10px 4px' }}>{row.date}</td>
                <td style={{ padding: '10px 4px', textAlign: 'right', color: 'var(--text-secondary)' }}>{row.prompt_tokens.toLocaleString()}</td>
                <td style={{ padding: '10px 4px', textAlign: 'right', color: 'var(--accent-blue)' }}>{row.completion_tokens.toLocaleString()}</td>
                <td style={{ padding: '10px 4px', textAlign: 'right' }}>
                  <span style={{ fontSize: '11px', background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                    {row.model.split('/')[0]}
                  </span>
                </td>
              </tr>
            ))}
            {history.length === 0 && (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>No recent usage data.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
