import React, { useState } from 'react';
import { updateConfig } from '../lib/api';
import { Settings, Save, AlertCircle } from 'lucide-react';

export default function ConfigPanel({ tickers, onConfigUpdated }) {
  const [tickerInput, setTickerInput] = useState(tickers ? tickers.join(', ') : '');
  const [status, setStatus] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    setStatus('');
    try {
      const tickerArray = tickerInput.split(',').map(t => t.trim()).filter(Boolean);
      const res = await updateConfig({ tickers: tickerArray });
      
      if (res.rejected && res.rejected.length > 0) {
        setStatus(`Saved. Rejected invalid tickers: ${res.rejected.join(', ')}`);
      } else {
        setStatus('Configuration saved successfully.');
      }
      
      // Update local input to reflect only valid saved tickers
      if (res.saved) {
        setTickerInput(res.saved.join(', '));
      }
      
      if (onConfigUpdated) onConfigUpdated(res.saved || []);
      
    } catch (e) {
      setStatus(`Error: ${e.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="glass-panel col-4" style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
        <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(20, 184, 166, 0.1)' }}>
          <Settings size={20} color="var(--accent-teal)" />
        </div>
        <div>
          <h3 style={{ fontSize: '18px' }}>Pipeline Config</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Manage tracked assets</p>
        </div>
      </div>

      <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
          Watchlist Tickers (comma separated)
        </label>
        <input 
          type="text" 
          value={tickerInput}
          onChange={(e) => setTickerInput(e.target.value)}
          placeholder="AAPL, MSFT, NVDA"
          style={{ marginBottom: '8px' }}
        />
        <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '24px' }}>
          Tickers are validated against yfinance. Invalid symbols will be rejected.
        </p>
        
        {/* Mock inputs for other config items just for UI completeness */}
        <label style={{ display: 'block', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px', opacity: 0.5 }}>
          Additional Keywords (Read-only)
        </label>
        <input type="text" value="earnings, merger, FDA" disabled style={{ opacity: 0.5, marginBottom: '24px' }} />
      </div>

      <div>
        {status && (
          <div style={{ 
            fontSize: '12px', 
            padding: '8px', 
            marginBottom: '16px', 
            borderRadius: '6px',
            background: status.includes('Error') || status.includes('Rejected') ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
            color: status.includes('Error') || status.includes('Rejected') ? 'var(--status-negative)' : 'var(--status-positive)',
            display: 'flex', gap: '6px', alignItems: 'center'
          }}>
            <AlertCircle size={14} /> {status}
          </div>
        )}
        
        <button 
          onClick={handleSave} 
          disabled={isSaving}
          style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '8px' }}
        >
          <Save size={18} />
          {isSaving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  );
}
