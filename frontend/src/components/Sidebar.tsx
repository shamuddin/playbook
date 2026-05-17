import { NavLink } from 'react-router-dom'
import {
  Shield,
  LayoutDashboard,
  AlertTriangle,
  Gavel,
  Activity,
  FileText,
  Settings,
  ClipboardList,
  Sliders,
  BarChart3,
  X,
  Gamepad2,
} from 'lucide-react'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/incidents', label: 'Incidents', icon: AlertTriangle },
  { path: '/judge', label: 'Judge Layer', icon: Gavel },
  { path: '/agents', label: 'Agent Health', icon: Activity },
  { path: '/swarm', label: 'Simulator', icon: Gamepad2, external: true },
  { path: '/compliance', label: 'Compliance', icon: FileText },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/policy-builder', label: 'Policy Builder', icon: Sliders },
  { path: '/review', label: 'Review Queue', icon: ClipboardList },
  { path: '/settings', label: 'Settings', icon: Settings },
]

interface SidebarProps {
  onClose?: () => void
}

export default function Sidebar({ onClose }: SidebarProps) {
  return (
    <aside className="w-64 h-full bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-lg font-bold text-gray-900">PLAYBOOK</h1>
            <p className="text-xs text-gray-500">AI Agent Security</p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="lg:hidden p-1 text-gray-500 hover:text-gray-700"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map((item) =>
          item.external ? (
            <a
              key={item.path}
              href={item.path}
              target="_blank"
              rel="noopener noreferrer"
              onClick={onClose}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors text-gray-600 hover:bg-gray-50 hover:text-gray-900"
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </a>
          ) : (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onClose}
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
          )
        )}
      </nav>
    </aside>
  )
}
