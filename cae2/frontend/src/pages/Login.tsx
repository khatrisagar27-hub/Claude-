import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, session } from '../api'
import { ErrorNote, useAction, useLoad } from '../ui'

export default function Login() {
  const navigate = useNavigate()
  const setup = useLoad<{ needed: boolean }>(() => api('/setup'))
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const { busy, error, run } = useAction()
  const first = setup.data?.needed

  const submit = (e: FormEvent) => {
    e.preventDefault()
    run(async () => {
      session.set(await api(first ? '/setup' : '/login', 'POST', form))
      navigate('/')
    })
  }
  const field = (key: keyof typeof form) => ({ value: form[key], onChange: (e: any) => setForm({ ...form, [key]: e.target.value }) })

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-900 px-4">
      <form onSubmit={submit} className="w-full max-w-sm rounded-lg bg-white p-7 shadow-xl">
        <h1 className="text-lg font-semibold">Continuous Audit Engine</h1>
        <p className="mb-5 mt-1 text-sm text-slate-500">
          {first ? 'First run: create the partner account that will administer this installation.' : 'Sign in to continue.'}
        </p>
        <ErrorNote error={error || setup.error} />
        {first && (<><label className="label">Your name</label><input className="input mb-3" required {...field('name')} /></>)}
        <label className="label">Email</label>
        <input className="input mb-3" type="email" required autoComplete="username" {...field('email')} />
        <label className="label">Password{first && ' (10 characters or more)'}</label>
        <input className="input mb-5" type="password" required minLength={first ? 10 : 1} autoComplete={first ? 'new-password' : 'current-password'} {...field('password')} />
        <button className="btn w-full" disabled={busy || setup.loading}>{first ? 'Create account' : 'Sign in'}</button>
      </form>
    </div>
  )
}
