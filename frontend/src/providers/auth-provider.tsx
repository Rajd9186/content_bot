"use client";

import { type ReactNode, createContext, useContext, useEffect, type FC } from "react";
import { useAuthStore, type AuthState } from "@/stores/auth-store";
import { apiClient } from "@/lib/api-client";

interface AuthContextValue {
  user: AuthState["user"];
  token: AuthState["token"];
  isAuthenticated: AuthState["isAuthenticated"];
  isLoading: AuthState["isLoading"];
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const { user, token, isAuthenticated, isLoading, setAuth, clearAuth, setLoading } =
    useAuthStore();

  useEffect(() => {
    if (token) {
      apiClient.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    } else {
      delete apiClient.defaults.headers.common["Authorization"];
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      setLoading(true);
      apiClient
        .get("/identity/me")
        .then((response) => {
          if (response.data.success && response.data.data) {
            setAuth(response.data.data as never, token);
          } else {
            clearAuth();
          }
        })
        .catch(() => {
          clearAuth();
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    const response = await apiClient.post("/identity/login", { email, password });
    if (response.data.success && response.data.data) {
      const { user: userData, token: newToken } = response.data.data as {
        user: never;
        token: string;
      };
      setAuth(userData, newToken);
    }
  };

  const logout = (): void => {
    clearAuth();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
