import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import { api } from '../services/api'

export default function LocalHostTesting() {
  const navigate = useNavigate()
  const [targetUrl, setTargetUrl] = useState('http://localhost:3001')
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

    // Don't scan this BugBust3r app — scan your target project instead (e.g. port 3001)
    const currentOrigin = typeof window !== 'undefined' ? window.location.origin : ''
    const targetOrigin = (() => {
      try {
        const u = new URL(targetUrl.trim())
        return u.origin
      } catch {
        return ''
      }
    })()
    if (currentOrigin && targetOrigin && currentOrigin === targetOrigin) {
      toast.error('Do not scan this BugBust3r app. Enter your target project URL instead (e.g. http://localhost:3001).')
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
      // Use a longer timeout for AddressSanitizer + Ghauri scans (5 minutes)
      const response = await api.post('/scans/local-testing', {
        target_url: targetUrl.trim(),
        label: 'LocalHostTesting',
        source_path: sourcePath.trim() || null,
      }, {
        timeout: 300000 // 5 minutes for AddressSanitizer + Ghauri
      })
      setResult(response.data)
      if (response.data.status === 'failed' && response.data.error) {
        toast.error(response.data.error)
      } else {
        toast.success('Scan completed')
      }
    } catch (error) {
      console.error('Scan error:', error)
      const isNetworkError = !error.response && (error.message === 'Network Error' || error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED')
      const detail = error.response?.data?.detail
      const errMsg = Array.isArray(detail) ? detail.map((d) => d.msg || d).join(', ') : (detail || error.response?.data?.error)
      const errorMessage = isNetworkError
        ? 'Backend not reachable. Start it first: run start-backend.bat (or start-project.bat) so the API runs on port 8000, then try again.'
        : (errMsg || error.message || 'Failed to run local scan')
      
      if (error.response?.status === 401) {
        toast.error('Authentication failed. Please login again.')
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        setTimeout(() => navigate('/login'), 2000)
      } else if (error.response?.status === 400) {
        toast.error(errorMessage)
      } else {
        toast.error(errorMessage)
        setResult({
          target_url: targetUrl.trim(),
          status: 'failed',
          environment: 'development',
          alert_count: 0,
          alerts: [],
          error: errorMessage,
          network_error: isNetworkError,
        })
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
            Run development-stage scans against a localhost service using <strong>AddressSanitizer</strong> (C/C++ memory safety) and <strong>Ghauri</strong> (SQL injection detection and exploitation, including blind SQLi and PostgreSQL). Optimized for quick feedback without the full production toolchain.
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-8 shadow-sm mb-10">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
            <h2 className="text-2xl font-semibold text-gray-900">Development Scan</h2>
            <span className="inline-flex items-center gap-2 flex-wrap">
              <span className="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-medium bg-amber-100 text-amber-800">
                AddressSanitizer · Memory Safety
              </span>
              <span className="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-medium bg-violet-100 text-violet-800">
                Ghauri · SQL Injection
              </span>
            </span>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Only <span className="font-semibold">http://localhost</span> or <span className="font-semibold">http://127.0.0.1</span> addresses are accepted.
            Enter your <strong>target project</strong> URL (e.g. <code className="bg-gray-100 px-1 rounded">http://localhost:3001</code>). Do not use this app&apos;s URL (port 3000).
          </p>
          <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-3 mb-6">
            <strong>Tip:</strong> Memory safety (AddressSanitizer) runs only when you provide a <strong>C/C++ source path</strong>—the tool discovers real issues in your code. SQL injection (Ghauri + SQLMap) runs on the <em>exact URL</em> you enter. Use a URL with a query parameter for SQLi (e.g. <code className="bg-amber-100 px-1 rounded">http://localhost:3001/product?id=1</code>). Run the scan with different URLs to cover more pages.
          </p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="localTarget" className="block text-sm font-medium text-gray-700 mb-2">
                Target URL (e.g. your app or lala store)
              </label>
              <input
                id="localTarget"
                type="text"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="http://localhost:3001"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-gray-900"
              />
            </div>
            <div>
              <label htmlFor="sourcePath" className="block text-sm font-medium text-gray-700 mb-2">
                C/C++ source path <span className="text-gray-500 font-normal">(optional — for buffer overflow / memory checks)</span>
              </label>
              <input
                id="sourcePath"
                type="text"
                value={sourcePath}
                onChange={(e) => setSourcePath(e.target.value)}
                placeholder="e.g. /path/to/your/cpp-project or leave empty to skip memory scan"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-gray-900"
              />
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
              ) : 'Run Localhost Scan'}
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
                {result.network_error && (
                  <p className="text-sm text-red-700 mt-3">
                    <strong>Fix:</strong> Run <code className="bg-red-100 px-1 rounded">start-backend.bat</code> in the BugBust3r folder (starts API on port 8000). Then refresh and run the scan again.{' '}
                    <a href="http://127.0.0.1:8000/health" target="_blank" rel="noopener noreferrer" className="underline font-medium text-red-800 hover:text-red-900">
                      Check if API is up →
                    </a>
                  </p>
                )}
              </div>
            )}

            {result.alerts?.length > 0 ? (
              <div className="space-y-6">
                <p className="text-sm text-gray-600">
                  This report is written for you. Each finding explains what was found, where it is, how to fix it, and how serious it is.
                </p>
                {result.alerts.map((alert, index) => (
                  <div key={index} className="border border-gray-200 rounded-xl p-5 bg-white shadow-sm hover:border-cyan-300 transition-colors">
                    <div className="flex items-center justify-between flex-wrap gap-2 mb-4">
                      <h4 className="text-xl font-semibold text-gray-900">{alert.name || 'Security issue'}</h4>
                      <span className={`text-sm font-medium px-3 py-1.5 rounded-full ${
                        alert.risk === 'CRITICAL' || alert.risk === 'ERROR' ? 'bg-red-100 text-red-800' :
                        alert.risk === 'HIGH' || alert.risk === 'WARNING' ? 'bg-orange-100 text-orange-800' :
                        alert.risk === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        Severity: {alert.risk || 'Info'}
                      </span>
                    </div>
                    {alert.severity_explanation && (
                      <p className="text-sm text-gray-600 mb-3 italic">{alert.severity_explanation}</p>
                    )}
                    <div className="space-y-3 text-sm">
                      <div>
                        <p className="font-semibold text-gray-700 mb-1">What we found</p>
                        <p className="text-gray-600">{alert.description || 'No description provided.'}</p>
                      </div>
                      {alert.location && (
                        <div>
                          <p className="font-semibold text-gray-700 mb-1">Where</p>
                          <p className="text-gray-600 font-mono text-xs bg-gray-50 px-2 py-1 rounded">{alert.location}</p>
                        </div>
                      )}
                      {alert.solution && (
                        <div>
                          <p className="font-semibold text-gray-700 mb-1">How to fix it</p>
                          <p className="text-gray-600">{alert.solution}</p>
                        </div>
                      )}
                    </div>
                    <p className="mt-3 text-xs text-gray-500">
                      Detected by: {alert.tool === 'ghauri' ? 'SQL injection (Ghauri)' : alert.tool === 'sqlmap' ? 'SQL injection with crawl (SQLMap)' : 'Memory safety (AddressSanitizer)'}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-10 border border-dashed border-gray-300 rounded-lg">
                <p className="text-gray-600 font-medium">No issues found by this scan</p>
                <p className="text-sm text-gray-500 mt-2">We checked for memory safety (buffer overflows) and SQL injection on the URL you entered. To look for more bugs, try a URL that includes a query parameter (e.g. <code className="bg-gray-100 px-1 rounded">?id=1</code>) for SQL injection, or run the scan on other pages.</p>
              </div>
            )}
            
            {(result.alerts?.length > 0 || result.results) && (
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm font-semibold text-blue-800 mb-2">Scan summary</p>
                <p className="text-sm text-blue-700 mb-2">
                  We found <strong>{result.alerts?.length ?? 0}</strong> finding{(result.alerts?.length ?? 0) !== 1 ? 's' : ''} on the URL you scanned. The report above explains each one in plain language. To look for more issues (including SQL injection), run the scan again with other URLs or add <code className="bg-blue-100 px-1 rounded">?id=1</code> to your URL.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                    {result.alerts?.length ?? 0} finding{(result.alerts?.length ?? 0) !== 1 ? 's' : ''}
                  </span>
                  {result.results?.addresssanitizer && (
                    <span className="px-3 py-1 bg-cyan-100 text-cyan-800 rounded-full text-xs font-medium" title={result.results.addresssanitizer.message || result.results.addresssanitizer.error || ''}>
                      ASan: {result.results.addresssanitizer.status === 'skipped' ? 'skipped (no source path)' : result.results.addresssanitizer.status === 'completed_with_issues' ? `${result.results.addresssanitizer.error_count ?? 0} issue(s)` : result.results.addresssanitizer.status === 'failed' && result.results.addresssanitizer.error ? `failed` : result.results.addresssanitizer.status}
                    </span>
                  )}
                  {result.results?.ghauri && (
                    <span className="px-3 py-1 bg-violet-100 text-violet-800 rounded-full text-xs font-medium" title={result.results.ghauri.error || ''}>
                      Ghauri: {result.results.ghauri.vulnerable ? 'SQLi' : result.results.ghauri.status}
                    </span>
                  )}
                  {result.results?.sqlmap && (
                    <span className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-medium" title={result.results.sqlmap.error || ''}>
                      SQLMap (crawl): {result.results.sqlmap.vulnerable ? 'SQLi' : result.results.sqlmap.status}
                    </span>
                  )}
                  {result.error && (
                    <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">
                      Error: {result.error}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

