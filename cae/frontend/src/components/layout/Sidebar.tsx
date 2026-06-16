import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, AlertTriangle, MessageSquare, Wrench,
  BookOpen, Activity, TrendingUp, Receipt, Package,
  BarChart3, Upload, FileText, Shield
} from 'lucide-react';

const nav = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/exceptions', icon: AlertTriangle, label: 'Exceptions' },
  { to: '/queries', icon: MessageSquare, label: 'Queries' },
  { to: '/remediation', icon: Wrench, label: 'Remediation' },
  { to: '/rules', icon: BookOpen, label: 'Audit Rules' },
  { to: '/risk', icon: Activity, label: 'Risk Heatmap' },
  { to: '/fraud', icon: Shield, label: 'Fraud Analytics' },
  { to: '/gst', icon: Receipt, label: 'GST' },
  { to: '/working-capital', icon: TrendingUp, label: 'Working Capital' },
  { to: '/ingestion', icon: Upload, label: 'Data Ingestion' },
  { to: '/reports', icon: FileText, label: 'Reports' },
];

export default function Sidebar() {
  return (
    <div className="w-56 bg-navy-800 border-r border-navy-border flex flex-col">
      <div className="p-4 border-b border-navy-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gold rounded-md flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-navy-900" />
          </div>
          <div>
            <div className="text-sm font-bold text-gold">CAE</div>
            <div className="text-[10px] text-gray-500 uppercase tracking-wider">Audit Engine</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `nav-link ${isActive ? 'active' : ''}`
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-navy-border">
        <div className="text-xs text-gray-600 text-center">
          Powered by Anthropic Claude
        </div>
      </div>
    </div>
  );
}
