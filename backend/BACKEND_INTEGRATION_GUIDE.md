# Backend Integration & API Communication Guide

## Part 1: API Architecture Patterns

### RESTful API Communication (Recommended for FastAPI)

#### Base API Service Setup
```javascript
// services/apiClient.js
class APIClient {
  constructor(baseURL, timeout = 30000) {
    this.baseURL = baseURL;
    this.timeout = timeout;
    this.token = this.getStoredToken();
    this.retryAttempts = 3;
    this.retryDelay = 1000; // ms
  }

  // Configuration
  getStoredToken() {
    return localStorage.getItem('accessToken');
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem('accessToken', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('accessToken');
  }

  // Request builder
  async request(method, endpoint, options = {}) {
    const { data, headers = {}, retry = true, ...rest } = options;
    
    const url = `${this.baseURL}${endpoint}`;
    const requestHeaders = {
      'Content-Type': 'application/json',
      ...headers,
      ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
    };

    const config = {
      method,
      headers: requestHeaders,
      timeout: this.timeout,
      ...(data && { body: JSON.stringify(data) }),
      ...rest,
    };

    // Implement retry logic
    for (let attempt = 0; attempt <= this.retryAttempts; attempt++) {
      try {
        const response = await this.fetchWithTimeout(url, config);
        return await this.handleResponse(response);
      } catch (error) {
        // Retry on network errors, not on client errors
        if (
          retry &&
          attempt < this.retryAttempts &&
          this.isRetryableError(error)
        ) {
          await this.delay(this.retryDelay * (attempt + 1));
          continue;
        }
        throw error;
      }
    }
  }

  // HTTP Methods
  get(endpoint, options) {
    return this.request('GET', endpoint, options);
  }

  post(endpoint, data, options) {
    return this.request('POST', endpoint, { ...options, data });
  }

  put(endpoint, data, options) {
    return this.request('PUT', endpoint, { ...options, data });
  }

  patch(endpoint, data, options) {
    return this.request('PATCH', endpoint, { ...options, data });
  }

  delete(endpoint, options) {
    return this.request('DELETE', endpoint, options);
  }

  // Batch requests
  async batch(requests) {
    return Promise.allSettled(
      requests.map(({ method, endpoint, data }) => {
        const httpMethod = method.toLowerCase();
        return this[httpMethod](endpoint, data);
      })
    );
  }

  // Helper: Fetch with timeout
  async fetchWithTimeout(url, config) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), config.timeout);

    try {
      return await fetch(url, { ...config, signal: controller.signal });
    } finally {
      clearTimeout(timeout);
    }
  }

  // Helper: Handle response
  async handleResponse(response) {
    const contentType = response.headers.get('content-type');
    const isJSON = contentType?.includes('application/json');
    const data = isJSON ? await response.json() : await response.text();

    // Handle authentication errors
    if (response.status === 401) {
      this.clearToken();
      window.location.href = '/login';
      throw new Error('Authentication expired. Please login again.');
    }

    // Handle server errors
    if (!response.ok) {
      const error = new Error(
        data?.message || `HTTP Error: ${response.status}`
      );
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  }

  // Helper: Check if error is retryable
  isRetryableError(error) {
    if (error instanceof TypeError) return true; // Network error
    if (error.name === 'AbortError') return true; // Timeout
    return false;
  }

  // Helper: Delay for retry
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

export default new APIClient(process.env.REACT_APP_API_URL);
```

