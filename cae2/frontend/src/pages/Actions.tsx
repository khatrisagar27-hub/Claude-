import { Link } from 'react-router-dom'
import { api } from '../api'
import { useEngagement } from '../App'
import { Empty, ErrorNote, Page, useLoad } from '../ui'

export default function Actions() {
  const { eng } = useEngagement()
  const list = useLoad<any[]>(() => api(`/engagements/${eng.id}/actions`), [eng.id])
  const open = list.data?.filter((a) => !a.is_done).length ?? 0
  return (
    <Page heading="Remediation actions" sub={list.data ? `${open} open of ${list.data.length}. Actions are added and ticked off on each finding.` : undefined}>
      <ErrorNote error={list.error} />
      {list.data?.length === 0 && <Empty>No actions recorded yet.</Empty>}
      {!!list.data?.length && (
        <div className="card overflow-hidden">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50"><tr>{['Action', 'Finding', 'Owner', 'Due', 'State'].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
            <tbody className="divide-y divide-slate-100">
              {list.data.map((a) => (
                <tr key={a.id}>
                  <td className="td">{a.description}</td>
                  <td className="td"><Link className="text-indigo-700 hover:underline" to={`../findings/${a.finding_id}`}>{a.rule_code}</Link> <span className="text-slate-500">{a.finding}</span></td>
                  <td className="td">{a.owner || '—'}</td>
                  <td className="td whitespace-nowrap">{a.due_date ? a.due_date.split('-').reverse().join('-') : '—'}</td>
                  <td className="td">{a.is_done ? <span className="text-emerald-700">Done</span> : a.overdue ? <span className="font-medium text-red-700">Overdue</span> : 'Open'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Page>
  )
}
