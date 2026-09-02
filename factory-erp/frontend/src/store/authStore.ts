import { create } from "zustand";

interface AuthState {
  token: string | null;
  plantId: string | null;
  setToken: (token: string | null) => void;
  setPlantId: (plantId: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("token"),
  plantId: localStorage.getItem("plantId"),
  setToken: (token) => {
    if (token) localStorage.setItem("token", token);
    else localStorage.removeItem("token");
    set({ token });
  },
  setPlantId: (plantId) => {
    if (plantId) localStorage.setItem("plantId", plantId);
    else localStorage.removeItem("plantId");
    set({ plantId });
  },
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("plantId");
    set({ token: null, plantId: null });
  },
}));
