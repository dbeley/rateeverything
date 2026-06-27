"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"
import { api, setToken as setApiToken } from "@/lib/api"

interface User {
  id: number
  username: string
  display_name: string | null
  email: string | null
  avatar_url: string | null
  bio: string | null
  is_admin: boolean
}

interface AuthContext {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<void>
  register: (username: string, password: string, displayName?: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthCtx = createContext<AuthContext>({
  user: null,
  token: null,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  loading: true,
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Load token from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("re_token")
    if (saved) {
      setToken(saved)
      setToken(saved)
      api.getMe().then(setUser).catch(() => {
        localStorage.removeItem("re_token")
        setToken(null)
      }).finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (username: string, password: string) => {
    const res = await api.login(username, password)
    localStorage.setItem("re_token", res.access_token)
    setApiToken(res.access_token)
    setUser(res.user)
  }

  const register = async (username: string, password: string, displayName?: string) => {
    const res = await api.register(username, password, displayName)
    localStorage.setItem("re_token", res.access_token)
    setApiToken(res.access_token)
    setUser(res.user)
  }

  const logout = () => {
    localStorage.removeItem("re_token")
    setToken(null)
    setUser(null)
  }

  return (
    <AuthCtx.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthCtx.Provider>
  )
}

export const useAuth = () => useContext(AuthCtx)
