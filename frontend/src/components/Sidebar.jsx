import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Workflow, Activity, ShieldCheck, Sparkles } from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/pipeline', icon: Workflow, label: 'Content Pipeline' },
  { to: '/agents', icon: Activity, label: 'Agent Monitor' },
  { to: '/compliance', icon: ShieldCheck, label: 'Compliance Hub' },
];

export default function Sidebar() {
  return (
    <aside style={{
      width: 'var(--sidebar-width)',
      height: '100vh',
      position: 'fixed',
      left: 0,
      top: 0,
      background: 'rgba(10, 10, 15, 0.95)',
      backdropFilter: 'blur(20px)',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 100,
      padding: '24px 0',
    }}>
      {/* Logo */}
      <div style={{
        padding: '0 24px 28px',
        borderBottom: '1px solid var(--border-subtle)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 36, height: 36,
            borderRadius: 10,
            background: 'var(--gradient-purple)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 20px rgba(139,92,246,0.3)',
          }}>
            <Sparkles size={20} color="#fff" />
          </div>
          <div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
              ContentForge
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--purple-400)', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              AI Platform
            </div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ padding: '20px 12px', flex: 1 }}>
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '11px 16px',
              borderRadius: 'var(--radius-md)',
              marginBottom: 4,
              color: isActive ? 'var(--text-primary)' : 'var(--text-tertiary)',
              background: isActive ? 'rgba(139,92,246,0.12)' : 'transparent',
              fontWeight: isActive ? 600 : 500,
              fontSize: '0.9rem',
              transition: 'all 0.2s ease',
              textDecoration: 'none',
              position: 'relative',
            })}
          >
            {({ isActive }) => (
              <>
                {isActive && <div style={{
                  position: 'absolute',
                  left: 0,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  width: 3,
                  height: 20,
                  borderRadius: 3,
                  background: 'var(--gradient-purple)',
                }} />}
                <Icon size={18} style={{ opacity: isActive ? 1 : 0.5 }} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '16px 24px',
        borderTop: '1px solid var(--border-subtle)',
        fontSize: '0.72rem',
        color: 'var(--text-tertiary)',
        textAlign: 'center',
      }}>
        Multi-Agent Content Ops
        <br />
        <span style={{ color: 'var(--purple-400)' }}>ET × Avataar Hackathon</span>
      </div>
    </aside>
  );
}
