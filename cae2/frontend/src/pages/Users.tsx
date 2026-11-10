import { FormEvent, useState } from 'react'
import { api, session, type User } from '../api'
import { ErrorNote, Page, useAction, useLoad } from '../ui'

export default function Users() {
  const users = useLoad<User[]>(() => api('/users'))
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'staff' })
  const { busy, error, run } = useAction()
  const me = session.get()?.user
  const set = (key: string) => (e: any) => setForm({ ...form, [key]: e.target.value })
  const add = (e: FormEvent) => { e.preventDefault(); run(async () => { await api('/users', 'POST', form); setForm({ name: '', email: '', password: '', role: 'staff' }); await users.reload() }) }
  const patch = (id: number, body: unknown) => run(async () => { await api(`/users/${id}`, 'PATCH', body); await users.reload() })

  return (
    <Page heading="Users" sub="Staff can upload data, run audits, comment and raise queries. Managers and partners also conclude on findings and change rules and settings. Partners manage users.">
      <ErrorNote error={error || users.error} />
      <form onSubmit={add} className="card mb-6 grid gap-3 p-5 md:grid-cols-5">
        <input className="input" placeholder="Name" required value={form.name} onChange={set('name')} />
        <input className="input" placeholder="Email" type="email" required value={form.email} onChange={set('email')} />
        <input className="input" placeholder="Password (10+ characters)" type="password" required minLength={10} autoComplete="new-password" value={form.password} onChange={set('password')} />
        <select className="input" value={form.role} onChange={set('role')}><option value="staff">Staff</option><option value="manager">Manager</option><option value="partner">Partner</option></select>
        <button className="btn" disabled={busy}>Add user</button>
      </form>
      <div className="card overflow-hidden">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50"><tr>{['Name', 'Email', 'Role', 'Access'].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
          <tbody className="divide-y divide-slate-100">
            {users.data?.map((u) => (
              <tr key={u.id} className={u.is_active ? '' : 'text-slate-400'}>
                <td className="td font-medium">{u.name}</td>
                <td className="td">{u.email}</td>
                <td className="td">
                  <select className="input w-32" value={u.role} disabled={busy || u.id === me?.id} onChange={(e) => patch(u.id, { role: e.target.value })}>
                    <option value="staff">Staff</option><option value="manager">Manager</option><option value="partner">Partner</option>
                  </select>
                </td>
                <td className="td">{u.id === me?.id ? 'You' : <button className="text-indigo-700 hover:underline" disabled={busy} onClick={() => patch(u.id, { is_active: !u.is_active })}>{u.is_active ? 'Disable' : 'Enable'}</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Page>
  )
}
