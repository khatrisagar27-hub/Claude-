import { useRef, useState } from 'react'
import { api, download } from '../api'
import { useEngagement } from '../App'
import { ErrorNote, Page, useAction, useLoad, when } from '../ui'

function DatasetCard({ ds, count, last, engId, closed, onDone }: { ds: any; count: number; last?: any; engId: number; closed: boolean; onDone: () => void }) {
  const input = useRef<HTMLInputElement>(null)
  const [mode, setMode] = useState('replace')
  const [open, setOpen] = useState(false)
  const { busy, error, run } = useAction()

  const upload = (file?: File) => {
    if (!file) return
    const form = new FormData()
    form.append('file', file)
    form.append('mode', mode)
    run(async () => { await api(`/engagements/${engId}/data/${ds.key}`, 'POST', form); onDone() }).finally(() => { if (input.current) input.current.value = '' })
  }

  return (
    <div className="card p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">{ds.label}</h3>
          <p className="mt-0.5 text-xs text-slate-500">{count ? `${count.toLocaleString('en-IN')} rows loaded` : 'Nothing loaded'}{ds.key === 'ledger' && ' · accepts Tally Day Book XML'}</p>
        </div>
        <button className="text-xs text-indigo-700 hover:underline" onClick={() => download(`/datasets/${ds.key}/template`, `${ds.key}_template.xlsx`)}>Template</button>
      </div>
      <ErrorNote error={error} />
      <div className="mt-3 flex gap-2">
        <select className="input w-28" value={mode} onChange={(e) => setMode(e.target.value)} disabled={closed}>
          <option value="replace">Replace</option><option value="append">Add to</option>
        </select>
        <input ref={input} type="file" accept=".xlsx,.xlsm,.xls,.csv,.xml" className="hidden" onChange={(e) => upload(e.target.files?.[0])} />
        <button className="btn-ghost flex-1" disabled={busy || closed} onClick={() => input.current?.click()}>{busy ? 'Uploading…' : 'Choose file'}</button>
      </div>
      {last && (
        <div className="mt-3 border-t border-slate-100 pt-3 text-xs text-slate-600">
          <div className="truncate" title={last.filename}>Last: {last.filename} · {when(last.created_at)}</div>
          <div className="mt-1">
            <span className="text-emerald-700">{last.rows_loaded} loaded</span>
            {last.rows_rejected > 0 && <> · <button className="font-medium text-red-700 underline" onClick={() => setOpen(!open)}>{last.rows_rejected} rejected</button></>}
          </div>
          {last.notes.map((n: string) => <div key={n} className="mt-1 text-amber-800">Note: {n}</div>)}
          {last.unmapped_columns.length > 0 && <div className="mt-1">Columns ignored: {last.unmapped_columns.join(', ')}</div>}
          {open && (
            <ul className="mt-2 max-h-48 overflow-auto rounded bg-red-50 p-2 text-red-900">
              {last.errors.map((e: any) => <li key={e.row}>Row {e.row}: {e.problems.join('; ')}</li>)}
            </ul>
          )}
        </div>
      )}
      <details className="mt-3 text-xs text-slate-500">
        <summary className="cursor-pointer">Columns</summary>
        <ul className="mt-1 space-y-0.5">
          {ds.columns.map((c: any) => <li key={c.name}><span className={c.required ? 'font-semibold text-slate-800' : ''}>{c.name}</span>{c.required && ' (required)'}{c.help && ` — ${c.help}`}</li>)}
        </ul>
      </details>
    </div>
  )
}

export default function Data() {
  const { eng } = useEngagement()
  const datasets = useLoad<any[]>(() => api('/datasets'))
  const loaded = useLoad<any>(() => api(`/engagements/${eng.id}/data`), [eng.id])
  return (
    <Page heading="Data" sub="Upload Excel or CSV exports. Headings are matched automatically; rows that fail validation are rejected with the reason and never guessed. Run the audit again after uploading.">
      <ErrorNote error={datasets.error || loaded.error} />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {datasets.data?.map((ds) => (
          <DatasetCard key={ds.key} ds={ds} engId={eng.id} closed={eng.is_closed} onDone={loaded.reload}
            count={loaded.data?.counts[ds.key] || 0} last={loaded.data?.batches.find((b: any) => b.dataset === ds.key)} />
        ))}
      </div>
    </Page>
  )
}
