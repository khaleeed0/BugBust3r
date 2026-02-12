import axios from 'axios'

// API base URL: use same-origin in dev so Vite proxy forwards /api to backend (no CORS, no direct 8000)
// In production or when not using Vite dev server, use explicit backend URL
const getApiUrl = () => {
  if (typeof window === 'undefined') {
    return import.meta.env.VITE_API_URL || 'http://localhost:8000'
  }
  // In Vite dev (npm run dev): use empty string so requests go to same origin and Vite proxies /api -> localhost:8000
  // This avoids "Cannot reach API" when the browser can't connect directly to port 8000
  if (import.meta.env.DEV) {
    return ''
  }
  const envUrl = import.meta.env.VITE_API_URL
  if (envUrl && (envUrl.includes('localhost') || envUrl.includes('127.0.0.1'))) {
    return envUrl
  }
  if (envUrl && envUrl.includes('backend:')) {
    return envUrl.replace('backend:', 'localhost:')
  }
  return envUrl || 'http://localhost:8000'
}

const API_URL = getApiUrl()

// Log API URL for debugging (remove in production)
if (typeof window !== 'undefined' && import.meta.env.DEV) {
  console.log('API URL:', API_URL)
}

// When API_URL is '' (dev + proxy), use /api/v1 so Vite proxies to backend
export const api = axios.create({
  baseURL: API_URL ? `${API_URL}/api/v1` : '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minute timeout for long-running requests (AddressSanitizer scans can take time)
})

// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Don't redirect if we're already on login/register page (let those pages handle the error)
      const currentPath = window.location.pathname
      if (currentPath !== '/login' && currentPath !== '/register') {
        // Unauthorized for authenticated requests - clear token and redirect to login
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
      // If on login/register page, just reject the promise so the page can handle it
    }
    return Promise.reject(error)
  }
)


