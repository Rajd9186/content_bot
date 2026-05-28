import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface ApiError {
  code: string;
  message: string;
  details?: Array<{ field?: string; message: string; code: string }>;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: ApiError | null;
  meta: {
    requestId: string;
    timestamp: string;
    correlationId: string;
    version: string;
  };
}

function correlationIdInterceptor(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
  config.headers.set("X-Correlation-ID", crypto.randomUUID());
  return config;
}

function responseErrorInterceptor(error: AxiosError<ApiResponse<unknown>>): Promise<never> {
  const message = error.response?.data?.error?.message || "An unexpected error occurred";
  const code = error.response?.data?.error?.code || "UNKNOWN_ERROR";

  console.error(`[API Error] ${code}: ${message}`, {
    status: error.response?.status,
    correlationId: error.config?.headers?.["X-Correlation-ID"],
  });

  return Promise.reject(error);
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

apiClient.interceptors.request.use(correlationIdInterceptor);
apiClient.interceptors.response.use((response) => response, responseErrorInterceptor);

export async function apiGet<T>(path: string, params?: Record<string, unknown>): Promise<T> {
  const response = await apiClient.get<ApiResponse<T>>(path, { params });
  if (!response.data.success || response.data.data === null) {
    throw new Error(response.data.error?.message || "Request failed");
  }
  return response.data.data;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await apiClient.post<ApiResponse<T>>(path, body);
  if (!response.data.success || response.data.data === null) {
    throw new Error(response.data.error?.message || "Request failed");
  }
  return response.data.data;
}

export async function apiPut<T>(path: string, body?: unknown): Promise<T> {
  const response = await apiClient.put<ApiResponse<T>>(path, body);
  if (!response.data.success || response.data.data === null) {
    throw new Error(response.data.error?.message || "Request failed");
  }
  return response.data.data;
}

export async function apiDelete<T>(path: string): Promise<T> {
  const response = await apiClient.delete<ApiResponse<T>>(path);
  if (!response.data.success || response.data.data === null) {
    throw new Error(response.data.error?.message || "Request failed");
  }
  return response.data.data;
}
