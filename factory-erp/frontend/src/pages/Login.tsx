import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { client } from "../api/client";
import { Plant } from "../api/types";
import { useAuthStore } from "../store/authStore";

export function Login() {
  const [email, setEmail] = useState("admin@factory.local");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const setToken = useAuthStore((s) => s.setToken);
  const setPlantId = useAuthStore((s) => s.setPlantId);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data } = await client.post("/auth/login", { email, password });
      setToken(data.access_token);
      // Set companyId/plantId right after login — without this the
      // dashboard has nothing to scope its queries to and hangs loading.
      const plants = await client.get<Plant[]>("/plants", {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      if (plants.data.length > 0) setPlantId(plants.data[0].id);
      navigate("/");
    } catch {
      setError("Incorrect email or password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <form onSubmit={handleSubmit} className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="mb-4 text-lg font-semibold text-slate-900">Factory ERP</h1>
        <label className="mb-1 block text-sm text-slate-600">Email</label>
        <input
          className="mb-3 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          type="email"
          required
        />
        <label className="mb-1 block text-sm text-slate-600">Password</label>
        <input
          className="mb-4 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          type="password"
          required
        />
        {error && <div className="mb-3 text-sm text-red-600">{error}</div>}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
