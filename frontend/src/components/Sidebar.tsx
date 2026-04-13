import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Wallet,
  FileText,
  ShoppingCart,
  GitCompare,
  Lightbulb,
  BarChart3,
  Scale,
  Settings,
  X,
  Menu,
} from 'lucide-react';
import { cn } from '../lib/utils';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/budget', label: 'Budget', icon: Wallet },
  { to: '/invoices', label: 'Invoices', icon: FileText },
  { to: '/sales-orders', label: 'Sales Orders', icon: ShoppingCart },
  { to: '/reconciliation', label: 'Reconciliation', icon: GitCompare },
  { to: '/proposals', label: 'Proposals', icon: Lightbulb },
  { to: '/reports', label: 'Reports', icon: BarChart3 },
  { to: '/true-up', label: 'True-Up', icon: Scale },
  { to: '/settings', label: 'Settings', icon: Settings },
] as const;

interface SidebarProps {
  open: boolean;
  onToggle: () => void;
}

export default function Sidebar({ open, onToggle }: SidebarProps) {
  return (
    <>
      {/* Mobile toggle button */}
      <button
        onClick={onToggle}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-slate-900 text-white shadow-lg"
      >
        {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Overlay for mobile */}
      {open && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-30"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-40 h-screen w-60 flex flex-col transition-transform duration-200',
          'bg-[var(--color-sidebar)]',
          !open && '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 h-16 border-b border-slate-700/50">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
            <Wallet className="w-4.5 h-4.5 text-white" />
          </div>
          <span className="text-lg font-bold text-white tracking-tight">
            Budget Platform
          </span>
        </div>

        {/* Nav items */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => {
                if (window.innerWidth < 1024) onToggle();
              }}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-blue-600/20 text-blue-400'
                    : 'text-slate-400 hover:bg-[var(--color-sidebar-hover)] hover:text-slate-200'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    className={cn(
                      'w-5 h-5 shrink-0',
                      isActive ? 'text-blue-400' : 'text-slate-500'
                    )}
                  />
                  <span>{label}</span>
                  {isActive && (
                    <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-400" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-sm font-medium text-slate-300">
              A
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-300 truncate">Admin</p>
              <p className="text-xs text-slate-500 truncate">Administrator</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
