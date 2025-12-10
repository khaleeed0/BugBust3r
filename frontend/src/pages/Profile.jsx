import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { toast } from 'react-toastify'

export default function Profile() {
  const { user: authUser, logout, refreshUser } = useAuth()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [user, setUser] = useState(null)
  const [editMode, setEditMode] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: ''
  })

  useEffect(() => {
    fetchUserInfo()
  }, [])

  const fetchUserInfo = async () => {
    try {
      const token = localStorage.getItem('token')
      if (token && token.startsWith('test-token-')) {
        // For test user, use stored user data
        const storedUser = localStorage.getItem('user')
        if (storedUser) {
          const testUser = JSON.parse(storedUser)
          setUser(testUser)
          setFormData({
            email: testUser.email || '',
            username: testUser.username || '',
            password: '',
            confirmPassword: ''
          })
        }
      } else {
        const response = await api.get('/auth/me')
        setUser(response.data)
        setFormData({
          email: response.data.email || '',
          username: response.data.username || '',
          password: '',
          confirmPassword: ''
        })
      }
    } catch (error) {
      console.error('Error fetching user info:', error)
      toast.error('Failed to load user information')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Validate password if provided
    if (formData.password && formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match')
      return
    }

    if (formData.password && formData.password.length < 6) {
      toast.error('Password must be at least 6 characters')
      return
    }

    setSaving(true)
    try {
      const token = localStorage.getItem('token')
      if (token && token.startsWith('test-token-')) {
        // For test user, just update local storage
        const updatedUser = {
          ...user,
          email: formData.email,
          username: formData.username
        }
        localStorage.setItem('user', JSON.stringify(updatedUser))
        setUser(updatedUser)
        toast.success('Profile updated successfully! (Test Mode)')
      } else {
        const updateData = {
          email: formData.email,
          username: formData.username
        }
        if (formData.password) {
          updateData.password = formData.password
        }
        
        const response = await api.put('/auth/me', updateData)
        setUser(response.data)
        await refreshUser() // Update global user state
        toast.success('Profile updated successfully!')
      }
      
      setEditMode(false)
      setFormData(prev => ({
        ...prev,
        password: '',
        confirmPassword: ''
      }))
    } catch (error) {
      console.error('Error updating profile:', error)
      toast.error(error.response?.data?.detail || 'Failed to update profile')
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
    toast.success('Logged out successfully')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-gray-900 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading profile...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-6 py-12 max-w-4xl">
        <div className="mb-8">
          <h1 className="text-4xl font-semibold text-gray-900 mb-3">Profile Settings</h1>
          <p className="text-lg text-gray-600">Manage your account information and preferences</p>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-8 shadow-sm">
          {!editMode ? (
            <>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-semibold text-gray-900">Account Information</h2>
                <button
                  onClick={() => setEditMode(true)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  Edit Profile
                </button>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-2">User ID</label>
                  <p className="text-base text-gray-900">{user?.id}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-2">Email</label>
                  <p className="text-base text-gray-900">{user?.email || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-2">Username</label>
                  <p className="text-base text-gray-900">{user?.username || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-2">Role</label>
                  <p className="text-base text-gray-900 capitalize">{user?.role || 'user'}</p>
                </div>
              </div>
            </>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-semibold text-gray-900">Edit Profile</h2>
                <button
                  type="button"
                  onClick={() => {
                    setEditMode(false)
                    fetchUserInfo() // Reset form
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-gray-900"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                    Username
                  </label>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    value={formData.username}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-gray-900"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                    New Password (leave blank to keep current)
                  </label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-gray-900"
                    placeholder="Enter new password"
                  />
                </div>

                {formData.password && (
                  <div>
                    <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                      Confirm New Password
                    </label>
                    <input
                      id="confirmPassword"
                      name="confirmPassword"
                      type="password"
                      value={formData.confirmPassword}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-gray-900"
                      placeholder="Confirm new password"
                    />
                  </div>
                )}

                <div className="pt-4 border-t border-gray-200">
                  <button
                    type="submit"
                    disabled={saving}
                    className="w-full px-6 py-3 bg-gray-900 text-white font-medium rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>

        {/* Logout Section */}
        <div className="mt-8 bg-white border border-gray-200 rounded-xl p-8 shadow-sm">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">Account Actions</h2>
          <div className="space-y-4">
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <h3 className="text-sm font-semibold text-red-900 mb-2">Danger Zone</h3>
              <p className="text-sm text-red-700 mb-4">
                Once you log out, you'll need to sign in again to access your account.
              </p>
              <button
                onClick={handleLogout}
                className="px-6 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

