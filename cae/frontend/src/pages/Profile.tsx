import { useState } from 'react';
import { ArrowLeft, User, Mail, Shield, Building2, Lock, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import apiClient from '../api/client';

const ROLE_LABELS: Record<string, string> = {
  super_admin: 'Super Admin',
  partner: 'Partner',
  manager: 'Manager',
  auditor: 'Auditor',
  cfo: 'CFO',
  management: 'Management',
  process_owner: 'Process Owner',
  client_user: 'Client User',
};

export default function Profile() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    if (newPassword !== confirmPassword) {
      setError('New passwords do not match.');
      return;
    }
    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters.');
      return;
    }
    setLoading(true);
    try {
      await apiClient.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSuccess('Password changed successfully.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to change password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="text-gray-500 hover:text-gray-300">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-xl font-bold text-white">My Profile</h1>
      </div>

      {/* User Info Card */}
      <div className="card space-y-4">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Account Information</h2>

        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-gold/20 border-2 border-gold/40 flex items-center justify-center text-gold text-2xl font-bold">
            {user?.full_name?.[0] || 'U'}
          </div>
          <div>
            <div className="text-white text-lg font-semibold">{user?.full_name}</div>
            <div className="text-gray-500 text-sm">{ROLE_LABELS[user?.role || ''] || user?.role}</div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-navy-700 rounded-lg flex items-center justify-center">
              <Mail className="w-4 h-4 text-gray-400" />
            </div>
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider">Email</div>
              <div className="text-sm text-gray-200">{user?.email}</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-navy-700 rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-gray-400" />
            </div>
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider">Role</div>
              <div className="text-sm text-gray-200 capitalize">{ROLE_LABELS[user?.role || ''] || user?.role}</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-navy-700 rounded-lg flex items-center justify-center">
              <User className="w-4 h-4 text-gray-400" />
            </div>
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider">User ID</div>
              <div className="text-xs text-gray-500 font-mono">{user?.id}</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-navy-700 rounded-lg flex items-center justify-center">
              <Building2 className="w-4 h-4 text-gray-400" />
            </div>
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider">Tenant ID</div>
              <div className="text-xs text-gray-500 font-mono">{user?.tenant_id}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Change Password */}
      <div className="card space-y-4">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-2">
          <Lock className="w-3.5 h-3.5" />
          Change Password
        </h2>

        <form onSubmit={handleChangePassword} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
              Current Password
            </label>
            <input
              type="password"
              value={currentPassword}
              onChange={e => setCurrentPassword(e.target.value)}
              required
              placeholder="••••••••"
              className="input-field"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
              New Password
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              required
              placeholder="••••••••"
              className="input-field"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
              Confirm New Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              required
              placeholder="••••••••"
              className="input-field"
            />
          </div>

          {error && (
            <div className="text-sm text-red-400 bg-red-900/20 border border-red-800/50 rounded-md px-3 py-2">
              {error}
            </div>
          )}

          {success && (
            <div className="text-sm text-green-400 bg-green-900/20 border border-green-800/50 rounded-md px-3 py-2 flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              {success}
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
            {loading ? (
              <span className="w-4 h-4 border-2 border-navy-900/40 border-t-navy-900 rounded-full animate-spin" />
            ) : null}
            {loading ? 'Changing…' : 'Change Password'}
          </button>
        </form>
      </div>
    </div>
  );
}
