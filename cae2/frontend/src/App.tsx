import { NavLink, Navigate, Outlet, Route, Routes, useNavigate, useOutletContext, useParams } from 'react-router-dom'
import { api, session } from './api'
import Data from './pages/Data'
import Engagements from './pages/Engagements'
import FindingDetail from './pages/FindingDetail'
import Findings from './pages/Findings'
import Gst from './pages/Gst'
import Login from './pages/Login'
import Overview from './pages/Overview'
import Rules from './pages/Rules'
import Settings from './pages/Settings'
import Users from './pages/Users'
import WorkingCapital from './pages/WorkingCapital'
import Actions from './pages/Actions'
import { ErrorNote, useLoad } from './ui'

export type Engagement = {
  id: number; client_name: string; client_gstin: string | null; name: string; kind: string; period_start: string; period_end: string
  materiality: number; trivial_threshold: number; settings: Record<string, any>; is_closed: boolean; open_findings: number
}
export type EngagementContext = { eng: Engagement; reload: () => Promise<void> }
export const useEngagement = () => useOutletContext<EngagementContext>()

function Shell() {
  const me = session.get()
  const navigate = useNavigate()
  if (!me) return <Navigate to="/login" replace />
  return (
    <div className="min-h-screen">
      <header className="flex h-12 items-center justify-between bg-slate-900 px-6 text-sm text-slate-200">
        <NavLink to="/" className="font-semibold tracking-wide text-white">Continuous Audit Engine</NavLink>
        <div className="flex items-center gap-4">
          {me.user.role === 'partner' && <NavLink to="/users" className="hover:text-white">Users</NavLink>}
          <span className="text-slate-400">{me.user.name} · {me.user.role}</span>
          <button className="hover:text-white" onClick={() => { session.clear(); navigate('/login') }}>Sign out</button>
        </div>
      </header>
      <Outlet />
    </div>
  )
}

const TABS = [['', 'Overview'], ['data', 'Data'], ['findings', 'Findings'], ['actions', 'Actions'], ['gst', 'GST'], ['working-capital', 'Working capital'], ['rules', 'Rules'], ['settings', 'Settings']]

function EngagementLayout() {
  const { id } = useParams()
  const { data: eng, error, reload } = useLoad<Engagement>(() => api(`/engagements/${id}`), [id])
  if (error) return <div className="p-6"><ErrorNote error={error} /></div>
  if (!eng) return <div className="p-6 text-sm text-slate-500">Loading…</div>
  return (
    <div>
      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 pt-4">
          <div className="flex flex-wrap items-baseline gap-x-3">
            <h2 className="text-lg font-semibold">{eng.client_name}</h2>
            <span className="text-sm text-slate-500">{eng.name} · {eng.period_start.split('-').reverse().join('-')} to {eng.period_end.split('-').reverse().join('-')}</span>
            {eng.is_closed && <span className="rounded bg-slate-200 px-2 py-0.5 text-xs font-medium">Closed — read only</span>}
          </div>
          <nav className="mt-3 flex gap-1 overflow-x-auto">
            {TABS.map(([path, label]) => (
              <NavLink key={path} to={path} end={path === ''}
                className={({ isActive }) => `whitespace-nowrap border-b-2 px-3 py-2 text-sm ${isActive ? 'border-indigo-600 font-medium text-indigo-700' : 'border-transparent text-slate-600 hover:text-slate-900'}`}>
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>
      <Outlet context={{ eng, reload } satisfies EngagementContext} />
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Shell />}>
        <Route index element={<Engagements />} />
        <Route path="users" element={<Users />} />
        <Route path="e/:id" element={<EngagementLayout />}>
          <Route index element={<Overview />} />
          <Route path="data" element={<Data />} />
          <Route path="findings" element={<Findings />} />
          <Route path="findings/:findingId" element={<FindingDetail />} />
          <Route path="actions" element={<Actions />} />
          <Route path="gst" element={<Gst />} />
          <Route path="working-capital" element={<WorkingCapital />} />
          <Route path="rules" element={<Rules />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
