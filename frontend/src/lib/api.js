import axios from 'axios';

// Vite proxy handles /api in dev. In prod, ensure VITE_API_URL is set or use relative if served together.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealth = async () => {
  const { data } = await api.get('/api/health');
  return data;
};

export const getReports = async (limit = 20, offset = 0, riskLevel = null) => {
  const params = { limit, offset };
  if (riskLevel) params.risk_level = riskLevel;
  const { data } = await api.get('/api/reports', { params });
  return data;
};

export const getReport = async (id) => {
  const { data } = await api.get(`/api/reports/${id}`);
  return data;
};

export const getSentimentHistory = async (days = 14) => {
  const { data } = await api.get('/api/sentiment-history', { params: { days } });
  return data;
};

export const getConfig = async () => {
  const { data } = await api.get('/api/config');
  return data;
};

export const updateConfig = async (configData) => {
  const { data } = await api.put('/api/config', configData);
  return data;
};

export const triggerRun = async () => {
  const { data } = await api.post('/api/trigger');
  return data;
};

export const getJobStatus = async (jobId) => {
  const { data } = await api.get(`/api/jobs/${jobId}`);
  return data;
};

export const getRuns = async (limit = 20, offset = 0) => {
  const { data } = await api.get('/api/runs', { params: { limit, offset } });
  return data;
};

export const getStats = async () => {
  const { data } = await api.get('/api/stats');
  return data;
};