### API Services (Feature-based)
```javascript
// services/userService.js
import api from './apiClient';

export const userService = {
  // Get all users
  async getUsers(page = 1, limit = 20) {
    return api.get('/users', {
      headers: { 'X-Page': page, 'X-Limit': limit },
    });
  },

  // Get single user
  async getUserById(id) {
    return api.get(`/users/${id}`);
  },

  // Create user
  async createUser(userData) {
    return api.post('/users', userData);
  },

  // Update user
  async updateUser(id, userData) {
    return api.put(`/users/${id}`, userData);
  },

  // Partial update
  async patchUser(id, partialData) {
    return api.patch(`/users/${id}`, partialData);
  },

  // Delete user
  async deleteUser(id) {
    return api.delete(`/users/${id}`);
  },

  // Batch operations
  async getUsersByIds(ids) {
    return api.post('/users/batch', { ids });
  },

  // Search users
  async searchUsers(query) {
    return api.get('/users/search', {
      headers: { 'X-Query': encodeURIComponent(query) },
    });
  },
};

// services/authService.js
import api from './apiClient';

export const authService = {
  async login(email, password) {
    const response = await api.post('/auth/login', { email, password });
    api.setToken(response.accessToken);
    return response;
  },

  async register(userData) {
    const response = await api.post('/auth/register', userData);
    api.setToken(response.accessToken);
    return response;
  },

  async refreshToken() {
    const refreshToken = localStorage.getItem('refreshToken');
    const response = await api.post('/auth/refresh', { refreshToken });
    api.setToken(response.accessToken);
    localStorage.setItem('refreshToken', response.refreshToken);
    return response;
  },

  async logout() {
    await api.post('/auth/logout');
    api.clearToken();
  },

  async getCurrentUser() {
    return api.get('/auth/me');
  },
};

// services/dataService.js (For analytics/structured finance data)
import api from './apiClient';

export const dataService = {
  async getDashboardData() {
    return api.get('/dashboard/metrics');
  },

  async getPortfolioData(portfolioId) {
    return api.get(`/portfolio/${portfolioId}`);
  },

  async getAnalytics(filters = {}) {
    return api.get('/analytics', { data: filters });
  },

  async exportData(format = 'csv') {
    const response = await api.get(`/export?format=${format}`, {
      headers: { 'Accept': `text/${format}` },
    });
    return response;
  },

  async uploadData(file) {
    const formData = new FormData();
    formData.append('file', file);

    return fetch(`${api.baseURL}/import`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${api.token}`,
      },
      body: formData,
    }).then(response => api.handleResponse(response));
  },
};
```

---

## Part 2: React Query/TanStack Query Integration

### Query Hooks Setup
```javascript
// hooks/useQuery.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService, authService, dataService } from '@/services';

// Users
export function useUsers(page = 1, limit = 20) {
  return useQuery({
    queryKey: ['users', page, limit],
    queryFn: () => userService.getUsers(page, limit),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // Cache for 10 minutes (was cacheTime)
  });
}

export function useUser(id) {
  return useQuery({
    queryKey: ['user', id],
    queryFn: () => userService.getUserById(id),
    enabled: !!id,
    staleTime: 10 * 60 * 1000,
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userData) => userService.createUser(userData),
    onSuccess: (newUser) => {
      // Update users list
      queryClient.setQueryData(['users'], (old) => ({
        ...old,
        data: [...(old?.data || []), newUser],
      }));

      // Invalidate to refetch
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (error) => {
      console.error('Error creating user:', error);
    },
  });
}

export function useUpdateUser(id) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userData) => userService.updateUser(id, userData),
    onSuccess: (updatedUser) => {
      // Update single user cache
      queryClient.setQueryData(['user', id], updatedUser);

      // Update list
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => userService.deleteUser(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.removeQueries({ queryKey: ['user', id] });
    },
  });
}

// Authentication
export function useAuth() {
  return useQuery({
    queryKey: ['auth', 'user'],
    queryFn: () => authService.getCurrentUser(),
    retry: false,
    staleTime: Infinity,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ email, password }) => authService.login(email, password),
    onSuccess: (user) => {
      queryClient.setQueryData(['auth', 'user'], user);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => authService.logout(),
    onSuccess: () => {
      queryClient.clear();
    },
  });
}

// Analytics/Data
export function useDashboardData() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dataService.getDashboardData(),
    staleTime: 2 * 60 * 1000, // Refresh every 2 minutes
  });
}

export function usePortfolioData(portfolioId) {
  return useQuery({
    queryKey: ['portfolio', portfolioId],
    queryFn: () => dataService.getPortfolioData(portfolioId),
    enabled: !!portfolioId,
    staleTime: 3 * 60 * 1000,
  });
}
```

### QueryClient Configuration
```javascript
// config/queryClient.js
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 10, // 10 minutes (cache time)
      retry: 1,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      retry: 1,
      retryDelay: 1000,
    },
  },
});

