import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart3, Lock, Mail } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import axios from 'axios';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setTokens, setUser } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/auth/login', { email, password });
      setTokens(res.data.access_token, res.data.refresh_token);
      const me = await axios.get('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${res.data.access_token}` },
      });
      setUser(me.data);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-navy-900 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gold/10 border border-gold/30 rounded-2xl mb-4">
            <BarChart3 className="w-8 h-8 text-gold" />
          </div>
          <h1 className="text-2xl font-bold text-white">Continuous Audit Engine</h1>
          <p className="text-gray-500 text-sm mt-1">AI-Powered Internal Audit Platform</p>
        </div>

        {/* Form */}
        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" />
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="partner@firm.com"
                  required
                  className="input-field pl-9"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" />
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="input-field pl-9"
                />
              </div>
            </div>

            {error && (
              <div className="text-sm text-red-400 bg-red-900/20 border border-red-800/50 rounded-md px-3 py-2">
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
              {loading ? (
                <span className="w-4 h-4 border-2 border-navy-900/40 border-t-navy-900 rounded-full animate-spin" />
              ) : null}
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-600 mt-6">
          Sagar Khatri & Associates — Internal Audit Platform
        </p>
      </div>
    </div>
  );
}
