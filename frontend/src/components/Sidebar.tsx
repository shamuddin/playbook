import { NavLink } from 'react-router-dom'
import {
  Shield,
  AlertTriangle,
  Gavel,
  Activity,
  FileText,
  Settings,
  ClipboardList,
  Sliders,
} from 'lucide-react'

const navItems = [
  { path: '/incidents', label: 'Incidents', icon: AlertTriangle },
  { path: '/judge', label: 'Judge Layer', icon: Gavel },
  { path: '/agents', label: 'Agent Health', icon: Activity },
  { path: '/compliance', label: 'Compliance', icon: FileText },
  { path: '/policy-builder', label: 'Policy Builder', icon: Sliders },
  { path: '/review', label: 'Review Queue', icon: ClipboardList },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export default function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <Shield className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-lg font-bold text-gray-900">PLAYBOOK</h1>
            <p className="text-xs text-gray-500">AI Agent Security</p>
          </div>
        </div>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
