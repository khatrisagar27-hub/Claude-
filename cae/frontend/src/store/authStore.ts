import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, EngagementRef } from '../types';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  companyId: string | null;
  /** Selected audit engagement; null = continuous monitoring outside any engagement */
  engagement: EngagementRef | null;
  setUser: (user: User) => void;
  setTokens: (access: string, refresh: string) => void;
  setCompanyId: (id: string) => void;
  setEngagement: (e: EngagementRef | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      companyId: null,
      engagement: null,
      setUser: (user) => set({ user }),
      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
      setCompanyId: (companyId) => set((st) => ({ companyId, engagement: st.companyId === companyId ? st.engagement : null })),
      setEngagement: (engagement) => set({ engagement }),
      logout: () => set({ user: null, accessToken: null, refreshToken: null, companyId: null, engagement: null }),
    }),
    { name: 'cae-auth' }
  )
);
