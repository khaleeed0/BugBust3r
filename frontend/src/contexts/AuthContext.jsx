import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../services/api'

const AuthContext = createContext()

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('token')
    if (token) {
      // Verify token and get user info from database
      api.get('/auth/me')
        .then(response => {
          setUser(response.data)
          localStorage.setItem('user', JSON.stringify(response.data))
        })
        .catch(() => {
          // Invalid token, clear storage
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          setUser(null)
        })
        .finally(() => {
          setLoading(false)
        })
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (username, password) => {
    // Login endpoint expects form-urlencoded data, not JSON
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)

    const response = await api.post('/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    const { access_token } = response.data
    
    localStorage.setItem('token', access_token)
    
    // Get user info from database
    try {
      const userResponse = await api.get('/auth/me')
      const userData = userResponse.data
      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))
    } catch (error) {
      // If /me fails, clear token and throw error
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      console.error('Failed to get user info after login:', error)
      throw new Error('Login successful but could not retrieve user information. Please try again.')
    }
    
    return response.data
  }

  const register = async (email, username, password, fullName) => {
    const response = await api.post('/auth/register', {
      email,
      username,
      password,
      full_name: fullName
    })
    
    // Auto login after registration
    await login(username, password)
    
    return response.data
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  const refreshUser = async () => {
    try {
      const response = await api.get('/auth/me')
      setUser(response.data)
      localStorage.setItem('user', JSON.stringify(response.data))
    } catch (error) {
      console.error('Error refreshing user:', error)
      // If refresh fails, user might be logged out
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      setUser(null)
    }
  }

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    refreshUser
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}


