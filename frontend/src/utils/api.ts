import { getApiBase } from './config'

export const API_BASE = getApiBase()

export function getToken(): string | null {
  return localStorage.getItem('playbook_token')
}

export function setToken(token: string) {
  localStorage.setItem('playbook_token', token)
}

export function removeToken() {
  localStorage.removeItem('playbook_token')
}

export function apiFetch(url: string, options: RequestInit = {}) {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return fetch(url, { ...options, headers })
}
