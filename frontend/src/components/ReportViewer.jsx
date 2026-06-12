import React, { useState } from 'react';
import { Calendar, FileText, ChevronRight, Mail } from 'lucide-react';

// Lightweight custom markdown parser to avoid external package overhead
const parseMarkdownToHtml = (text) => {
  if (!text) return '';
  
  const lines = text.split('\n');
  let html = [];
  let inList = false;
  let inTable = false;
  let tableRows = [];

  const closeList = () => {
    if (inList) {
      html.push('</ul>');
      inList = false;
    }
  };

  const closeTable = () => {
    if (inTable) {
      html.push('<table>');
      tableRows.forEach((row, i) => {
        html.push('<tr>');
        row.forEach(cell => {
          const tag = (i === 0) ? 'th' : 'td';
          html.push(`<${tag}>${cell}</${tag}>`);
        });
        html.push('</tr>');
      });
      html.push('</table>');
      inTable = false;
      tableRows = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i].trim();
    
    // Check table
    if (line.startsWith('|')) {
      closeList();
      inTable = true;
      const cells = line.split('|').map(c => c.trim()).filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
      const isSeparator = cells.every(c => c.match(/^:?-+:?$/));
      if (!isSeparator && cells.length > 0) {
        tableRows.push(cells.map(c => c.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')));
      }
      continue;
    } else {
      closeTable();
    }

    // Check list
    if (line.startsWith('- ') || line.startsWith('* ')) {
      if (!inList) {
        html.push('<ul>');
        inList = true;
      }
      let content = line.substring(2);
      content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      html.push(`<li>${content}</li>`);
      continue;
    } else {
      closeList();
    }

    if (line.startsWith('### ')) {
      html.push(`<h3>${line.substring(4)}</h3>`);
    } else if (line.startsWith('## ')) {
      html.push(`<h2>${line.substring(3)}</h2>`);
    } else if (line.startsWith('# ')) {
      html.push(`<h1>${line.substring(2)}</h1>`);
    } else if (line.startsWith('> ')) {
      html.push(`<blockquote>${line.substring(2)}</blockquote>`);
    } else if (line === '') {
      // Paragraph spacer
    } else {
      let content = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      html.push(`<p>${content}</p>`);
    }
  }

  closeList();
  closeTable();

  return html.join('\n');
};

export default function ReportViewer({ reports }) {
  const [selectedReportIndex, setSelectedReportIndex] = useState(0);

  const activeReport = reports && reports.length > 0 ? reports[selectedReportIndex] : null;
  const formattedHtml = activeReport ? parseMarkdownToHtml(activeReport.content) : '';

  const formatDate = (isoStr) => {
    try {
      return new Date(isoStr).toLocaleDateString(undefined, { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="glass-panel col-8" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h3 style={{ fontSize: '18px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileText style={{ color: 'var(--accent-purple)', width: '20px', height: '20px' }} />
          Executive Intelligence Briefing
        </h3>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Llama-3.3-70B synthesised correlation summaries and market overviews</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 3fr', gap: '24px', flex: 1, minHeight: '380px' }}>
        {/* Left Side: Report Archives List */}
        <div style={{ borderRight: '1px solid rgba(255, 255, 255, 0.05)', paddingRight: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <p style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Archives</p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto', maxHeight: '380px' }}>
            {reports && reports.length > 0 ? (
              reports.map((report, idx) => {
                const isSelected = selectedReportIndex === idx;
                const sentColor = report.overall_sentiment === 'Positive' 
                  ? 'var(--status-positive)' 
                  : (report.overall_sentiment === 'Negative' ? 'var(--status-negative)' : 'var(--status-neutral)');
                
                return (
                  <div
                    key={report.id}
                    onClick={() => setSelectedReportIndex(idx)}
                    style={{
                      background: isSelected ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
                      border: isSelected ? '1px solid rgba(59, 130, 246, 0.2)' : '1px solid transparent',
                      padding: '12px',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px'
                    }}
                    className="glass-card-interactive"
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '11px', color: sentColor, fontWeight: 600 }}>{report.overall_sentiment.toUpperCase()}</span>
                      <ChevronRight style={{ width: '12px', height: '12px', color: isSelected ? 'var(--accent-blue)' : 'var(--text-muted)' }} />
                    </div>
                    <p style={{ fontSize: '13px', color: 'var(--text-primary)', fontWeight: isSelected ? 600 : 400, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {report.title.replace("Market Intelligence Report - ", "")}
                    </p>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Calendar style={{ width: '10px', height: '10px' }} />
                      {formatDate(report.created_at).split(',')[0]}
                    </span>
                  </div>
                );
              })
            ) : (
              <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No reports generated yet.</p>
            )}
          </div>
        </div>

        {/* Right Side: Active Report content */}
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: '380px', overflowY: 'auto', maxHeight: '420px', paddingRight: '8px' }}>
          {activeReport ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '16px', borderBottom: '1px solid rgba(255, 255, 255, 0.05)', paddingBottom: '12px' }}>
                <div>
                  <h4 style={{ fontSize: '20px', color: 'var(--text-primary)' }}>{activeReport.title}</h4>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '6px' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Calendar style={{ width: '12px', height: '12px' }} />
                      {formatDate(activeReport.created_at)}
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Mail style={{ width: '12px', height: '12px' }} />
                      Dispatched to Watchlist
                    </span>
                  </div>
                </div>
                
                <div>
                  <span className={`badge ${
                    activeReport.overall_sentiment === 'Positive' 
                      ? 'badge-positive' 
                      : (activeReport.overall_sentiment === 'Negative' ? 'badge-negative' : 'badge-neutral')
                  }`}>
                    Overall: {activeReport.overall_sentiment}
                  </span>
                </div>
              </div>

              {/* Rendered HTML */}
              <div 
                className="markdown-body" 
                dangerouslySetInnerHTML={{ __html: formattedHtml }}
              />
            </div>
          ) : (
            <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', color: 'var(--text-secondary)' }}>
              No active report to view. Press "Run Sentinel Pipeline" to compile a report.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
