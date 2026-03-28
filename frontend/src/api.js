const API_BASE = '/api';

export async function startPipeline(brief) {
  const res = await fetch(`${API_BASE}/pipeline/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(brief),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPipeline(id) {
  const res = await fetch(`${API_BASE}/pipeline/${id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listPipelines() {
  const res = await fetch(`${API_BASE}/pipelines`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function approvePipeline(id, approved, feedback = '') {
  const res = await fetch(`${API_BASE}/pipeline/${id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved, feedback }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAnalytics() {
  const res = await fetch(`${API_BASE}/analytics`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function connectPipelineWS(pipelineId, onMessage) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/pipeline/${pipelineId}`;
  const ws = new WebSocket(wsUrl);
  ws.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)); }
    catch { onMessage({ message: e.data }); }
  };
  ws.onerror = () => {};
  ws.onclose = () => {};
  return ws;
}

export function connectGlobalWS(onMessage) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/global`;
  const ws = new WebSocket(wsUrl);
  ws.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)); }
    catch { onMessage({ message: e.data }); }
  };
  ws.onerror = () => {};
  ws.onclose = () => {};
  return ws;
}
