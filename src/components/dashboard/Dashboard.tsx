import { Link } from 'react-router-dom'
import { useAuth } from '@/components/auth/AuthProvider'
import { useApi } from '@/hooks/useApi'
import { collectionsApi, playbooksApi } from '@/services/api'

export default function Dashboard() {
  const { user, isAdmin } = useAuth()

  // Fetch dashboard data
  const { data: collectionsData, loading: collectionsLoading } = useApi(
    () => collectionsApi.list({ limit: 5 }),
    []
  )

  const { data: playbooksData, loading: playbooksLoading } = useApi(
    () => playbooksApi.list({ limit: 5 }),
    []
  )

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.name}
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          Here's what you can do with Sutra today
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <Link
          to="/prompts/new"
          className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
        >
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-indigo-500 rounded-md flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Create Prompt
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    New AI prompt
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </Link>

        <Link
          to="/collections"
          className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
        >
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Collections
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {collectionsLoading ? 'Loading...' : collectionsData?.pagination?.total_count || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </Link>

        <Link
          to="/playbooks/new"
          className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
        >
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Create Playbook
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    New workflow
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </Link>

        <Link
          to="/integrations"
          className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
        >
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-orange-500 rounded-md flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Integrations
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    LLM Setup
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </Link>
      </div>

      {/* Recent Items */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Collections */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent Collections
            </h3>
            {collectionsLoading ? (
              <div className="animate-pulse space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-4 bg-gray-200 rounded"></div>
                ))}
              </div>
            ) : collectionsData?.items?.length ? (
              <div className="space-y-3">
                {collectionsData.items.map((collection) => (
                  <div key={collection.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-md">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{collection.name}</p>
                      <p className="text-xs text-gray-500">{collection.description}</p>
                    </div>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {collection.type}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">No collections yet. Create your first collection!</p>
            )}
            <div className="mt-4">
              <Link
                to="/collections"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
              >
                View all collections →
              </Link>
            </div>
          </div>
        </div>

        {/* Recent Playbooks */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent Playbooks
            </h3>
            {playbooksLoading ? (
              <div className="animate-pulse space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-4 bg-gray-200 rounded"></div>
                ))}
              </div>
            ) : playbooksData?.items?.length ? (
              <div className="space-y-3">
                {playbooksData.items.map((playbook) => (
                  <div key={playbook.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-md">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{playbook.name}</p>
                      <p className="text-xs text-gray-500">{playbook.description}</p>
                    </div>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      {playbook.visibility}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">No playbooks yet. Create your first workflow!</p>
            )}
            <div className="mt-4">
              <Link
                to="/playbooks"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
              >
                View all playbooks →
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Admin Quick Access */}
      {isAdmin && (
        <div className="mt-8">
          <div className="bg-gray-900 rounded-lg p-6">
            <h3 className="text-lg font-medium text-white mb-4">Admin Dashboard</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Link
                to="/admin"
                className="bg-gray-800 hover:bg-gray-700 text-white p-4 rounded-md text-center transition-colors"
              >
                <div className="text-sm font-medium">System Management</div>
                <div className="text-xs text-gray-300 mt-1">Users, settings, health</div>
              </Link>
              <Link
                to="/admin#llm"
                className="bg-gray-800 hover:bg-gray-700 text-white p-4 rounded-md text-center transition-colors"
              >
                <div className="text-sm font-medium">LLM Configuration</div>
                <div className="text-xs text-gray-300 mt-1">Providers, budgets, limits</div>
              </Link>
              <Link
                to="/admin#usage"
                className="bg-gray-800 hover:bg-gray-700 text-white p-4 rounded-md text-center transition-colors"
              >
                <div className="text-sm font-medium">Usage Monitoring</div>
                <div className="text-xs text-gray-300 mt-1">Costs, alerts, analytics</div>
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
