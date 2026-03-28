import { useState, useEffect } from 'react';
import {
  PenTool, ShieldCheck, Globe, Send, Brain,
  Activity, Cpu, Clock, CheckCircle2, AlertCircle, Loader2
} from 'lucide-react';
import { listPipelines, connectGlobalWS } from '../api';

const AGENTS = [
  { key: 'creator', name: 'Content Creator', icon: PenTool, color: '#8b5cf6', desc: 'Generates content from briefs using AI' },
  { key: 'compliance', name: 'Compliance Reviewer', icon: ShieldCheck, color: '#f59e0b', desc: 'Checks brand, legal & regulatory compliance' },
  { key: 'localizer', name: 'Localizer', icon: Globe, color: '#06b6d4', desc: 'Translates & culturally adapts content' },
  { key: 'distributor', name: 'Distributor', icon: Send, color: '#10b981', desc: 'Formats & publishes to channels' },
  { key: 'intelligence', name: 'Content Intelligence', icon: Brain, color: '#f43f5e', desc: 'Analyses engagement & strategy' },
];

export default function AgentMonitor() {
  const [events, setEvents] = useState([]);
  const [agentStates, setAgentStates] = useState({});
  const [pipelines, setPipelines] = useState([]);

  useEffect(() => {
    listPipelines().then(setPipelines).catch(() => {});
    const ws = connectGlobalWS((evt) => {
      setEvents(prev => [...prev.slice(-100), evt]);
      if (evt.agent_name) {
        setAgentStates(prev => ({
          ...prev,
          [evt.agent_name]: {
            status: evt.event_type === 'agent_start' ? 'running' :
                    evt.event_type === 'agent_complete' ? 'completed' :
                    evt.event_type === 'agent_error' ? 'failed' : prev[evt.agent_name]?.status || 'idle',
            lastMessage: evt.message,
            timestamp: evt.timestamp,
            duration: evt.data?.duration,
          },
        }));
      }
    });
    return () => ws.close();
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1>Agent Monitor</h1>
        <p>Real-time coordination view of all AI agents</p>
      </div>

      {/* Agent Cards */}
      <div className="grid-3" style={{ marginBottom: 28 }}>
        {AGENTS.map((agent, i) => {
          const state = agentStates[agent.key] || { status: 'idle' };
          const Icon = agent.icon;
          return (
            <div key={agent.key} className={`glass-card animate-slide-up stagger-${Math.min(i + 1, 4)}`}
              style={{ position: 'relative', overflow: 'hidden' }}>
              <div style={{
                position: 'absolute', top: 0, left: 0, right: 0, height: 3,
                background: state.status === 'running' ? agent.color : 'transparent',
                boxShadow: state.status === 'running' ? `0 0 20px ${agent.color}` : 'none',
                transition: 'all 0.3s ease',
              }} />

              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 10,
                  background: `${agent.color}18`, color: agent.color,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Icon size={20} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.95rem', fontWeight: 700 }}>{agent.name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>{agent.desc}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  {state.status === 'running' && <Loader2 size={16} style={{ color: agent.color, animation: 'spin 1s linear infinite' }} />}
                  {state.status === 'completed' && <CheckCircle2 size={16} style={{ color: 'var(--emerald-400)' }} />}
                  {state.status === 'failed' && <AlertCircle size={16} style={{ color: 'var(--rose-400)' }} />}
                  {state.status === 'idle' && <Cpu size={16} style={{ color: 'var(--text-tertiary)', opacity: 0.5 }} />}
                </div>
              </div>

              {state.lastMessage && (
                <div style={{
                  padding: '8px 12px', background: 'rgba(0,0,0,0.3)',
                  borderRadius: 'var(--radius-sm)', fontSize: '0.8rem',
                  fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)',
                  marginBottom: 8,
                }}>
                  {state.lastMessage}
                </div>
              )}

              <div style={{ display: 'flex', gap: 12, fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Activity size={11} /> {state.status.toUpperCase()}
                </span>
                {state.duration && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Clock size={11} /> {state.duration.toFixed(1)}s
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Agent Coordination Diagram */}
      <div className="glass-card animate-slide-up" style={{ animationDelay: '0.25s', opacity: 0, marginBottom: 24 }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 16 }}>Agent Coordination Flow</h3>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          gap: 0, padding: '20px 0', overflowX: 'auto',
        }}>
          {AGENTS.map((agent, i) => {
            const state = agentStates[agent.key] || { status: 'idle' };
            const Icon = agent.icon;
            return (
              <div key={agent.key} style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
                  padding: '12px 16px', minWidth: 100,
                }}>
                  <div style={{
                    width: 52, height: 52, borderRadius: '50%',
                    background: state.status === 'running' ? `${agent.color}30` :
                               state.status === 'completed' ? 'rgba(16,185,129,0.2)' : 'var(--bg-glass)',
                    border: `2px solid ${state.status === 'running' ? agent.color :
                            state.status === 'completed' ? 'var(--emerald-500)' : 'var(--border-subtle)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    boxShadow: state.status === 'running' ? `0 0 20px ${agent.color}40` : 'none',
                    transition: 'all 0.5s ease',
                  }}>
                    {state.status === 'running'
                      ? <Loader2 size={22} style={{ color: agent.color, animation: 'spin 1s linear infinite' }} />
                      : state.status === 'completed'
                        ? <CheckCircle2 size={22} style={{ color: 'var(--emerald-400)' }} />
                        : <Icon size={20} style={{ color: 'var(--text-tertiary)' }} />
                    }
                  </div>
                  <span style={{
                    fontSize: '0.72rem', fontWeight: 600, textAlign: 'center',
                    color: state.status !== 'idle' ? 'var(--text-primary)' : 'var(--text-tertiary)',
                  }}>
                    {agent.name}
                  </span>
                </div>
                {i < AGENTS.length - 1 && (
                  <div style={{
                    width: 40, height: 2,
                    background: state.status === 'completed'
                      ? 'var(--emerald-500)'
                      : 'var(--border-subtle)',
                    transition: 'all 0.5s ease',
                  }} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Live Event Stream */}
      <div className="glass-card animate-slide-up" style={{ animationDelay: '0.3s', opacity: 0 }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 12 }}>Live Event Stream</h3>
        <div className="log-terminal" style={{ maxHeight: 350 }}>
          {events.length === 0 && (
            <div style={{ color: 'var(--text-tertiary)', padding: 24, textAlign: 'center' }}>
              <Activity size={28} style={{ marginBottom: 8, opacity: 0.3 }} /><br />
              Start a pipeline to see live agent events here
            </div>
          )}
          {events.map((e, i) => (
            <div key={i} className={`log-entry ${e.event_type === 'error' ? 'error' : e.event_type === 'agent_complete' ? 'success' : ''}`}>
              <span className="log-time">{new Date(e.timestamp).toLocaleTimeString()}</span>
              {e.agent_name && <span className="log-agent">[{e.agent_name}]</span>}
              <span className="log-message">{e.message}</span>
            </div>
          ))}
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
