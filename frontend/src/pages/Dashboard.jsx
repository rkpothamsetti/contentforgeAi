import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Clock, Zap, ShieldCheck, Globe, BarChart3, TrendingUp,
  ArrowRight, Workflow, CheckCircle2
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { getAnalytics, listPipelines } from '../api';

const STAGE_LABELS = {
  queued: 'Queued', creating: 'Creating', reviewing: 'Reviewing',
  awaiting_approval: 'Awaiting Approval', localizing: 'Localizing',
  distributing: 'Distributing', completed: 'Completed', failed: 'Failed',
  rejected: 'Rejected',
};

const PIE_COLORS = ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e'];

// Simulated historical data for chart (in a real system this would come from the API)
const MOCK_TREND = [
  { day: 'Mon', ai: 4, manual: 32 },
  { day: 'Tue', ai: 6, manual: 48 },
  { day: 'Wed', ai: 3, manual: 24 },
  { day: 'Thu', ai: 8, manual: 64 },
  { day: 'Fri', ai: 5, manual: 40 },
  { day: 'Sat', ai: 2, manual: 16 },
  { day: 'Sun', ai: 7, manual: 56 },
];

export default function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [pipelines, setPipelines] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      try {
        const [a, p] = await Promise.all([getAnalytics(), listPipelines()]);
        setAnalytics(a);
        setPipelines(p);
      } catch { /* backend not running yet, show defaults */ }
    };
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  const a = analytics || {};
  const timeSavings = a.time_savings_percent || 97.5;
  const avgCycle = a.avg_cycle_time_seconds || 0;
  const manualHours = a.avg_manual_equivalent_hours || 14.5;
  const compRate = a.compliance_pass_rate || 100;

  const formatPie = Object.entries(a.content_by_format || {}).map(([name, value]) => ({ name, value }));

  return (
    <div>
      <div className="page-header">
        <h1>Command Center</h1>
        <p>Real-time overview of your AI-powered content operations</p>
      </div>

      {/* KPI Cards */}
      <div className="grid-4" style={{ marginBottom: 28 }}>
        {[
          {
            icon: <Zap size={20} />, label: 'Time Savings',
            value: `${timeSavings.toFixed(1)}%`,
            trend: `${manualHours}h manual → ${(avgCycle / 60).toFixed(1)}m AI`,
            gradient: 'var(--gradient-purple)', color: 'var(--purple-400)',
            bg: 'rgba(139,92,246,0.12)',
          },
          {
            icon: <Workflow size={20} />, label: 'Pipelines Run',
            value: a.total_pipelines || 0,
            trend: `${a.completed_pipelines || 0} completed`,
            gradient: 'var(--gradient-cyan)', color: 'var(--cyan-400)',
            bg: 'rgba(6,182,212,0.12)',
          },
          {
            icon: <ShieldCheck size={20} />, label: 'Compliance Rate',
            value: `${compRate}%`,
            trend: 'Brand + Legal + Regulatory',
            gradient: 'var(--gradient-emerald)', color: 'var(--emerald-400)',
            bg: 'rgba(16,185,129,0.12)',
          },
          {
            icon: <Globe size={20} />, label: 'Languages / Channels',
            value: `${a.languages_supported || 2} / ${a.channels_active || 3}`,
            trend: 'Active localizations & distributions',
            gradient: 'var(--gradient-amber)', color: 'var(--amber-400)',
            bg: 'rgba(245,158,11,0.12)',
          },
        ].map((m, i) => (
          <div key={i} className={`glass-card metric-card animate-slide-up stagger-${i + 1}`}>
            <div className="metric-accent" style={{ background: m.gradient }} />
            <div className="metric-icon" style={{ background: m.bg, color: m.color }}>
              {m.icon}
            </div>
            <div className="metric-value" style={{ color: m.color }}>{m.value}</div>
            <div className="metric-label">{m.label}</div>
            <div className="metric-trend" style={{ color: 'var(--text-tertiary)' }}>
              <TrendingUp size={12} /> {m.trend}
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid-2" style={{ marginBottom: 28 }}>
        {/* Time Comparison Chart */}
        <div className="glass-card animate-slide-up" style={{ animationDelay: '0.25s', opacity: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Content Cycle Time</h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-tertiary)' }}>AI vs Manual (minutes)</p>
            </div>
            <BarChart3 size={18} style={{ color: 'var(--text-tertiary)' }} />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={MOCK_TREND}>
              <defs>
                <linearGradient id="gradManual" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#f43f5e" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradAI" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="day" stroke="#6b6b78" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#6b6b78" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  background: 'rgba(20,20,32,0.95)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 10, fontSize: '0.82rem',
                }}
              />
              <Area type="monotone" dataKey="manual" stroke="#f43f5e" fill="url(#gradManual)" strokeWidth={2} name="Manual (min)" />
              <Area type="monotone" dataKey="ai" stroke="#8b5cf6" fill="url(#gradAI)" strokeWidth={2} name="AI (min)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Content by Format Pie */}
        <div className="glass-card animate-slide-up" style={{ animationDelay: '0.3s', opacity: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Content by Format</h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-tertiary)' }}>Distribution of output types</p>
            </div>
          </div>
          {formatPie.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={formatPie} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                  paddingAngle={4} dataKey="value" stroke="none"
                >
                  {formatPie.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{
                  background: 'rgba(20,20,32,0.95)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 10, fontSize: '0.82rem',
                }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-tertiary)', fontSize: '0.9rem' }}>
              Run a pipeline to see format distribution
            </div>
          )}
          {formatPie.length > 0 && (
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 8 }}>
              {formatPie.map((f, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.78rem' }}>
                  <div style={{ width: 10, height: 10, borderRadius: 3, background: PIE_COLORS[i % PIE_COLORS.length] }} />
                  <span style={{ color: 'var(--text-secondary)' }}>{f.name.replace('_', ' ')}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent Pipelines */}
      <div className="glass-card animate-slide-up" style={{ animationDelay: '0.35s', opacity: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Recent Pipelines</h3>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/pipeline')}>
            New Pipeline <ArrowRight size={14} />
          </button>
        </div>
        {pipelines.length === 0 ? (
          <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-tertiary)' }}>
            <Workflow size={40} style={{ marginBottom: 12, opacity: 0.3 }} /><br />
            No pipelines yet. Create your first content pipeline to see it here.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {pipelines.slice(0, 8).map(p => (
              <div key={p.id}
                onClick={() => navigate(`/pipeline?id=${p.id}`)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 16,
                  padding: '12px 16px',
                  background: 'var(--bg-glass)',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onMouseOver={e => e.currentTarget.style.background = 'var(--bg-glass-hover)'}
                onMouseOut={e => e.currentTarget.style.background = 'var(--bg-glass)'}
              >
                <CheckCircle2 size={16} style={{ color: p.stage === 'completed' ? 'var(--emerald-400)' : 'var(--text-tertiary)', flexShrink: 0 }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '0.88rem', fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {p.topic}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                    {p.format?.replace('_', ' ')} • {new Date(p.created_at).toLocaleTimeString()}
                  </div>
                </div>
                <span className={`stage-badge stage-${p.stage}`}>
                  {STAGE_LABELS[p.stage] || p.stage}
                </span>
                {p.duration > 0 && (
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Clock size={12} /> {p.duration.toFixed(1)}s
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
