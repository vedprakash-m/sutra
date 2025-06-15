// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:7075/api'

export interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
  timestamp?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  pagination: {
    current_page: number
    total_pages: number
    total_count: number
    limit: number
    has_next: boolean
    has_prev: boolean
  }
}

class ApiService {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  setToken(token: string | null) {
    this.token = token
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    return headers
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`
      
      try {
        const errorData = await response.json()
        errorMessage = errorData.message || errorData.error || errorMessage
      } catch (e) {
        // If JSON parsing fails, use the default error message
      }
      
      throw new Error(errorMessage)
    }

    return response.json()
  }

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = new URL(`${this.baseUrl}${endpoint}`)
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value))
        }
      })
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
    })

    return this.handleResponse<T>(response)
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    })

    return this.handleResponse<T>(response)
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    })

    return this.handleResponse<T>(response)
  }

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    })

    return this.handleResponse<T>(response)
  }
}

// Create singleton instance
export const apiService = new ApiService()

// Collection related types and functions
export interface Collection {
  id: string
  name: string
  description: string
  type: 'private' | 'shared_team' | 'public_marketplace'
  owner_id: string
  created_at: string
  updated_at: string
  prompt_count?: number
  tags?: string[]
}

export interface Prompt {
  id: string
  title: string
  content: string
  collection_id: string
  created_at: string
  updated_at: string
  version: number
  tags?: string[]
}

export interface Playbook {
  id: string
  name: string
  description: string
  steps: PlaybookStep[]
  creator_id: string
  created_at: string
  updated_at: string
  visibility: 'private' | 'shared'
}

export interface PlaybookStep {
  id: string
  type: 'prompt' | 'review' | 'variable'
  prompt_id?: string
  content?: string
  variables?: Record<string, any>
  order: number
}

export interface LLMIntegration {
  id: string
  provider: string
  name: string
  api_key: string
  enabled: boolean
  configuration: Record<string, any>
}

// API Functions
export const collectionsApi = {
  list: (params?: { page?: number; limit?: number; search?: string; type?: string }) =>
    apiService.get<PaginatedResponse<Collection>>('/collections', params),
  
  get: (id: string) =>
    apiService.get<Collection>(`/collections/${id}`),
  
  create: (collection: Partial<Collection>) =>
    apiService.post<Collection>('/collections', collection),
  
  update: (id: string, collection: Partial<Collection>) =>
    apiService.put<Collection>(`/collections/${id}`, collection),
  
  delete: (id: string) =>
    apiService.delete(`/collections/${id}`)
}

export const playbooksApi = {
  list: (params?: { page?: number; limit?: number; search?: string; visibility?: string }) =>
    apiService.get<PaginatedResponse<Playbook>>('/playbooks', params),
  
  get: (id: string) =>
    apiService.get<Playbook>(`/playbooks/${id}`),
  
  create: (playbook: Partial<Playbook>) =>
    apiService.post<Playbook>('/playbooks', playbook),
  
  update: (id: string, playbook: Partial<Playbook>) =>
    apiService.put<Playbook>(`/playbooks/${id}`, playbook),
  
  delete: (id: string) =>
    apiService.delete(`/playbooks/${id}`),
  
  execute: (id: string, variables?: Record<string, any>) =>
    apiService.post(`/playbooks/${id}/execute`, { variables })
}

export const integrationsApi = {
  listLLM: () =>
    apiService.get<{ integrations: Record<string, LLMIntegration>; supportedProviders: any[] }>('/integrations/llm'),
  
  saveLLM: (provider: string, integration: Partial<LLMIntegration>) =>
    apiService.post(`/integrations/llm/${provider}`, integration),
  
  deleteLLM: (provider: string) =>
    apiService.delete(`/integrations/llm/${provider}`)
}

export const adminApi = {
  getLLMSettings: () =>
    apiService.get('/management/llm/settings'),
  
  updateLLMSettings: (settings: any) =>
    apiService.put('/management/llm/settings', settings),
  
  getSystemHealth: () =>
    apiService.get('/management/system/health'),
  
  getUsageStats: () =>
    apiService.get('/management/usage')
}

export const llmApi = {
  execute: (promptText: string, model: string, variables?: Record<string, any>) =>
    apiService.post('/llm', { promptText, model, variables })
}

export default apiService
