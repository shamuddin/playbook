import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  FileText,
  Shield,
  CheckCircle,
  Download,
  Lock,
  Clock,
  Fingerprint,
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

interface EvidencePackage {
  package_id: string
  incident_id: string
  package_type: string
  integrity_hash: string
  is_verified: boolean
  generated_at: string | null
  retention_until: string | null
  artifacts: string[]
  manifest: Record<string, any>
  signature: Record<string, any>
}

interface VerifyResult {
  verified: boolean
  package_hash: string
  computed_hash: string
  signature_valid: boolean
  tamper_evident: boolean
}

export default function ForensicsPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [pkg, setPkg] = useState<EvidencePackage | null>(null)
  const [verify, setVerify] = useState<VerifyResult | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    loadForensics()
  }, [id])

  const loadForensics = async () => {
    setLoading(true)
    try {
      const [pkgRes, verifyRes] = await Promise.all([
        fetch(`${API_BASE}/forensics/${id}`),
        fetch(`${API_BASE}/forensics/${id}?format=verify`),
      ])
      const pkgData = await pkgRes.json()
      const verifyData = await verifyRes.json()
      setPkg(pkgData.data || null)
      setVerify(verifyData.data || null)
    } catch {
      // ignore
    }
    setLoading(false)
  }

  const handleExport = (format: 'zip' | 'html') => {
    if (!id) return
    window.open(`${API_BASE}/forensics/${id}/export?format=${format}`, '_blank')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  if (!pkg) {
    return (
      <div className="space-y-6">
        <button onClick={() => navigate('/incidents')} className="flex items-center gap-1 text-sm text-blue-600 hover:underline">
          <ArrowLeft className="w-4 h-4" /> Back to incidents
        </button>
        <div className="card p-8 text-center text-gray-500">No forensics package found</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button onClick={() => navigate(`/incidents/${id}`)} className="flex items-center gap-1 text-sm text-blue-600 hover:underline">
          <ArrowLeft className="w-4 h-4" /> Back to incident
        </button>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExport('zip')}
            className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
          >
            <Download className="w-4 h-4" /> Export ZIP
          </button>
          <button
            onClick={() => handleExport('html')}
            className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200"
          >
            <FileText className="w-4 h-4" /> Export HTML
          </button>
        </div>
      </div>

      {/* Package Header */}
      <div className="card p-6 border-l-4 border-blue-500">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Fingerprint className="w-5 h-5 text-blue-600" />
              <h1 className="text-xl font-bold text-gray-900">{pkg.package_id}</h1>
            </div>
            <p className="text-sm text-gray-600">Incident: <span className="font-mono">{pkg.incident_id}</span></p>
            <p className="text-sm text-gray-600">Type: {pkg.package_type}</p>
          </div>
          <div className="text-right">
            {pkg.is_verified ? (
              <span className="flex items-center gap-1 px-3 py-1 rounded-full bg-green-100 text-green-700 text-sm font-medium">
                <CheckCircle className="w-4 h-4" /> Verified
              </span>
            ) : (
              <span className="flex items-center gap-1 px-3 py-1 rounded-full bg-yellow-100 text-yellow-700 text-sm font-medium">
                <Shield className="w-4 h-4" /> Unverified
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Integrity & Verification */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Lock className="w-5 h-5 text-blue-600" />
            Integrity
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Hash (SHA-256)</span>
              <span className="font-mono text-xs text-gray-900 truncate max-w-[200px]">{pkg.integrity_hash}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Generated</span>
              <span className="text-gray-900">
                {pkg.generated_at ? new Date(pkg.generated_at).toLocaleString() : '—'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Retention</span>
              <span className="text-gray-900">
                {pkg.retention_until ? new Date(pkg.retention_until).toLocaleDateString() : '—'}
              </span>
            </div>
          </div>
        </div>

        <div className="card p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-green-600" />
            Verification Report
          </h2>
          {verify ? (
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Status</span>
                <span className={verify.verified ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                  {verify.verified ? 'Verified' : 'Failed'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Signature</span>
                <span className={verify.signature_valid ? 'text-green-600' : 'text-red-600'}>
                  {verify.signature_valid ? 'Valid' : 'Invalid'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Tamper Evident</span>
                <span className={verify.tamper_evident ? 'text-green-600' : 'text-yellow-600'}>
                  {verify.tamper_evident ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Verification pending</p>
          )}
        </div>
      </div>

      {/* Artifacts */}
      <div className="card p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" />
          Artifacts
        </h2>
        {pkg.artifacts && pkg.artifacts.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {pkg.artifacts.map((a, i) => (
              <div key={i} className="bg-gray-50 p-3 rounded-lg text-center">
                <FileText className="w-6 h-6 text-gray-400 mx-auto mb-1" />
                <span className="text-xs text-gray-700 font-medium">{a}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">No artifacts recorded</p>
        )}
      </div>

      {/* Manifest */}
      {pkg.manifest && Object.keys(pkg.manifest).length > 0 && (
        <div className="card p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-600" />
            Manifest
          </h2>
          <pre className="text-xs bg-gray-50 p-4 rounded-lg overflow-x-auto">
            {JSON.stringify(pkg.manifest, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
