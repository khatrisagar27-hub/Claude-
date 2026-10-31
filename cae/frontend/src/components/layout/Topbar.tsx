import { useEffect, useState, useRef } from 'react';
import { LogOut, Bell, ChevronDown, Building2, ClipboardCheck } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import type { Company, Engagement } from '../../types';
import { AUDIT_TYPE_LABEL } from '../../api/labels';

export default function Topbar() {
  const { user, companyId, setCompanyId, engagement, setEngagement, logout } = useAuthStore();
  const navigate = useNavigate();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [showCompanyMenu, setShowCompanyMenu] = useState(false);
  const companyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiClient.get('/companies').then(r => setCompanies(r.data)).catch(() => {});
  }, []);

  // engagements of the selected company; refreshed when the Engagements page announces a change
  useEffect(() => {
    if (!companyId) { setEngagements([]); return; }
    const load = () => apiClient.get(`/engagements?company_id=${companyId}`).then(r => setEngagements(r.data)).catch(() => setEngagements([]));
    load();
    window.addEventListener('cae:engagements-changed', load);
    return () => window.removeEventListener('cae:engagements-changed', load);
  }, [companyId]);

  const pickEngagement = (id: string) => {
    const e = engagements.find(x => x.id === id);
    setEngagement(e ? { id: e.id, label: e.label, audit_type: e.audit_type } : null);
  };

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

      {/* Engagement (audit) selector — scopes every screen and report */}
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <ClipboardCheck className="w-4 h-4 text-gold shrink-0" />
        <select
          aria-label="Audit engagement"
          value={engagement?.id || ''}
          onChange={e => pickEngagement(e.target.value)}
          className="bg-navy-700 border border-navy-border text-sm text-gray-200 rounded-lg px-2 py-1.5 max-w-[340px] focus:outline-none focus:border-gold"
        >
          <option value="">Continuous monitoring (no engagement)</option>
          {engagements.map(e => <option key={e.id} value={e.id}>{e.label}</option>)}
        </select>
        {engagement && (
          <span className={`text-xs font-semibold px-2 py-0.5 rounded border whitespace-nowrap ${engagement.audit_type === 'statutory'
            ? 'bg-blue-900/40 text-blue-300 border-blue-800/60' : 'bg-purple-900/40 text-purple-300 border-purple-800/60'}`}>
            {AUDIT_TYPE_LABEL[engagement.audit_type]}
          </span>
        )}
        <button onClick={() => navigate('/engagements')} className="text-xs text-gray-500 hover:text-gold whitespace-nowrap">
          Manage
        </button>
      </div>

      <div className="flex items-center gap-3">
        <button aria-label="Notifications" className="relative p-2 text-gray-400 hover:text-gray-100">
          <Bell className="w-5 h-5" />
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

        <button aria-label="Sign out" onClick={handleLogout} className="btn-ghost flex items-center gap-1 text-sm text-gray-400 hover:text-red-400">
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
