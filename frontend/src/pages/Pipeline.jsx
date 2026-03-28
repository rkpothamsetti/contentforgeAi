import { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Play, PenTool, ShieldCheck, Globe, Send, Brain,
  CheckCircle2, XCircle, Loader2, Clock, Sparkles
} from 'lucide-react';
import { startPipeline, getPipeline, connectPipelineWS } from '../api';

const STAGES = [
  { key: 'creating', label: 'Create', icon: PenTool },
  { key: 'reviewing', label: 'Compliance', icon: ShieldCheck },
  { key: 'localizing', label: 'Localise', icon: Globe },
  { key: 'distributing', label: 'Distribute', icon: Send },
  { key: 'intelligence', label: 'Intelligence', icon: Brain },
];

const STAGE_ORDER = ['queued', 'creating', 'reviewing', 'awaiting_approval', 'localizing', 'distributing', 'completed'];

function stageIndex(stage) {
  const i = STAGE_ORDER.indexOf(stage);
  return i === -1 ? -1 : i;
}

const FORMATS = [
  { value: 'blog_post', label: 'Blog Post' },
  { value: 'social_media', label: 'Social Media' },
  { value: 'email_newsletter', label: 'Email Newsletter' },
  { value: 'press_release', label: 'Press Release' },
  { value: 'sales_collateral', label: 'Sales Collateral' },
];

const CHANNELS = ['website', 'linkedin', 'twitter', 'email', 'internal', 'instagram'];
const LANGUAGES = ['Hindi', 'Spanish', 'French', 'German', 'Japanese', 'Arabic', 'Portuguese', 'Mandarin'];

