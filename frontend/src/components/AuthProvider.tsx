import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { getToken, setToken, removeToken, apiFetch, API_BASE } from '../utils/api'

interface User {
  id: string
  email: string
  full_name: string
  role: string
}

interface AuthContextValue {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setTokenState] = useState<string | null>(getToken())
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const stored = getToken()
    if (stored) {
      setTokenState(stored)
      fetchUser(stored)
    } else {
      setIsLoading(false)
    }
  }, [])

  const fetchUser = async (_token: string) => {
    try {
      const res = await apiFetch(`${API_BASE}/auth/me`)
      if (res.ok) {
        const data = await res.json()
        setUser(data.data)
      } else {
        removeToken()
        setTokenState(null)
      }
    } catch {
      removeToken()
      setTokenState(null)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }))
      throw new Error(err.detail || 'Login failed')
    }
    const data = await res.json()
    const accessToken = data.data.access_token
    setToken(accessToken)
    setTokenState(accessToken)
    setUser(data.data.user)
  }

  const logout = () => {
    removeToken()
    setTokenState(null)
    setUser(null)
    window.location.reload()
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
