import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi, UserResponse } from '../lib/api'

const TOKEN_KEY = 'auth_token'
const USER_KEY = 'auth_user'

interface AuthContextType {
  user: UserResponse | null
  token: string | null
  isLoading: boolean
  login: (username: string, password: string) => Promise<{ must_change_password?: boolean } | null>
  logout: () => void
  isAuthenticated: boolean
  isAdmin: boolean
  mustChangePassword: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(() => {
    const stored = localStorage.getItem(USER_KEY)
    return stored ? JSON.parse(stored) : null
  })
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem(TOKEN_KEY)
  })
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (token && !user) {
      authApi.getMe()
        .then(setUser)
        .catch(() => {
          localStorage.removeItem(TOKEN_KEY)
          localStorage.removeItem(USER_KEY)
          setToken(null)
          setUser(null)
        })
    }
  }, [token, user])

  const login = async (username: string, password: string) => {
    setIsLoading(true)
    try {
      const response = await authApi.login({ username, password })
      localStorage.setItem(TOKEN_KEY, response.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(response.user))
      setToken(response.access_token)
      setUser(response.user)
      return { must_change_password: response.user.must_change_password ?? false }
    } catch (err) {
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setToken(null)
    setUser(null)
  }

  const mustChangePassword = user?.must_change_password ?? false

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        logout,
        isAuthenticated: !!token && !!user,
        isAdmin: user?.role === 'admin',
        mustChangePassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