// App.jsx
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './config/queryClient';

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
    </QueryClientProvider>
  );
}
```

---

## Part 3: Error Handling & Loading States

### Error Handling Hook
```javascript
// hooks/useAsyncError.js
import { useState, useCallback } from 'react';

export function useAsyncError() {
  const [error, setError] = useState(null);

  const throwError = useCallback((error) => {
    setError(error);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return { error, throwError, clearError };
}

// Components/ErrorFallback.jsx
export function ErrorFallback({ error, retry }) {
  return (
    <div className="error-fallback">
      <h2>Something went wrong</h2>
      <p>{error?.message}</p>
      <div className="error-details">
        {error?.status && <p>Error Code: {error.status}</p>}
        {process.env.NODE_ENV === 'development' && (
          <pre>{JSON.stringify(error?.data, null, 2)}</pre>
        )}
      </div>
      <button onClick={retry}>Try Again</button>
    </div>
  );
}
```

### Loading & Error State Components
```javascript
// components/DataLoader.jsx
export function DataLoader({ isLoading, error, data, children, onRetry }) {
  if (isLoading) {
    return <Loading message="Loading data..." />;
  }

  if (error) {
    return (
      <div className="error-container">
        <h3>Failed to load data</h3>
        <p>{error?.message}</p>
        <Button onClick={onRetry}>Try Again</Button>
      </div>
    );
  }

  if (!data || (Array.isArray(data) && data.length === 0)) {
    return (
      <div className="empty-state">
        <p>No data available</p>
      </div>
    );
  }

  return children;
}

// Usage
function UsersList() {
  const { data, isLoading, error, refetch } = useUsers();

  return (
    <DataLoader
      isLoading={isLoading}
      error={error}
      data={data}
      onRetry={refetch}
    >
      {data?.map(user => (
        <UserCard key={user.id} user={user} />
      ))}
    </DataLoader>
  );
}
```

### Toast Notification Pattern
```javascript
// components/Toast.jsx
import { useState, useCallback } from 'react';

export function useToast() {
  const [toasts, setToasts] = useState([]);

  const add = useCallback((message, type = 'info', duration = 3000) => {
    const id = Date.now();
    const toast = { id, message, type };
    
    setToasts(prev => [...prev, toast]);

    if (duration > 0) {
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, duration);
    }

    return id;
  }, []);

  const remove = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return { toasts, add, remove };
}

// ToastContainer.jsx
export function ToastContainer({ toasts }) {
  return (
    <div className="toast-container">
      {toasts.map(toast => (
        <Toast key={toast.id} {...toast} />
      ))}
    </div>
  );
}
```

---

## Part 4: Real-time Data Updates (WebSocket)

### WebSocket Service
```javascript
// services/websocketService.js
class WebSocketService {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.listeners = new Map();
    this.messageQueue = [];
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect(token) {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;

          // Send auth
          this.send('auth', { token });

          // Flush message queue
          this.messageQueue.forEach(msg => this.send(msg.type, msg.data));
          this.messageQueue = [];

          resolve();
        };

        this.ws.onmessage = (event) => {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.attemptReconnect(token);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }

  send(type, data) {
    const message = JSON.stringify({ type, data, timestamp: Date.now() });

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    } else {
      this.messageQueue.push({ type, data });
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) callbacks.splice(index, 1);
    };
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return;
    const callbacks = this.listeners.get(event);
    const index = callbacks.indexOf(callback);
    if (index > -1) callbacks.splice(index, 1);
  }

  handleMessage(message) {
    const { type, data } = message;
    const callbacks = this.listeners.get(type) || [];
    callbacks.forEach(callback => callback(data));
  }

  attemptReconnect(token) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      setTimeout(() => this.connect(token), delay);
    }
  }
}

export const wsService = new WebSocketService(
  process.env.REACT_APP_WS_URL
);
```

### Real-time Hook
```javascript
// hooks/useRealtimeData.js
import { useEffect, useState } from 'react';
import { wsService } from '@/services/websocketService';

