import {
  LayoutDashboard,
  FileUp,
  GitBranch,
  ShieldCheck,
  FileSpreadsheet,
  History,
  Boxes,
  Settings,
  ArrowUpRight,
  Database,
  CircleHelp,
} from 'lucide-react';
import type { Page } from '../types';
import type { ReactNode } from 'react';
export const navigation: { id: Page; label: string; icon: typeof LayoutDashboard }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'import', label: 'Data Import', icon: FileUp },
  { id: 'mapping', label: 'Account Role Mapping', icon: GitBranch },
  { id: 'quality', label: 'Data Quality', icon: ShieldCheck },
  { id: 'reports', label: 'Reports', icon: FileSpreadsheet },
  { id: 'history', label: 'Processing History', icon: History },
  { id: 'modules', label: 'Module Management', icon: Boxes },
  { id: 'settings', label: 'Settings', icon: Settings },
];
export default function Shell({
  page,
  navigate,
  children,
  connected,
}: {
  page: Page;
  navigate: (page: Page) => void;
  children: ReactNode;
  connected: boolean;
}) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#dashboard" onClick={() => navigate('dashboard')}>
          <span className="brand-icon">
            <GitBranch size={25} />
          </span>
          <span>
            DataMap<span className="brand-sub">STUDIO</span>
          </span>
        </a>
        <div className="workspace-label">
          <span className="workspace-dot" />
          Local workspace<span className="workspace-tag">01</span>
        </div>
        <span className="nav-heading">WORKSPACE</span>
        <nav aria-label="Main navigation">
          {navigation.slice(0, 6).map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              className={page === id ? 'active' : ''}
              onClick={() => navigate(id)}
              aria-current={page === id ? 'page' : undefined}
            >
              <Icon size={18} />
              {label}
              {page === id && <span className="active-dot" />}
            </button>
          ))}
          <span className="nav-heading secondary-heading">PLATFORM</span>
          {navigation.slice(6).map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              className={page === id ? 'active' : ''}
              onClick={() => navigate(id)}
              aria-current={page === id ? 'page' : undefined}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="privacy-card">
            <ShieldCheck size={20} />
            <strong>Your data stays local</strong>
            <p>Workbooks are processed on this computer.</p>
          </div>
          <a href="/docs" target="_blank" rel="noreferrer">
            <CircleHelp size={16} />
            API documentation
            <ArrowUpRight size={14} />
          </a>
          <div className="version">
            DataMap Studio <span>v1.0.0</span>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace<span>/</span>
            <strong>{navigation.find((n) => n.id === page)?.label}</strong>
          </div>
          <div className="connection">
            <span className={connected ? 'online-dot' : 'offline-dot'} />
            {connected ? 'Local processor ready' : 'Local processor unavailable'}
            <span className="avatar">DM</span>
          </div>
        </header>
        <main id="main-content">{children}</main>
        <footer>
          <span>
            <Database size={13} />
            Local processing · Original files preserved
          </span>
          <span>Built for clear, traceable data.</span>
        </footer>
      </div>
    </div>
  );
}
