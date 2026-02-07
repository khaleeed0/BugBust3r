import axios from 'axios'

// Get API URL from environment variable or use default
// IMPORTANT: Browser must use localhost:8000, not backend:8000
// The backend:8000 URL only works inside Docker network, not from browser
// In Docker: VITE_API_URL should be http://localhost:8000 (for browser access)
// Local dev: VITE_API_URL=http://localhost:8000 (or leave empty for default)
const getApiUrl = () => {
  // Check if we're in a browser (not SSR)
  if (typeof window !== 'undefined') {
    // Browser always needs to use localhost (or host IP), not Docker service names
    const envUrl = import.meta.env.VITE_API_URL
    
    // If env URL contains 'backend:', replace with localhost (for browser access)
    if (envUrl && envUrl.includes('backend:')) {
      return envUrl.replace('backend:', 'localhost:')
    }
    
    // Use environment variable if set and valid for browser
    if (envUrl && (envUrl.includes('localhost') || envUrl.includes('127.0.0.1'))) {
      return envUrl
    }
    
    // Default: use localhost:8000 (works for both Docker and local dev)
    return 'http://localhost:8000'
  }
  return import.meta.env.VITE_API_URL || 'http://localhost:8000'
}

const API_URL = getApiUrl()

// Log API URL for debugging (remove in production)
if (typeof window !== 'undefined' && import.meta.env.DEV) {
  console.log('API URL:', API_URL)
}

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
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


