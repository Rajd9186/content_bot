import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import type { PipelineSSEEvent } from "@/types/api";

const api = axios.create({
  baseURL: typeof window !== "undefined"
    ? localStorage.getItem("acip-api-url") || "http://localhost:8000/api/v1"
    : "http://localhost:8000/api/v1",
  timeout: 0,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem("acip-api-url");
    if (stored) config.baseURL = stored;
    const token = localStorage.getItem("acip-token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("acip-token");
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export async function apiGet<T>(url: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  const cleanParams: Record<string, string> = {};
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) cleanParams[k] = String(v);
    });
  }
  const { data } = await api.get<T>(url, { params: Object.keys(cleanParams).length > 0 ? cleanParams : undefined });
  return data;
}

export async function apiPost<T>(
  url: string,
  body?: unknown,
  params?: Record<string, string | number | boolean | undefined>,
  timeout?: number,
): Promise<T> {
  const cleanParams: Record<string, string> = {};
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) cleanParams[k] = String(v);
    });
  }
  const { data } = await api.post<T>(url, body ?? null, {
    params: Object.keys(cleanParams).length > 0 ? cleanParams : undefined,
    ...(timeout !== undefined ? { timeout } : {}),
  });
  return data;
}

export async function apiDelete<T>(url: string): Promise<T> {
  const { data } = await api.delete<T>(url);
  return data;
}

export function createSSEConnection(
  path: string,
  onEvent: (event: PipelineSSEEvent) => void,
  onError?: (error: Event) => void,
  onOpen?: () => void,
): EventSource {
  const baseUrl = typeof window !== "undefined"
    ? localStorage.getItem("acip-api-url") || "http://localhost:8000/api/v1"
    : "http://localhost:8000/api/v1";
  const url = `${baseUrl}${path}`;
  const es = new EventSource(url);
  es.onopen = () => onOpen?.();
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      onEvent(data);
    } catch {}
  };
  es.onerror = (e) => {
    onError?.(e);
    es.close();
  };
  return es;
}

export async function validateApiConnection(): Promise<boolean> {
  try {
    const { data } = await api.get<{ status: string }>("/health");
    return data.status === "ok";
  } catch {
    return false;
  }
}

export default api;
