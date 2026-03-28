import { useState, useEffect } from 'react';
import {
  ShieldCheck, CheckCircle2, XCircle, AlertTriangle,
  ThumbsUp, ThumbsDown, FileText, Clock, RefreshCw
} from 'lucide-react';
import { listPipelines, getPipeline, approvePipeline } from '../api';

const SEVERITY_ICON = {
  pass: <CheckCircle2 size={14} style={{ color: 'var(--emerald-400)' }} />,
  warning: <AlertTriangle size={14} style={{ color: 'var(--amber-400)' }} />,
  fail: <XCircle size={14} style={{ color: 'var(--rose-400)' }} />,
};

export default function ComplianceHub() {
  const [pipelines, setPipelines] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(false);

  const load = async () => {
    try {
      const list = await listPipelines();
      setPipelines(list);
    } catch {}
  };

  useEffect(() => { load(); const id = setInterval(load, 5000); return () => clearInterval(id); }, []);

  const selectPipeline = async (id) => {
    setSelected(id);
    try {
      const p = await getPipeline(id);
      setDetail(p);
    } catch {}
  };

  const handleAction = async (approved) => {
    if (!selected) return;
    setLoading(true);
    try {
      await approvePipeline(selected, approved, feedback);
      setFeedback('');
      await load();
      const p = await getPipeline(selected);
      setDetail(p);
    } catch {}
    setLoading(false);
  };

  const awaitingApproval = pipelines.filter(p => p.stage === 'awaiting_approval');
  const reviewed = pipelines.filter(p => ['completed', 'rejected'].includes(p.stage));
  const report = detail?.compliance_report;

  return (
    <div>
      <div className="page-header">
        <h1>Compliance Hub</h1>
        <p>Human-in-the-loop review queue for content compliance</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 24 }}>
        {/* Left: Queue */}
        <div>
          {/* Awaiting Approval */}
          <div className="glass-card animate-slide-up stagger-1" style={{ marginBottom: 16 }}>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <AlertTriangle size={16} style={{ color: 'var(--amber-400)' }} />
              Awaiting Review ({awaitingApproval.length})
            </h3>
            {awaitingApproval.length === 0 ? (
              <div style={{ padding: '24px 0', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '0.85rem' }}>
                No items awaiting review
              </div>
            ) : (
              awaitingApproval.map(p => (
                <div key={p.id} onClick={() => selectPipeline(p.id)}
                  style={{
                    padding: '12px', borderRadius: 'var(--radius-sm)',
                    background: selected === p.id ? 'rgba(139,92,246,0.12)' : 'var(--bg-glass)',
                    border: `1px solid ${selected === p.id ? 'var(--purple-500)' : 'transparent'}`,
                    cursor: 'pointer', marginBottom: 6, transition: 'all 0.2s ease',
                  }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 2 }}>{p.topic}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)' }}>
                    #{p.id} • {p.format?.replace('_', ' ')}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Reviewed */}
          <div className="glass-card animate-slide-up stagger-2">
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileText size={16} style={{ color: 'var(--text-tertiary)' }} />
              Reviewed ({reviewed.length})
            </h3>
            {reviewed.length === 0 ? (
              <div style={{ padding: '24px 0', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '0.85rem' }}>
                No reviewed items yet
              </div>
            ) : (
              reviewed.slice(0, 10).map(p => (
                <div key={p.id} onClick={() => selectPipeline(p.id)}
                  style={{
                    padding: '10px', borderRadius: 'var(--radius-sm)',
                    background: selected === p.id ? 'rgba(139,92,246,0.12)' : 'transparent',
                    cursor: 'pointer', marginBottom: 4, transition: 'all 0.2s ease',
                    display: 'flex', alignItems: 'center', gap: 8,
                  }}>
                  {p.stage === 'completed'
                    ? <CheckCircle2 size={14} style={{ color: 'var(--emerald-400)' }} />
                    : <XCircle size={14} style={{ color: 'var(--rose-400)' }} />}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '0.82rem', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {p.topic}
                    </div>
                  </div>
                  {p.duration > 0 && (
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>{p.duration.toFixed(0)}s</span>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right: Detail */}
        <div>
          {!detail ? (
            <div className="glass-card animate-slide-up" style={{ textAlign: 'center', padding: '60px 20px' }}>
              <ShieldCheck size={48} style={{ color: 'var(--text-tertiary)', opacity: 0.3, marginBottom: 16 }} />
              <p style={{ color: 'var(--text-tertiary)' }}>
                Select a pipeline from the queue to view its compliance report
              </p>
            </div>
          ) : (
            <div className="glass-card animate-slide-up">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 4 }}>{detail.brief?.topic}</h3>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <span className="tag tag-purple">{detail.brief?.format?.replace('_', ' ')}</span>
                    <span className={`stage-badge stage-${detail.stage}`}>
                      {detail.stage === 'awaiting_approval' ? 'Awaiting Approval' : detail.stage}
                    </span>
                  </div>
                </div>
                <button className="btn btn-ghost btn-sm" onClick={() => selectPipeline(selected)}>
                  <RefreshCw size={14} /> Refresh
                </button>
              </div>

              {/* Compliance Score */}
              {report && (
                <>
                  <div style={{
                    display: 'flex', gap: 24, padding: '16px 20px', marginBottom: 20,
                    background: 'var(--bg-glass)', borderRadius: 'var(--radius-md)',
                  }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{
                        fontSize: '2rem', fontWeight: 800,
                        color: report.score >= 80 ? 'var(--emerald-400)' : report.score >= 60 ? 'var(--amber-400)' : 'var(--rose-400)',
                      }}>
                        {report.score}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>Score / 100</div>
                    </div>
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                        Overall: <span style={{
                          color: report.overall_status === 'pass' ? 'var(--emerald-400)' :
                                 report.overall_status === 'warning' ? 'var(--amber-400)' : 'var(--rose-400)'
                        }}>
                          {report.overall_status?.toUpperCase()}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>
                        {report.findings?.length || 0} findings • {report.auto_fixes_applied || 0} auto-fixes applied
                      </div>
                    </div>
                  </div>

                  {/* Findings */}
                  <h4 style={{ fontSize: '0.88rem', fontWeight: 700, marginBottom: 10 }}>Compliance Findings</h4>
                  {(report.findings || []).map((f, i) => (
                    <div key={i} className={`finding-item ${f.severity}`}>
                      <div className="finding-category" style={{
                        color: f.severity === 'pass' ? 'var(--emerald-400)' :
                               f.severity === 'warning' ? 'var(--amber-400)' : 'var(--rose-400)',
                        display: 'flex', alignItems: 'center', gap: 6,
                      }}>
                        {SEVERITY_ICON[f.severity]} {f.category}
                      </div>
                      <div className="finding-description">{f.description}</div>
                      {f.suggestion && <div className="finding-suggestion">💡 {f.suggestion}</div>}
                      {f.location && (
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
                          "{f.location}"
                        </div>
                      )}
                    </div>
                  ))}
                </>
              )}

              {/* Content Preview */}
              {detail.draft_content && (
                <div style={{ marginTop: 20 }}>
                  <h4 style={{ fontSize: '0.88rem', fontWeight: 700, marginBottom: 10 }}>Content Preview</h4>
                  <div className="content-preview" style={{ maxHeight: 250 }}>
                    {detail.reviewed_content || detail.draft_content}
                  </div>
                </div>
              )}

              {/* Approval Actions */}
              {detail.stage === 'awaiting_approval' && (
                <div style={{ marginTop: 20, padding: '16px', background: 'var(--bg-glass)', borderRadius: 'var(--radius-md)' }}>
                  <h4 style={{ fontSize: '0.88rem', fontWeight: 700, marginBottom: 10 }}>Your Decision</h4>
                  <textarea className="form-textarea" placeholder="Optional feedback or revision notes…"
                    value={feedback} onChange={e => setFeedback(e.target.value)}
                    rows={2} style={{ marginBottom: 12 }} />
                  <div style={{ display: 'flex', gap: 12 }}>
                    <button className="btn btn-success" onClick={() => handleAction(true)} disabled={loading}>
                      <ThumbsUp size={16} /> Approve & Continue
                    </button>
                    <button className="btn btn-danger" onClick={() => handleAction(false)} disabled={loading}>
                      <ThumbsDown size={16} /> Reject
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
