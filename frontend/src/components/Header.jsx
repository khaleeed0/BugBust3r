import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200">
      <div className="container mx-auto px-6 py-4">
        <div className="flex justify-between items-center">
          <Link to="/dashboard" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 rounded-lg bg-cyan-500 flex items-center justify-center text-white text-xl font-semibold transition-transform group-hover:scale-105">
              🛡️
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                Bugbust3r
              </h1>
            </div>
          </Link>
          
          {user && (
            <nav className="flex items-center space-x-8">
              <Link 
                to="/dashboard" 
                className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
              >
                Dashboard
              </Link>
              <Link 
                to="/local-host-testing" 
                className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
              >
                Local Host Testing
              </Link>
              <Link 
                to="/scans" 
                className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
              >
                Scans
              </Link>
              <Link 
                to="/reports" 
                className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
              >
                Reports
              </Link>
              <Link 
                to="/profile" 
                className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
              >
                Profile
              </Link>
              <div className="flex items-center space-x-4 ml-4 pl-4 border-l border-gray-200">
                <Link 
                  to="/profile"
                  className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
                >
                  {user.username}
                </Link>
              </div>
            </nav>
          )}
        </div>
      </div>
    </header>
  )
}
