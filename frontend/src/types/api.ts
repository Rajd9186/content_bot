export interface ApiError {
  code: string;
  message: string;
  details?: Array<{
    field?: string;
    message: string;
    code: string;
  }>;
}

export interface ApiMeta {
  requestId: string;
  timestamp: string;
  correlationId: string;
  version: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: ApiError | null;
  meta: ApiMeta;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface HealthStatus {
  status: string;
  version: string;
  uptimeSeconds: number;
}

export interface ReadinessStatus {
  status: string;
  checks: Record<string, string>;
}

export interface User {
  id: string;
  email: string;
  displayName: string;
  workspaceId: string;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
}