export default function Pipeline() {
  const [searchParams] = useSearchParams();
  const existingId = searchParams.get('id');

  const [brief, setBrief] = useState({
    topic: '', audience: 'enterprise decision-makers', format: 'blog_post',
    tone: 'professional', key_points: [], brand_name: 'TechCorp',
    target_languages: ['Hindi', 'Spanish'],
    target_channels: ['website', 'linkedin', 'email'],
    knowledge_context: '',
  });
  const [keyPointInput, setKeyPointInput] = useState('');
  const [pipelineId, setPipelineId] = useState(existingId || null);
  const [pipeline, setPipeline] = useState(null);
  const [logs, setLogs] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const logRef = useRef(null);
  const wsRef = useRef(null);

  // Poll pipeline status
  useEffect(() => {
    if (!pipelineId) return;
    const poll = async () => {
      try {
        const p = await getPipeline(pipelineId);
        setPipeline(p);
      } catch {}
    };
    poll();
    const id = setInterval(poll, 2000);
    return () => clearInterval(id);
  }, [pipelineId]);

  // WebSocket for live logs
  useEffect(() => {
    if (!pipelineId) return;
    const ws = connectPipelineWS(pipelineId, (evt) => {
      setLogs(prev => [...prev, evt]);
      // Auto-refresh pipeline
      getPipeline(pipelineId).then(setPipeline).catch(() => {});
    });
    wsRef.current = ws;
    return () => ws.close();
  }, [pipelineId]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!brief.topic.trim()) return;
    setSubmitting(true);
    setLogs([]);
    try {
      const res = await startPipeline(brief);
      setPipelineId(res.pipeline_id);
    } catch (err) {
      setLogs([{ message: `Error: ${err.message}`, event_type: 'error', timestamp: new Date().toISOString() }]);
    }
    setSubmitting(false);
  };

  const addKeyPoint = () => {
    if (keyPointInput.trim()) {
      setBrief(b => ({ ...b, key_points: [...b.key_points, keyPointInput.trim()] }));
      setKeyPointInput('');
    }
  };

  const toggleItem = (field, value) => {
    setBrief(b => ({
      ...b,
      [field]: b[field].includes(value) ? b[field].filter(v => v !== value) : [...b[field], value],
    }));
  };

  const currentStage = pipeline?.stage || 'queued';
  const ci = stageIndex(currentStage);

  return (
    <div>
      <div className="page-header">
        <h1>Content Pipeline</h1>
        <p>Create and monitor AI-powered content workflows</p>
      </div>

      {!pipelineId ? (
        /* ── Brief Form ─────────────────────────────────────────────────── */
        <form onSubmit={handleSubmit}>
          <div className="grid-2">
            <div className="glass-card animate-slide-up stagger-1">
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Sparkles size={18} style={{ color: 'var(--purple-400)' }} /> Content Brief
              </h3>

              <div className="form-group">
                <label>Topic *</label>
                <input className="form-input" placeholder="e.g. AI in Enterprise Content Operations"
                  value={brief.topic} onChange={e => setBrief({ ...brief, topic: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Target Audience</label>
                <input className="form-input" placeholder="e.g. enterprise decision-makers"
                  value={brief.audience} onChange={e => setBrief({ ...brief, audience: e.target.value })} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div className="form-group">
                  <label>Format</label>
                  <select className="form-select" value={brief.format}
                    onChange={e => setBrief({ ...brief, format: e.target.value })}>
                    {FORMATS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>Tone</label>
                  <select className="form-select" value={brief.tone}
                    onChange={e => setBrief({ ...brief, tone: e.target.value })}>
                    {['professional', 'casual', 'authoritative', 'friendly', 'technical', 'inspirational'].map(t =>
                      <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                    )}
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Brand Name</label>
                <input className="form-input" value={brief.brand_name}
                  onChange={e => setBrief({ ...brief, brand_name: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Key Points</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input className="form-input" placeholder="Add a key point…"
                    value={keyPointInput} onChange={e => setKeyPointInput(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addKeyPoint(); } }} />
                  <button type="button" className="btn btn-ghost btn-sm" onClick={addKeyPoint}>Add</button>
                </div>
                {brief.key_points.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
                    {brief.key_points.map((p, i) => (
                      <span key={i} className="tag tag-purple" style={{ cursor: 'pointer' }}
                        onClick={() => setBrief(b => ({ ...b, key_points: b.key_points.filter((_, j) => j !== i) }))}>
                        {p} ×
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="glass-card animate-slide-up stagger-2">
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 20 }}>
                Distribution & Localisation
              </h3>

              <div className="form-group">
                <label>Target Languages</label>
                <div className="checkbox-group">
                  {LANGUAGES.map(l => (
                    <label key={l} className={`checkbox-chip ${brief.target_languages.includes(l) ? 'selected' : ''}`}
                      onClick={() => toggleItem('target_languages', l)}>
                      <input type="checkbox" checked={brief.target_languages.includes(l)} readOnly />
                      {l}
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>Target Channels</label>
                <div className="checkbox-group">
                  {CHANNELS.map(c => (
                    <label key={c} className={`checkbox-chip ${brief.target_channels.includes(c) ? 'selected' : ''}`}
                      onClick={() => toggleItem('target_channels', c)}>
                      <input type="checkbox" checked={brief.target_channels.includes(c)} readOnly />
                      {c.charAt(0).toUpperCase() + c.slice(1)}
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>Knowledge Context (optional)</label>
                <textarea className="form-textarea"
                  placeholder="Paste internal data, reports, product specs, or customer feedback here. The AI will use this to inform the content."
                  value={brief.knowledge_context}
                  onChange={e => setBrief({ ...brief, knowledge_context: e.target.value })}
                  rows={5} />
              </div>

              <button type="submit" className="btn btn-primary btn-lg" disabled={submitting || !brief.topic.trim()}
                style={{ width: '100%', justifyContent: 'center', marginTop: 8 }}>
                {submitting ? <><Loader2 size={18} className="spin" /> Starting…</> : <><Play size={18} /> Launch Pipeline</>}
              </button>
            </div>
          </div>
        </form>
      ) : (
        /* ── Pipeline Tracker ───────────────────────────────────────────── */
        <div>
          {/* Stage Tracker */}
          <div className="glass-card animate-slide-up" style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Pipeline #{pipelineId}</h3>
              <span className={`stage-badge stage-${currentStage}`}>
                {currentStage === 'awaiting_approval' ? 'Awaiting Approval' : currentStage.charAt(0).toUpperCase() + currentStage.slice(1)}
              </span>
            </div>
            <div className="pipeline-tracker">
              {STAGES.map((s, i) => {
                const stageIdx = STAGE_ORDER.indexOf(s.key);
                let state = 'pending';
                if (currentStage === 'completed') state = 'completed';
                else if (currentStage === 'failed' || currentStage === 'rejected') state = ci >= stageIdx ? 'failed' : 'pending';
                else if (stageIdx < ci) state = 'completed';
                else if (stageIdx === ci || (s.key === 'reviewing' && currentStage === 'awaiting_approval')) state = 'active';

                const Icon = s.icon;
                return (
                  <div key={s.key} style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                    <div className={`pipeline-step ${state}`}>
                      <div className="pipeline-step-icon">
                        {state === 'completed' ? <CheckCircle2 size={20} color="#34d399" /> :
                         state === 'failed' ? <XCircle size={20} color="#fb7185" /> :
                         state === 'active' ? <Loader2 size={20} style={{ animation: 'spin 1s linear infinite', color: '#a78bfa' }} /> :
                         <Icon size={18} style={{ color: '#6b6b78' }} />}
                      </div>
                      <div className="pipeline-step-label">{s.label}</div>
                    </div>
                    {i < STAGES.length - 1 && (
                      <div className={`pipeline-connector ${state === 'completed' ? 'completed' : state === 'active' ? 'active' : ''}`} />
                    )}
                  </div>
                );
              })}
            </div>

            {/* Timing */}
            {pipeline?.total_duration_seconds > 0 && (
              <div style={{
                display: 'flex', gap: 24, justifyContent: 'center',
                padding: '16px 0 0', borderTop: '1px solid var(--border-subtle)', marginTop: 12,
              }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--purple-400)' }}>
                    {pipeline.total_duration_seconds.toFixed(1)}s
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>AI Pipeline Time</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--rose-400)' }}>
                    {pipeline.estimated_manual_hours}h
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>Manual Equivalent</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--emerald-400)' }}>
                    {pipeline.estimated_manual_hours > 0
                      ? ((1 - (pipeline.total_duration_seconds / 3600) / pipeline.estimated_manual_hours) * 100).toFixed(1)
                      : '0'}%
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>Time Saved</div>
                </div>
              </div>
            )}
          </div>

          {/* Logs + Content Preview */}
          <div className="grid-2">
            <div className="glass-card animate-slide-up stagger-1">
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 12 }}>Agent Activity Log</h3>
              <div className="log-terminal" ref={logRef}>
                {logs.length === 0 && (
                  <div style={{ color: 'var(--text-tertiary)', padding: 20, textAlign: 'center' }}>
                    Waiting for agent activity…
                  </div>
                )}
                {logs.map((l, i) => (
                  <div key={i} className={`log-entry ${l.event_type === 'error' ? 'error' : l.event_type === 'agent_complete' ? 'success' : ''}`}>
                    <span className="log-time">{new Date(l.timestamp).toLocaleTimeString()}</span>
                    {l.agent_name && <span className="log-agent">[{l.agent_name}]</span>}
                    <span className="log-message">{l.message}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card animate-slide-up stagger-2">
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 12 }}>Generated Content</h3>
              <div className="content-preview">
                {pipeline?.draft_content || 'Content will appear here once the Creator agent completes…'}
              </div>
            </div>
          </div>

          {/* New Pipeline button */}
          {(currentStage === 'completed' || currentStage === 'failed' || currentStage === 'rejected') && (
            <div style={{ textAlign: 'center', marginTop: 24 }}>
              <button className="btn btn-primary btn-lg" onClick={() => { setPipelineId(null); setPipeline(null); setLogs([]); }}>
                <Play size={18} /> Start New Pipeline
              </button>
            </div>
          )}
        </div>
      )}

      {/* Inline spin animation */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } } .spin { animation: spin 1s linear infinite; }`}</style>
    </div>
  );
}
