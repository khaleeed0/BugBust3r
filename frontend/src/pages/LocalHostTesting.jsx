import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import { api } from '../services/api'

export default function LocalHostTesting() {
  const navigate = useNavigate()
  const [targetUrl, setTargetUrl] = useState('http://localhost:3000')
  const [sourcePath, setSourcePath] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!targetUrl.trim()) {
      toast.error('Please enter a localhost URL')
      return
    }

    // Validate URL format
    const urlPattern = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?/
    if (!urlPattern.test(targetUrl.trim())) {
      toast.error('Only localhost or 127.0.0.1 URLs are allowed')
      return
    }

    // Check authentication
    const token = localStorage.getItem('token')
    if (!token) {
      toast.error('Please login to run scans')
      navigate('/login')
      return
    }

    // Check if using test token (from hardcoded test users)
    // Test tokens won't work with the backend API, so we need to prompt for real login
    if (token.startsWith('test-token-')) {
      toast.error('Test users cannot run scans. Please login with a registered account.')
      setTimeout(() => {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        navigate('/login')
      }, 2000)
      return
    }

    setLoading(true)
    setResult(null)
    try {
      // Use a longer timeout for AddressSanitizer scans (5 minutes)
      const response = await api.post('/scans/local-testing', {
        target_url: targetUrl.trim(),
        label: 'LocalHostTesting',
        source_path: sourcePath.trim() || null,
      }, {
        timeout: 300000 // 5 minutes for AddressSanitizer scans
      })
      setResult(response.data)
      toast.success('AddressSanitizer scan completed')
    } catch (error) {
      console.error('Scan error:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to run local scan'
      
      // Handle authentication errors
      if (error.response?.status === 401) {
        toast.error('Authentication failed. Please login again.')
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        setTimeout(() => navigate('/login'), 2000)
      } else if (error.response?.status === 400) {
        toast.error(errorMessage)
      } else {
        toast.error(`Scan failed: ${errorMessage}`)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-6 py-12 max-w-4xl">
        <div className="mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-sm text-cyan-600 hover:text-cyan-800 transition-colors mb-6 inline-flex items-center gap-2"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-4xl font-semibold text-gray-900 mb-4">LocalHostTesting</h1>
          <p className="text-lg text-gray-600">
            Run development-stage scans against a localhost service using AddressSanitizer - a runtime memory safety tool for finding buffer overflow, use-after-free, and other memory corruption vulnerabilities in C/C++ code. This flow is optimized for quick feedback without running the full production toolchain.
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-8 shadow-sm mb-10">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
            <h2 className="text-2xl font-semibold text-gray-900">Development Scan</h2>
            <span className="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-medium bg-amber-100 text-amber-800">
              AddressSanitizer · Memory Safety
            </span>
          </div>
          <p className="text-sm text-gray-600 mb-6">
            Only <span className="font-semibold">http://localhost</span> or <span className="font-semibold">http://127.0.0.1</span> addresses are accepted.
            Make sure the target service is accessible from the Docker network before launching the scan.
          </p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="localTarget" className="block text-sm font-medium text-gray-700 mb-2">
                Localhost URL
              </label>
              <input
                id="localTarget"
                type="text"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="http://localhost:3000"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-gray-900"
              />
            </div>
            <div>
              <label htmlFor="sourcePath" className="block text-sm font-medium text-gray-700 mb-2">
                Source Code Path (Optional)
                <span className="text-xs text-gray-500 ml-2">Absolute path to your project's source code directory</span>
              </label>
              <input
                id="sourcePath"
                type="text"
                value={sourcePath}
                onChange={(e) => setSourcePath(e.target.value)}
                placeholder="C:\Users\username\project\src or /home/user/project/src"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-gray-900"
              />
              <p className="mt-2 text-xs text-gray-500">
                💡 If left empty, AddressSanitizer will run a demo vulnerable C program. Provide the absolute path to your C/C++ source directory to scan your project.
              </p>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-3 bg-gray-900 text-white font-medium rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
                  Scanning... This may take 1-3 minutes for large codebases
                </span>
              ) : 'Run AddressSanitizer Scan'}
            </button>
          </form>
        </div>

        {result && (
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
              <div>
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Scan Summary</p>
                <h3 className="text-2xl font-semibold text-gray-900 mt-1">{result.target_url}</h3>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">Environment</p>
                <p className="font-semibold text-gray-900">{result.environment}</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="p-4 border border-gray-200 rounded-lg">
                <p className="text-sm text-gray-500">Status</p>
                <p className={`text-lg font-semibold capitalize ${
                  result.status === 'failed' ? 'text-red-600' : 
                  result.status === 'completed' ? 'text-green-600' : 
                  'text-gray-900'
                }`}>{result.status}</p>
              </div>
              <div className="p-4 border border-gray-200 rounded-lg">
                <p className="text-sm text-gray-500">Alerts</p>
                <p className="text-lg font-semibold text-gray-900">{result.alert_count}</p>
              </div>
              <div className="p-4 border border-gray-200 rounded-lg">
                <p className="text-sm text-gray-500">Job ID</p>
                <p className="text-sm font-mono text-gray-900 break-all">{result.job_id}</p>
              </div>
            </div>

            {result.error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm font-semibold text-red-800 mb-2">Scan Error:</p>
                <p className="text-sm text-red-700 whitespace-pre-wrap">{result.error}</p>
              </div>
            )}

            {result.alerts?.length > 0 ? (
              <div className="space-y-4">
                {result.alerts.map((alert, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 hover:border-cyan-300 transition-colors">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <h4 className="text-lg font-semibold text-gray-900">{alert.name || 'Security Issue'}</h4>
                        <span className="px-2 py-0.5 bg-cyan-100 text-cyan-800 rounded text-xs font-medium">
                          {alert.tool || 'AddressSanitizer'}
                        </span>
                      </div>
                      <span className={`text-sm font-medium px-2 py-1 rounded ${
                        alert.risk === 'CRITICAL' || alert.risk === 'ERROR' ? 'bg-red-100 text-red-800' :
                        alert.risk === 'HIGH' || alert.risk === 'WARNING' ? 'bg-orange-100 text-orange-800' :
                        alert.risk === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {alert.risk || 'Info'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{alert.description || 'No description provided.'}</p>
                    {alert.solution && (
                      <p className="text-sm text-gray-500">
                        <span className="font-semibold">Recommendation:</span> {alert.solution}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-10 border border-dashed border-gray-300 rounded-lg">
                <p className="text-gray-600 font-medium">No memory safety issues found by AddressSanitizer 🎉</p>
                <p className="text-sm text-gray-500 mt-2">The scan completed successfully with no buffer overflow, use-after-free, or other memory corruption issues detected.</p>
              </div>
            )}
            
            {result.alerts?.length > 0 && (
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm font-semibold text-blue-800 mb-2">Scan Summary:</p>
                <div className="flex flex-wrap gap-2">
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                    AddressSanitizer · {result.alerts.length} issue{result.alerts.length !== 1 ? 's' : ''} found
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

