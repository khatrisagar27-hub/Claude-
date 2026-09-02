import { NavLink, Outlet } from "react-router-dom";

import { useAuthStore } from "../store/authStore";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/machines", label: "Machines" },
  { to: "/stock", label: "Stock" },
  { to: "/production", label: "Production" },
];

export function Layout() {
  const logout = useAuthStore((s) => s.logout);

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-6">
            <span className="text-sm font-semibold text-slate-900">Factory ERP</span>
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.end}
                className={({ isActive }) =>
                  `text-sm ${isActive ? "font-medium text-slate-900" : "text-slate-500 hover:text-slate-700"}`
                }
              >
                {l.label}
              </NavLink>
            ))}
          </div>
          <button onClick={logout} className="text-sm text-slate-500 hover:text-slate-700">
            Sign out
          </button>
        </div>
      </nav>
      <Outlet />
    </div>
  );
}
