// Mock for src/services/api.ts
/* eslint-disable @typescript-eslint/no-unused-vars */

export interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
  timestamp?: string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
  hasNext: boolean
}

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

// Mock implementation
export const apiService = {
  async get<T>(endpoint: string): Promise<T> {
    return {
      data: [],
      total: 0,
      page: 1,
      limit: 10,
      hasNext: false
    } as T
  },

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return {} as T
  },

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return {} as T
  },

  async delete<T>(endpoint: string): Promise<T> {
    return {} as T
  }
}

export const collectionsApi = {
  list: (params?: any) => Promise.resolve({ data: [], total: 0, page: 1, limit: 10, hasNext: false }),
  get: (id: string) => Promise.resolve({} as Collection),
  create: (collection: any) => Promise.resolve({} as Collection),
  update: (id: string, collection: any) => Promise.resolve({} as Collection),
  delete: (id: string) => Promise.resolve()
}

export const playbooksApi = {
  list: (params?: any) => Promise.resolve({ data: [], total: 0, page: 1, limit: 10, hasNext: false }),
  get: (id: string) => Promise.resolve({} as Playbook),
  create: (playbook: any) => Promise.resolve({} as Playbook),
  update: (id: string, playbook: any) => Promise.resolve({} as Playbook),
  delete: (id: string) => Promise.resolve()
}

export const integrationsApi = {
  list: () => Promise.resolve({ data: [], total: 0, page: 1, limit: 10, hasNext: false }),
  get: (id: string) => Promise.resolve({} as LLMIntegration),
  create: (integration: any) => Promise.resolve({} as LLMIntegration),
  update: (id: string, integration: any) => Promise.resolve({} as LLMIntegration),
  delete: (id: string) => Promise.resolve()
}

export const adminApi = {
  getStats: () => Promise.resolve({}),
  getUsers: () => Promise.resolve({ data: [], total: 0, page: 1, limit: 10, hasNext: false })
}

export const llmApi = {
  execute: (data: any) => Promise.resolve({})
}

export default apiService
