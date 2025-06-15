import React from 'react'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '@/components/auth/AuthProvider'
import Dashboard from '@/components/dashboard/Dashboard'

// Mock the useAuth hook to return unauthenticated state
jest.mock('@/components/auth/AuthProvider', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useAuth: () => ({
    user: null,
    isAuthenticated: false,
    isLoading: false,
    login: jest.fn(),
    logout: jest.fn(),
    isAdmin: false,
  })
}))

describe('Dashboard', () => {
  it('should render welcome message when not authenticated', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </BrowserRouter>
    )

    expect(screen.getByText('Welcome to Sutra')).toBeInTheDocument()
    expect(screen.getByText('AI Operations Platform for systematic prompt engineering')).toBeInTheDocument()
  })
})
