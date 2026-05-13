import { useParams } from 'react-router-dom'

export default function IncidentDetailPage() {
  const { id } = useParams()

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Incident {id}</h1>
      <div className="card">
        <p className="text-gray-500">Incident detail will be implemented here.</p>
      </div>
    </div>
  )
}
