import React, { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import { TrendingUp, BarChart2 } from 'lucide-react';

export default function SentimentChart({ history, tickers }) {
  const [viewMode, setViewMode] = useState('timeseries'); // timeseries | aspects

  // Format data for Recharts
  const chartData = useMemo(() => {
    if (!history) return [];

    if (viewMode === 'timeseries') {
      // Group by date, average sentiment per ticker
      const dateMap = {};
      
      Object.keys(history).forEach(ticker => {
        history[ticker].forEach(entry => {
          const d = entry.date || new Date().toISOString().split('T')[0];
          if (!dateMap[d]) {
            dateMap[d] = { date: d };
            tickers?.forEach(t => dateMap[d][t] = null);
          }
          // Simple average for the day if multiple runs
          if (dateMap[d][ticker] === null) {
            dateMap[d][ticker] = entry.sentiment_score;
          } else {
            dateMap[d][ticker] = (dateMap[d][ticker] + entry.sentiment_score) / 2;
          }
        });
      });
      
      return Object.values(dateMap).sort((a, b) => new Date(a.date) - new Date(b.date));
    } else {
      // Aggregate Aspect data from all history (latest few runs)
      const aspectMap = {};
      
      Object.keys(history).forEach(ticker => {
        history[ticker].forEach(entry => {
          if (entry.absa_data) {
            Object.entries(entry.absa_data).forEach(([aspect, score]) => {
              if (!aspectMap[aspect]) aspectMap[aspect] = { aspect, total: 0, count: 0 };
              aspectMap[aspect].total += score;
              aspectMap[aspect].count += 1;
            });
          }
        });
      });
      
      return Object.values(aspectMap)
        .map(a => ({ aspect: a.aspect, score: a.total / a.count }))
        .sort((a, b) => b.score - a.score)
        .slice(0, 10); // Top 10 aspects
    }
  }, [history, tickers, viewMode]);

  // Generate colors for tickers
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4', '#ec4899'];

  return (
    <div className="glass-panel col-full" style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <TrendingUp size={24} color="var(--accent-blue)" />
          <div>
            <h2 style={{ fontSize: '18px' }}>Deep Learning Sentiment Signals</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '4px' }}>
              {viewMode === 'timeseries' 
                ? 'Document-level FinBERT scores over time (-1 to 1)' 
                : 'DeBERTa Aspect-Based Sentiment Analysis (ABSA) extracted entities'}
            </p>
          </div>
        </div>
        
        <div style={{ display: 'flex', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '4px' }}>
          <button 
            onClick={() => setViewMode('timeseries')}
            style={{ 
              background: viewMode === 'timeseries' ? 'var(--bg-tertiary)' : 'transparent',
              color: viewMode === 'timeseries' ? '#fff' : 'var(--text-muted)',
              padding: '6px 12px', fontSize: '13px', border: 'none', boxShadow: 'none'
            }}
          >
            Time Series
          </button>
          <button 
            onClick={() => setViewMode('aspects')}
            style={{ 
              background: viewMode === 'aspects' ? 'var(--bg-tertiary)' : 'transparent',
              color: viewMode === 'aspects' ? '#fff' : 'var(--text-muted)',
              padding: '6px 12px', fontSize: '13px', border: 'none', boxShadow: 'none'
            }}
          >
            Aspect Breakdown
          </button>
        </div>
      </div>

      <div style={{ height: '350px', width: '100%' }}>
        {chartData.length === 0 ? (
          <div style={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', color: 'var(--text-muted)' }}>
            No sentiment data available for the selected period.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            {viewMode === 'timeseries' ? (
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="var(--text-muted)" fontSize={12} domain={[-1, 1]} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', border: '1px solid var(--border-glow)', borderRadius: '8px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)' }}
                  itemStyle={{ color: '#fff', fontSize: '13px' }}
                  labelStyle={{ color: 'var(--text-muted)', marginBottom: '4px' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', color: 'var(--text-secondary)', paddingTop: '10px' }} />
                <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" />
                {tickers?.map((ticker, index) => (
                  <Bar key={ticker} dataKey={ticker} name={ticker} fill={colors[index % colors.length]} radius={[4, 4, 0, 0]} maxBarSize={40} />
                ))}
              </BarChart>
            ) : (
              <BarChart layout="vertical" data={chartData} margin={{ top: 10, right: 30, left: 40, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                <XAxis type="number" stroke="var(--text-muted)" fontSize={12} domain={[-1, 1]} tickLine={false} axisLine={false} />
                <YAxis dataKey="aspect" type="category" stroke="var(--text-secondary)" fontSize={12} tickLine={false} axisLine={false} width={120} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', border: '1px solid var(--border-glow)', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff', fontSize: '13px' }}
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                />
                <ReferenceLine x={0} stroke="rgba(255,255,255,0.2)" />
                <Bar dataKey="score" name="ABSA Score" radius={[0, 4, 4, 0]} barSize={24}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.score > 0 ? 'var(--status-positive)' : 'var(--status-negative)'} />
                  ))}
                </Bar>
              </BarChart>
            )}
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
