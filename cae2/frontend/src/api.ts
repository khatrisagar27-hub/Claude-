// Thin fetch wrapper: adds the token, turns error responses into Error(message).

export type User = { id: number; email: string; name: string; role: 'partner' | 'manager' | 'staff'; is_active: boolean }

const KEY = 'cae.session'

export const session = {
  get(): { token: string; user: User } | null {
    try {
      return JSON.parse(localStorage.getItem(KEY) || 'null')
    } catch {
      return null
    }
  },
  set(value: { token: string; user: User }) {
    localStorage.setItem(KEY, JSON.stringify(value))
  },
  clear() {
    localStorage.removeItem(KEY)
  },
}

export const canReview = () => ['partner', 'manager'].includes(session.get()?.user.role ?? '')

async function send(path: string, init: RequestInit): Promise<Response> {
  const token = session.get()?.token
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: { ...(init.headers || {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  })
  if (response.status === 401 && token) {
    session.clear()
    window.location.assign('/login')
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') message = body.detail
      else if (Array.isArray(body.detail)) message = body.detail.map((d: any) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join('; ')
    } catch {
      /* non-JSON error body */
    }
    throw new Error(message)
  }
  return response
}

export async function api<T = any>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const init: RequestInit = { method }
  if (body instanceof FormData) init.body = body
  else if (body !== undefined) {
    init.body = JSON.stringify(body)
    init.headers = { 'Content-Type': 'application/json' }
  }
  return (await send(path, init)).json()
}

export async function download(path: string, fallbackName: string) {
  const response = await send(path, { method: 'GET' })
  const name = /filename="([^"]+)"/.exec(response.headers.get('Content-Disposition') || '')?.[1] || fallbackName
  const url = URL.createObjectURL(await response.blob())
  const link = Object.assign(document.createElement('a'), { href: url, download: name })
  link.click()
  URL.revokeObjectURL(url)
}
