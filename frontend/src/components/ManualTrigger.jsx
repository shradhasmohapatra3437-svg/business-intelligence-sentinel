import React, { useState, useEffect } from 'react';
import { Play, Loader, CheckCircle, XCircle } from 'lucide-react';
import { triggerRun, getJobStatus } from '../lib/api';

export default function ManualTrigger({ onPipelineSuccess }) {
  const [status, setStatus] = useState('idle'); // idle, running, complete, error
  const [jobId, setJobId] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [elapsed, setElapsed] = useState(0);

  const handleTrigger = async () => {
    try {
      setStatus('running');
      setElapsed(0);
      setErrorMsg('');
      const res = await triggerRun();
      setJobId(res.job_id);
    } catch (e) {
      setStatus('error');
      setErrorMsg(e.message || 'Failed to trigger pipeline');
    }
  };

  useEffect(() => {
    let pollInterval;
    let timerInterval;

    if (status === 'running' && jobId) {
      // Elapsed timer
      timerInterval = setInterval(() => {
        setElapsed(prev => prev + 1);
      }, 1000);

      // Poll API
      pollInterval = setInterval(async () => {
        try {
          const job = await getJobStatus(jobId);
          if (job.status === 'complete') {
            setStatus('complete');
            if (onPipelineSuccess) onPipelineSuccess();
          } else if (job.status === 'failed') {
            setStatus('error');
            setErrorMsg(job.error_message || 'Pipeline failed during execution');
          }
        } catch (e) {
          console.error("Polling error:", e);
        }
      }, 3000);
    }

    return () => {
      clearInterval(pollInterval);
      clearInterval(timerInterval);
    };
  }, [status, jobId, onPipelineSuccess]);

  // Determine approx phase based on elapsed time
  let phaseText = "Initializing...";
  if (elapsed > 2) phaseText = "Collecting financial data & news...";
  if (elapsed > 15) phaseText = "Running deep learning sentiment analysis...";
  if (elapsed > 35) phaseText = "Reasoning with LLM & generating report...";
  if (elapsed > 55) phaseText = "Finalizing & sending email...";

  return (
    <div className="glass-panel col-4" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '32px' }}>
      
      {status === 'idle' && (
        <>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(59, 130, 246, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <Play style={{ color: 'var(--accent-blue)', marginLeft: '4px' }} size={32} />
          </div>
          <h3 style={{ marginBottom: '8px' }}>Manual Override</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px' }}>
            Trigger an immediate run of the full data collection and sentiment pipeline.
          </p>
          <button onClick={handleTrigger} style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '8px', padding: '12px' }}>
            <Play size={18} />
            Run Agent Now
          </button>
        </>
      )}

      {status === 'running' && (
        <>
          <div style={{ marginBottom: '24px' }}>
            <Loader className="animate-spin" size={48} color="var(--accent-blue)" />
          </div>
          <h3 style={{ marginBottom: '8px', color: 'var(--accent-blue)' }}>Pipeline Active</h3>
          <p style={{ color: 'var(--text-primary)', fontSize: '15px', marginBottom: '8px' }}>
            {phaseText}
          </p>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', fontVariantNumeric: 'tabular-nums' }}>
            Elapsed: {elapsed}s
          </p>
        </>
      )}

      {status === 'complete' && (
        <>
          <div style={{ marginBottom: '16px' }}>
            <CheckCircle size={56} color="var(--status-positive)" />
          </div>
          <h3 style={{ marginBottom: '8px', color: 'var(--status-positive)' }}>Mission Accomplished</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px' }}>
            Report generated and emailed successfully in {elapsed}s.
          </p>
          <button onClick={() => setStatus('idle')} style={{ width: '100%', background: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
            Reset Trigger
          </button>
        </>
      )}

      {status === 'error' && (
        <>
          <div style={{ marginBottom: '16px' }}>
            <XCircle size={48} color="var(--status-negative)" />
          </div>
          <h3 style={{ marginBottom: '8px', color: 'var(--status-negative)' }}>Pipeline Failed</h3>
          <p style={{ color: 'var(--status-negative)', fontSize: '13px', background: 'rgba(239, 68, 68, 0.1)', padding: '12px', borderRadius: '8px', marginBottom: '24px', width: '100%', wordBreak: 'break-word' }}>
            {errorMsg}
          </p>
          <button onClick={() => setStatus('idle')} style={{ width: '100%' }}>
            Try Again
          </button>
        </>
      )}

    </div>
  );
}
