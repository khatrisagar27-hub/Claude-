import { LogOut, Bell, ChevronDown } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';

export default function Topbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try { await apiClient.post('/auth/logout'); } catch {}
    logout();
    navigate('/login');
  };

  return (
    <header className="h-14 bg-navy-800 border-b border-navy-border flex items-center justify-between px-6">
      <div className="text-sm text-gray-400">
        Continuous Audit Engine — <span className="text-gray-200 font-medium">Real-time Risk Intelligence</span>
      </div>
      <div className="flex items-center gap-4">
        <button className="relative p-2 text-gray-400 hover:text-gray-100">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>
        <div className="flex items-center gap-2 text-sm">
          <div className="w-7 h-7 rounded-full bg-gold/20 border border-gold/40 flex items-center justify-center text-gold text-xs font-semibold">
            {user?.full_name?.[0] || 'U'}
          </div>
          <span className="text-gray-300">{user?.full_name || 'User'}</span>
          <span className="text-xs text-gray-500 capitalize">{user?.role}</span>
        </div>
        <button onClick={handleLogout} className="btn-ghost flex items-center gap-1 text-sm">
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
