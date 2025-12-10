import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { toast } from 'react-toastify'

export default function Dashboard() {
  const [targetUrl, setTargetUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const createOrGetTarget = async (url) => {
    // Normalize URL (remove trailing slash)
    const normalizedUrl = url.trim().replace(/\/$/, '')
    
    // Try to create a new target for this URL
    try {
      const response = await api.post('/targets', {
        url: normalizedUrl,
        name: normalizedUrl,
        asset_value: 'high'
      })
      return response.data
    } catch (error) {
      // If target already exists, fetch existing targets and find it
      const detail = error.response?.data?.detail
      if (error.response?.status === 400 && (detail?.includes('already exists') || detail?.includes('Target URL'))) {
        try {
          const listResponse = await api.get('/targets')
          const existing = listResponse.data.find((t) => {
            const targetUrl = t.url.trim().replace(/\/$/, '')
            return targetUrl === normalizedUrl
          })
          if (existing) {
            return existing
          }
        } catch (fetchError) {
          console.error('Failed to fetch existing targets:', fetchError)
        }
        // If we can't find it in user's targets, the backend should return it
        // But if not, show a helpful error
        throw new Error(`Target URL "${normalizedUrl}" already exists. Please use a different URL or select it from your targets.`)
      }
      throw error
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!targetUrl.trim()) {
      toast.error('Please enter a target URL')
      return
    }

    setLoading(true)
    try {
      const url = targetUrl.trim()

      // 1) Create (or reuse) a Target in the backend
      const target = await createOrGetTarget(url)

      // 2) Create a Scan for that target
      await api.post('/scans', {
        target_id: target.id
      })

      toast.success('Scan job created successfully!')
      setTargetUrl('')
      navigate('/scans')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create scan job')
    } finally {
      setLoading(false)
    }
  }

  const securityTools = [
    {
      name: 'Sublist3r',
      icon: '🔍',
      stage: 'Stage 1',
      description: 'Subdomain Enumeration',
      output: 'Discovered subdomains'
    },
    {
      name: 'Httpx',
      icon: '🌐',
      stage: 'Stage 2',
      description: 'HTTP Service Detection',
      output: 'Active web services'
    },
    {
      name: 'Gobuster',
      icon: '🗂️',
      stage: 'Stage 3',
      description: 'Directory Discovery',
      output: 'Hidden directories & files'
    },
    {
      name: 'OWASP ZAP',
      icon: '🛡️',
      stage: 'Stage 4',
      description: 'Web Application Scanning',
      output: 'Security alerts & vulnerabilities'
    },
    {
      name: 'Nuclei',
      icon: '⚡',
      stage: 'Stage 5',
      description: 'Template-Based Scanning',
      output: 'Template-based findings'
    },
    {
      name: 'SQLMap',
      icon: '💉',
      stage: 'Stage 6',
      description: 'SQL Injection Testing',
      output: 'SQL injection vulnerabilities'
    }
  ]

  const handlePhase1Click = () => {
    navigate('/local-host-testing')
  }

  const handlePhase2Submit = async (e) => {
    if (e) e.preventDefault()
    if (!targetUrl.trim()) {
      toast.error('Please enter a target URL')
      return
    }
    const event = e || { preventDefault: () => {} }
    await handleSubmit(event)
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-6 py-12 max-w-6xl">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1 className="text-4xl font-semibold text-gray-900 mb-3">
            Security Scanner
          </h1>
          <p className="text-lg text-gray-600">
            Automated vulnerability detection and security assessment
          </p>
        </div>

        {/* Phase Selection - Two Main Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {/* Phase 1: Static Code Analysis */}
          <div className="bg-gradient-to-br from-blue-50 to-cyan-50 border-2 border-blue-200 rounded-xl p-8 shadow-lg hover:shadow-xl transition-shadow">
            <div className="text-center">
              <div className="text-5xl mb-4">🔍</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">
                Phase 1: Static Code Analysis
              </h2>
              <p className="text-gray-700 mb-6">
                Analyze source code for buffer overflow vulnerabilities, security issues, and code quality problems using Semgrep.
              </p>
              <button
                onClick={handlePhase1Click}
                className="w-full px-8 py-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-transform"
              >
                Start Static Analysis
              </button>
              <p className="text-xs text-gray-600 mt-4">
                Uses: Semgrep • Localhost targets only
              </p>
            </div>
          </div>

          {/* Phase 2: Dynamic Analysis Web Penetration Scanner */}
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-200 rounded-xl p-8 shadow-lg hover:shadow-xl transition-shadow">
            <div className="text-center">
              <div className="text-5xl mb-4">🌐</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">
                Phase 2: Dynamic Analysis Web Penetration Scanner
              </h2>
              <p className="text-gray-700 mb-6">
                Comprehensive web application security testing with multi-stage scanning including subdomain enumeration, directory discovery, and vulnerability detection.
              </p>
              <div className="space-y-3">
                <input
                  type="text"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  placeholder="https://example.com"
                  className="w-full px-4 py-3 border border-purple-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-gray-900"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handlePhase2Submit(e)
                    }
                  }}
                />
                <button
                  onClick={handlePhase2Submit}
                  disabled={loading || !targetUrl.trim()}
                  className="w-full px-8 py-4 bg-purple-600 text-white font-semibold rounded-lg hover:bg-purple-700 transition-colors shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-transform disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                >
                  {loading ? 'Starting Scan...' : 'Start Dynamic Analysis'}
                </button>
              </div>
              <p className="text-xs text-gray-600 mt-4">
                Uses: Sublist3r, Httpx, Gobuster, ZAP, Nuclei, SQLMap
              </p>
            </div>
          </div>
        </div>

        {/* Security Tools */}
        <div>
          <h2 className="text-2xl font-semibold text-gray-900 mb-8">Security Tools</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {securityTools.map((tool, index) => (
              <div
                key={index}
                className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="text-3xl">{tool.icon}</div>
                  <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    {tool.stage}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {tool.name}
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  {tool.description}
                </p>
                <p className="text-xs text-gray-500">
                  Output: {tool.output}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
