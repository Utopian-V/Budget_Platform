import { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Search, Upload, Loader2, LogOut, User, ChevronDown } from 'lucide-react';
import { importAll } from '../lib/api';
import { cn } from '../lib/utils';

const routeTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/budget': 'Budget Management',
  '/invoices': 'Invoices',
  '/sales-orders': 'Sales Orders',
  '/reconciliation': 'Reconciliation',
  '/proposals': 'Proposals',
  '/reports': 'Reports',
  '/true-up': 'True-Up Review',
  '/settings': 'Settings',
};

export default function Header() {
  const location = useLocation();
  const [importing, setImporting] = useState(false);
  const [search, setSearch] = useState('');
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  const title = routeTitles[location.pathname] ?? 'Budget Platform';

  const handleImport = async () => {
    setImporting(true);
    try {
      await importAll();
    } catch {
      // silently handle
    } finally {
      setImporting(false);
    }
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-20 bg-white/80 backdrop-blur-sm border-b border-slate-200 h-16 flex items-center justify-between px-6 gap-4">
      <h1 className="text-xl font-bold text-slate-900 shrink-0">{title}</h1>

      <div className="flex items-center gap-3 ml-auto">
        {/* Search */}
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search..."
            className="w-56 pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-200 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
          />
        </div>

        {/* Import Button */}
        <button
          onClick={handleImport}
          disabled={importing}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-60 transition-colors"
        >
          {importing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Upload className="w-4 h-4" />
          )}
          <span className="hidden sm:inline">Import Data</span>
        </button>

        {/* Profile Dropdown */}
        <div className="relative" ref={profileRef}>
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm font-semibold text-white">
              A
            </div>
            <span className="hidden sm:block text-sm font-medium text-slate-700">Admin</span>
            <ChevronDown className={cn('w-4 h-4 text-slate-400 transition-transform', profileOpen && 'rotate-180')} />
          </button>

          {profileOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-lg border border-slate-200 py-2 z-50">
              <div className="px-4 py-3 border-b border-slate-100">
                <p className="text-sm font-semibold text-slate-900">Admin</p>
                <p className="text-xs text-slate-500 mt-0.5">Administrator</p>
              </div>
              <div className="py-1">
                <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors">
                  <User className="w-4 h-4 text-slate-400" />
                  Profile Settings
                </button>
                <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors">
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
              <div className="px-4 py-2 border-t border-slate-100">
                <p className="text-[10px] text-slate-400">Google SSO not yet configured</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
