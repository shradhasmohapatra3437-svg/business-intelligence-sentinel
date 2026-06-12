import React, { useState } from 'react';
import { Plus, X, List, AlertCircle } from 'lucide-react';
import { updateConfig } from '../lib/api';

export default function WatchlistConfig({ tickers, onConfigUpdated }) {
  const [newTicker, setNewTicker] = useState('');
  const [currentTickers, setCurrentTickers] = useState(tickers || []);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Sync state if tickers prop changes
  React.useEffect(() => {
    setCurrentTickers(tickers || []);
  }, [tickers]);

  const handleAdd = (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    const clean = newTicker.trim().toUpperCase();
    if (!clean) return;
    
    if (currentTickers.includes(clean)) {
      setError(`${clean} is already in the watchlist.`);
      return;
    }
    
    setCurrentTickers([...currentTickers, clean]);
    setNewTicker('');
  };

  const handleRemove = (tickerToRemove) => {
    setError('');
    setSuccess(false);
    setCurrentTickers(currentTickers.filter(t => t !== tickerToRemove));
  };

  const handleSave = async () => {
    if (currentTickers.length === 0) {
      setError('Watchlist must contain at least one ticker.');
      return;
    }
    
    setIsSaving(true);
    setError('');
    setSuccess(false);
    
    try {
      await updateConfig(currentTickers);
      setSuccess(true);
      if (onConfigUpdated) {
        onConfigUpdated(currentTickers);
      }
      setTimeout(() => setSuccess(false), 3000);
    } catch (e) {
      setError(e.message || 'Failed to update watchlist config.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="glass-panel col-4" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h3 style={{ fontSize: '18px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <List style={{ color: 'var(--accent-blue)', width: '20px', height: '20px' }} />
          Sentinel Watchlist Config
        </h3>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Manage the stock tickers tracked by the deep learning pipeline</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1 }}>
        {/* Active Tickers Tags List */}
        <div>
          <p style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>Active Watchlist</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', minHeight: '80px', padding: '12px', background: 'rgba(255,255,255,0.02)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.05)' }}>
            {currentTickers.length > 0 ? (
              currentTickers.map(ticker => (
                <span 
                  key={ticker} 
                  style={{
                    background: 'rgba(59, 130, 246, 0.1)',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    color: '#60a5fa',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    fontSize: '13px',
                    fontWeight: 600,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  {ticker}
                  <button 
                    onClick={() => handleRemove(ticker)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#9ca3af',
                      padding: 0,
                      boxShadow: 'none',
                      display: 'flex',
                      alignItems: 'center',
                      cursor: 'pointer'
                    }}
                  >
                    <X style={{ width: '12px', height: '12px' }} />
                  </button>
                </span>
              ))
            ) : (
              <span style={{ color: 'var(--text-muted)', fontSize: '13px', display: 'flex', alignItems: 'center' }}>No tickers added yet</span>
            )}
          </div>
        </div>

        {/* Add Ticker Form */}
        <form onSubmit={handleAdd} style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            placeholder="e.g. AMZN, TSLA"
            value={newTicker}
            onChange={(e) => setNewTicker(e.target.value)}
            style={{ textTransform: 'uppercase' }}
          />
          <button 
            type="submit"
            style={{
              padding: '10px 14px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: 'none'
            }}
          >
            <Plus style={{ width: '18px', height: '18px' }} />
          </button>
        </form>

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--status-negative)', fontSize: '13px', background: 'rgba(239, 68, 68, 0.1)', padding: '10px', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
            <AlertCircle style={{ width: '16px', height: '16px', flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div style={{ color: 'var(--status-positive)', fontSize: '13px', background: 'rgba(16, 185, 129, 0.1)', padding: '10px', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
            Watchlist configuration updated successfully!
          </div>
        )}
      </div>

      <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.05)', paddingTop: '16px' }}>
        <button 
          onClick={handleSave} 
          disabled={isSaving}
          style={{ width: '100%' }}
        >
          {isSaving ? 'Saving Watchlist...' : 'Save Watchlist'}
        </button>
      </div>
    </div>
  );
}
