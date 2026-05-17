/**
 * Shared configuration helper that reads user preferences from localStorage.
 *
 * All pages should use these helpers instead of hardcoded constants so that
 * changes made on the Settings page actually take effect.
 */

const DEFAULT_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003/api/v1'
const DEFAULT_WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8003/api/v1/ws/incidents'

export function getApiBase(): string {
  try {
    const stored = window.localStorage.getItem('playbook_api_url')
    return stored ? JSON.parse(stored) : DEFAULT_API_URL
  } catch {
    return DEFAULT_API_URL
  }
}

export function getWsUrl(): string {
  try {
    const stored = window.localStorage.getItem('playbook_ws_url')
    return stored ? JSON.parse(stored) : DEFAULT_WS_URL
  } catch {
    return DEFAULT_WS_URL
  }
}

export function getPageSize(): number {
  try {
    const stored = window.localStorage.getItem('playbook_page_size')
    return stored ? JSON.parse(stored) : 25
  } catch {
    return 25
  }
}

export function getRefreshInterval(): number {
  try {
    const stored = window.localStorage.getItem('playbook_refresh_interval')
    return stored ? JSON.parse(stored) : 30
  } catch {
    return 30
  }
}

export function getSoundAlerts(): boolean {
  try {
    const stored = window.localStorage.getItem('playbook_sound_alerts')
    return stored ? JSON.parse(stored) : false
  } catch {
    return false
  }
}
