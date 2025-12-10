import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../services/api'
import { toast } from 'react-toastify'

export default function Reports() {
  const { id } = useParams()
  const [reports, setReports] = useState([])
  const [selectedReport, setSelectedReport] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) {
      fetchReport(id)
    } else {
      fetchReports()
    }
  }, [id])

  const fetchReports = async () => {
    try {
      const response = await api.get('/reports')
      setReports(response.data || [])
    } catch (error) {
      console.error('Error fetching reports:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch reports'
      
      const token = localStorage.getItem('token')
      if (token && token.startsWith('test-token-')) {
        toast.info('Backend API not available. Using test mode - no reports to display.')
      } else {
        toast.error(errorMessage)
      }
      
      setReports([])
    } finally {
      setLoading(false)
    }
  }

  const fetchReport = async (reportId) => {
    try {
      const response = await api.get(`/reports/${reportId}`)
      setSelectedReport(response.data)
    } catch (error) {
      console.error('Error fetching report:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch report'
      
      const token = localStorage.getItem('token')
      if (token && token.startsWith('test-token-')) {
        toast.info('Backend API not available. Using test mode.')
      } else {
        toast.error(errorMessage)
      }
      
      setSelectedReport(null)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString()
  }

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
      case 'success':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'running':
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'failed':
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-gray-900 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading reports...</p>
        </div>
      </div>
    )
  }

  // Show single report if ID is provided
  if (selectedReport) {
    return (
      <div className="min-h-screen bg-white">
        <div className="container mx-auto px-6 py-12 max-w-6xl">
          <div className="mb-6">
            <Link to="/reports" className="text-cyan-600 hover:text-cyan-700 transition-colors flex items-center">
              <span className="mr-2">←</span>
              Back to Reports
            </Link>
          </div>
          
          <div className="mb-8">
            <h1 className="text-4xl font-semibold text-gray-900 mb-3">Security Report</h1>
            <p className="text-lg text-gray-600">{selectedReport.target_url}</p>
          </div>
          
          <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
            <div className="grid grid-cols-2 gap-6 mb-6">
              <div>
                <p className="text-sm text-gray-500 mb-2">Status</p>
                <span className={`px-3 py-1 inline-flex text-sm font-medium rounded-full border ${getStatusColor(selectedReport.status)}`}>
                  {selectedReport.status}
                </span>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-2">Created At</p>
                <p className="text-base text-gray-900">{formatDate(selectedReport.created_at)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-2">Completed At</p>
                <p className="text-base text-gray-900">{formatDate(selectedReport.completed_at)}</p>
              </div>
            </div>

            {selectedReport.error_message && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">{selectedReport.error_message}</p>
              </div>
            )}
          </div>

          {/* All Findings Section */}
          {selectedReport.findings && selectedReport.findings.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">All Findings</h2>
              <p className="text-sm text-gray-600 mb-4">Total: {selectedReport.findings.length} findings discovered</p>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {selectedReport.findings.map((finding, index) => (
                  <div key={finding.id || index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="text-lg font-semibold text-gray-900 mb-1">
                          {finding.vulnerability_name || 'Security Finding'}
                        </h4>
                        <div className="flex items-center gap-3 text-sm text-gray-600 mb-2">
                          <span>Tool: {finding.tool_name || 'Unknown'}</span>
                          <span>•</span>
                          <span>Location: {finding.location || 'N/A'}</span>
                        </div>
                      </div>
                      <span className={`px-3 py-1 text-xs font-medium rounded-full border ${
                        finding.severity === 'critical' ? 'bg-red-100 text-red-800 border-red-200' :
                        finding.severity === 'high' ? 'bg-orange-100 text-orange-800 border-orange-200' :
                        finding.severity === 'medium' ? 'bg-yellow-100 text-yellow-800 border-yellow-200' :
                        finding.severity === 'low' ? 'bg-blue-100 text-blue-800 border-blue-200' :
                        'bg-gray-100 text-gray-800 border-gray-200'
                      }`}>
                        {finding.severity?.toUpperCase() || 'INFO'}
                      </span>
                    </div>
                    {finding.description && (
                      <p className="text-sm text-gray-700 mb-2">{finding.description}</p>
                    )}
                    {finding.evidence && (
                      <details className="mt-2">
                        <summary className="text-sm font-medium text-gray-700 cursor-pointer hover:text-gray-900">
                          View Evidence
                        </summary>
                        <pre className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded text-xs text-gray-700 font-mono overflow-auto">
                          {finding.evidence}
                        </pre>
                      </details>
                    )}
                    {finding.recommendation && (
                      <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded">
                        <p className="text-sm font-semibold text-blue-900 mb-1">Recommendation:</p>
                        <p className="text-sm text-blue-800">{finding.recommendation}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tool Execution Stages */}
          <div className="mb-6">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Scan Stages</h2>
            <div className="space-y-6">
              {selectedReport.stages?.map((stage, index) => (
                <div key={index} className="bg-white border border-gray-200 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {stage.stage} - {stage.tool_name}
                    </h3>
                    <div className="flex items-center space-x-4">
                      <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusColor(stage.status)}`}>
                        {stage.status}
                      </span>
                      {stage.execution_time && (
                        <span className="text-sm text-gray-600">
                          ⏱️ {stage.execution_time}s
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {stage.error && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
                      <p className="text-sm text-red-800">Error: {stage.error}</p>
                    </div>
                  )}
                  
                  {stage.input_data && (
                    <details className="mb-4 cursor-pointer">
                      <summary className="text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors">
                        View Input Data
                      </summary>
                      <pre className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded-lg overflow-auto text-xs text-gray-700 font-mono">
                        {JSON.stringify(stage.input_data, null, 2)}
                      </pre>
                    </details>
                  )}
                  
                  <details className="cursor-pointer">
                    <summary className="text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors">
                      View Tool Output
                    </summary>
                    <pre className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg overflow-auto text-xs text-gray-700 font-mono max-h-96">
                      {JSON.stringify(stage.output, null, 2)}
                    </pre>
                  </details>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Show reports list
  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-6 py-12 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-4xl font-semibold text-gray-900 mb-3">Security Reports</h1>
          <p className="text-lg text-gray-600">View detailed security scan reports</p>
        </div>

        {reports.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
            <div className="text-5xl mb-4">📊</div>
            <p className="text-gray-600 text-lg">No reports available</p>
            <p className="text-gray-500 mt-2">Complete a scan to see reports</p>
          </div>
        ) : (
          <div className="space-y-6">
            {reports.map((report) => (
              <div key={report.job_id} className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-gray-900 mb-4">
                      {report.target_url}
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Status</p>
                        <span className={`px-3 py-1 inline-flex text-xs font-medium rounded-full border ${getStatusColor(report.status)}`}>
                          {report.status}
                        </span>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Created</p>
                        <p className="font-medium text-gray-900">{formatDate(report.created_at)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Stages</p>
                        <p className="font-medium text-gray-900">
                          {report.completed_stages} / {report.total_stages}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Tools Used</p>
                        <p className="font-medium text-gray-900">{report.tools_used?.length || 0}</p>
                      </div>
                    </div>
                    {report.findings_summary && (
                      <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                        <h4 className="text-sm font-semibold mb-3 text-gray-900">Findings Summary</h4>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                          {report.findings_summary.subdomains_found > 0 && (
                            <div className="flex items-center">
                              <span className="mr-2">🔍</span>
                              <span className="text-gray-700">Subdomains: <span className="font-semibold text-gray-900">{report.findings_summary.subdomains_found}</span></span>
                            </div>
                          )}
                          {report.findings_summary.http_services > 0 && (
                            <div className="flex items-center">
                              <span className="mr-2">🌐</span>
                              <span className="text-gray-700">HTTP Services: <span className="font-semibold text-gray-900">{report.findings_summary.http_services}</span></span>
                            </div>
                          )}
                          {report.findings_summary.directories_found > 0 && (
                            <div className="flex items-center">
                              <span className="mr-2">🗂️</span>
                              <span className="text-gray-700">Directories: <span className="font-semibold text-gray-900">{report.findings_summary.directories_found}</span></span>
                            </div>
                          )}
                          {report.findings_summary.security_alerts > 0 && (
                            <div className="flex items-center">
                              <span className="mr-2">🛡️</span>
                              <span className="text-gray-700">Security Alerts: <span className="font-semibold text-red-600">{report.findings_summary.security_alerts}</span></span>
                            </div>
                          )}
                          {report.findings_summary.vulnerabilities > 0 && (
                            <div className="flex items-center">
                              <span className="mr-2">⚡</span>
                              <span className="text-gray-700">Vulnerabilities: <span className="font-semibold text-yellow-600">{report.findings_summary.vulnerabilities}</span></span>
                            </div>
                          )}
                          {report.findings_summary.sql_injections > 0 && (
                            <div className="flex items-center">
                              <span className="mr-2">💉</span>
                              <span className="text-gray-700">SQL Injections: <span className="font-semibold text-red-600">{report.findings_summary.sql_injections}</span></span>
                            </div>
                          )}
                          {report.findings_summary.semgrep_findings > 0 && (
                            <div className="flex items-center">
                              <span className="mr-2">🔍</span>
                              <span className="text-gray-700">Semgrep Findings: <span className="font-semibold text-orange-600">{report.findings_summary.semgrep_findings}</span></span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="ml-4">
                    <a
                      href={`/reports/${report.job_id}`}
                      className="px-6 py-3 bg-gray-900 text-white font-medium rounded-lg hover:bg-gray-800 transition-colors inline-block"
                    >
                      View Report →
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
