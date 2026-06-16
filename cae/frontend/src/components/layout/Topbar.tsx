import { useEffect, useState, useRef } from 'react';
import { LogOut, Bell, ChevronDown, Building2, User } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import type { Company } from '../../types';

export default function Topbar() {
  const { user, companyId, setCompanyId, logout } = useAuthStore();
  const navigate = useNavigate();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [showCompanyMenu, setShowCompanyMenu] = useState(false);
  const companyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiClient.get('/companies').then(r => setCompanies(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (companyRef.current && !companyRef.current.contains(e.target as Node)) {
        setShowCompanyMenu(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const currentCompany = companies.find(c => c.id === companyId);

  const handleLogout = async () => {
    try { await apiClient.post('/auth/logout'); } catch {}
    logout();
    navigate('/login');
  };

  return (
    <header className="h-14 bg-navy-800 border-b border-navy-border flex items-center justify-between px-6 gap-4">
      {/* Company Switcher */}
      <div ref={companyRef} className="relative">
        <button
          onClick={() => setShowCompanyMenu(s => !s)}
          className="flex items-center gap-2 bg-navy-700 border border-navy-border rounded-lg px-3 py-1.5 text-sm hover:border-gold/40 transition-colors"
        >
          <Building2 className="w-4 h-4 text-gold" />
          <span className="text-gray-200 font-medium max-w-[200px] truncate">
            {currentCompany?.name || 'Select Company'}
          </span>
          {companies.length > 1 && <ChevronDown className="w-3.5 h-3.5 text-gray-500" />}
        </button>

        {showCompanyMenu && companies.length > 0 && (
          <div className="absolute left-0 top-full mt-1 bg-navy-800 border border-navy-border rounded-lg shadow-xl z-50 min-w-[260px]">
            <div className="px-3 py-2 text-xs text-gray-600 uppercase tracking-wider border-b border-navy-border">
              Switch Company
            </div>
            {companies.map(c => (
              <button
                key={c.id}
                onClick={() => { setCompanyId(c.id); setShowCompanyMenu(false); }}
                className={`w-full text-left px-4 py-2.5 text-sm hover:bg-navy-700 transition-colors ${c.id === companyId ? 'text-gold font-medium' : 'text-gray-300'}`}
              >
                <div className="font-medium">{c.name}</div>
                {c.gstin && <div className="text-xs text-gray-500 mt-0.5">GSTIN: {c.gstin}</div>}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="text-sm text-gray-600 hidden lg:block">
        Continuous Audit Engine — <span className="text-gray-400">Real-time Risk Intelligence</span>
      </div>

      <div className="flex items-center gap-3">
        <button className="relative p-2 text-gray-400 hover:text-gray-100">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        {/* Profile button */}
        <button
          onClick={() => navigate('/profile')}
          className="flex items-center gap-2 text-sm hover:bg-navy-700 rounded-lg px-2 py-1 transition-colors"
        >
          <div className="w-7 h-7 rounded-full bg-gold/20 border border-gold/40 flex items-center justify-center text-gold text-xs font-semibold">
            {user?.full_name?.[0] || 'U'}
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-gray-200 text-sm leading-tight">{user?.full_name || 'User'}</div>
            <div className="text-gray-500 text-xs capitalize leading-tight">{user?.role}</div>
          </div>
        </button>

        <button onClick={handleLogout} className="btn-ghost flex items-center gap-1 text-sm text-gray-400 hover:text-red-400">
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