export function useRealtimeData(event) {
  const [data, setData] = useState(null);

  useEffect(() => {
    const unsubscribe = wsService.on(event, (newData) => {
      setData(newData);
    });

    return unsubscribe;
  }, [event]);

  return data;
}

// Usage
function RealtimeMetrics() {
  const metrics = useRealtimeData('metrics:update');

  return (
    <div>
      <h2>Live Metrics</h2>
      {metrics && <MetricsDisplay data={metrics} />}
    </div>
  );
}
```

---

## Part 5: Testing API Integration

### API Mocking (MSW - Mock Service Worker)
```javascript
// mocks/handlers.js
import { http, HttpResponse } from 'msw';

const API_BASE = process.env.REACT_APP_API_URL;

export const handlers = [
  // GET /users
  http.get(`${API_BASE}/users`, () => {
    return HttpResponse.json({
      data: [
        { id: 1, name: 'John Doe', email: 'john@example.com' },
        { id: 2, name: 'Jane Smith', email: 'jane@example.com' },
      ],
      total: 2,
    });
  }),

  // POST /users
  http.post(`${API_BASE}/users`, async ({ request }) => {
    const user = await request.json();
    return HttpResponse.json(
      { id: 3, ...user },
      { status: 201 }
    );
  }),

  // Error handling
  http.get(`${API_BASE}/users/:id`, ({ params }) => {
    if (params.id === '999') {
      return HttpResponse.json(
        { message: 'User not found' },
        { status: 404 }
      );
    }
    return HttpResponse.json({
      id: params.id,
      name: 'Test User',
    });
  }),
];

// mocks/server.js
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);

// Setup in test setup file
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Component Testing with API
```javascript
// __tests__/UsersList.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/config/queryClient';
import UsersList from '@/pages/UsersList';

describe('UsersList', () => {
  it('displays users after loading', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <UsersList />
      </QueryClientProvider>
    );

    // Check loading state
    expect(screen.getByText('Loading data...')).toBeInTheDocument();

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    expect(screen.getByText('Jane Smith')).toBeInTheDocument();
  });

  it('handles errors gracefully', async () => {
    // Override handler for this test
    server.use(
      http.get(`${API_BASE}/users`, () => {
        return HttpResponse.json(
          { message: 'Server error' },
          { status: 500 }
        );
      })
    );

    render(
      <QueryClientProvider client={queryClient}>
        <UsersList />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to load data/)).toBeInTheDocument();
    });
  });
});
```

---

## Best Practices Summary

1. **Always use a typed API client** (TypeScript recommended)
2. **Implement proper error handling** with user-friendly messages
3. **Use query caching** to reduce unnecessary requests
4. **Implement retry logic** for network failures
5. **Handle authentication** with token refresh
6. **Use loading/error states** in UI
7. **Test API integrations** with mocking
8. **Monitor API performance** with analytics
9. **Implement request deduplication** for identical concurrent requests
10. **Log errors** for debugging and monitoring

---

## Common FastAPI Backend Integration Examples

```javascript
// For your FastAPI backend

// FastAPI endpoint example:
// @router.get("/dashboard/metrics")
// async def get_dashboard_metrics():
//     return { data: {...}, success: true }

// Frontend call:
const metrics = await api.get('/dashboard/metrics');

// FastAPI with authentication:
// @router.post("/auth/login")
// async def login(credentials: LoginSchema):
//     token = create_access_token(user)
//     return { accessToken: token }

// Frontend setup:
const { accessToken } = await api.post('/auth/login', credentials);
api.setToken(accessToken);

// FastAPI file upload:
// @router.post("/import")
// async def import_data(file: UploadFile):
//     return { status: "success" }

// Frontend:
await dataService.uploadData(file);

// FastAPI with pagination:
// @router.get("/users?page={page}&limit={limit}")
// async def list_users(page: int = 1, limit: int = 20):
//     return { data: [...], total: count, page, limit }

// Frontend:
const users = await userService.getUsers(page, limit);
```

This guide covers everything you need for professional frontend-backend integration!
