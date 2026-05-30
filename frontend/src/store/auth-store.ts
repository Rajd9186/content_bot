import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserProfile, AuthTokens } from "@/types/api";
import api from "@/lib/api";

interface AuthState {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const { data } = await api.post<{ user: UserProfile } & AuthTokens>("/auth/login", { email, password });
          localStorage.setItem("acip-token", data.accessToken);
          set({
            user: data.user,
            token: data.accessToken,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (e: unknown) {
          const msg = e instanceof Error ? e.message : "Login failed";
          set({ isLoading: false, error: msg });
          throw e;
        }
      },

      logout: () => {
        localStorage.removeItem("acip-token");
        set({ user: null, token: null, isAuthenticated: false, error: null });
      },

      checkAuth: async () => {
        const token = get().token;
        if (!token) return;
        try {
          const { data } = await api.get<UserProfile>("/auth/me");
          set({ user: data, isAuthenticated: true });
        } catch {
          get().logout();
        }
      },
    }),
    { name: "acip-auth", partialize: (state) => ({ user: state.user, token: state.token }) },
  ),
);
