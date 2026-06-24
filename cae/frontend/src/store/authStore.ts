import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '../types';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  companyId: string | null;
  setUser: (user: User) => void;
  setTokens: (access: string, refresh: string) => void;
  setCompanyId: (id: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      companyId: null,
      setUser: (user) => set({ user }),
      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
      setCompanyId: (companyId) => set({ companyId }),
      logout: () => set({ user: null, accessToken: null, refreshToken: null, companyId: null }),
    }),
    { name: 'cae-auth' }
  )
);
