import { useState, useEffect } from 'react'
import { apiService } from '../services/api'
import { useAuth } from '../components/auth/AuthProvider'

export interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

export function useApi<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = []
): UseApiState<T> & { refetch: () => Promise<void> } {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: true,
    error: null
  })
  
  const { token } = useAuth()

  const fetchData = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }))
    
    try {
      // Set the auth token for API requests
      if (token) {
        apiService.setToken(token)
      }
      
      const result = await apiCall()
      setState({
        data: result,
        loading: false,
        error: null
      })
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error instanceof Error ? error.message : 'An error occurred'
      })
    }
  }

  useEffect(() => {
    if (token !== null) { // Only fetch when auth state is determined
      fetchData()
    }
  }, [token, ...dependencies])

  return {
    ...state,
    refetch: fetchData
  }
}

export function useAsyncAction<T = any>() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { token } = useAuth()

  const execute = async (action: () => Promise<T>): Promise<T | null> => {
    setLoading(true)
    setError(null)
    
    try {
      // Set the auth token for API requests
      if (token) {
        apiService.setToken(token)
      }
      
      const result = await action()
      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred'
      setError(errorMessage)
      throw error
    } finally {
      setLoading(false)
    }
  }

  return {
    loading,
    error,
    execute
  }
}
