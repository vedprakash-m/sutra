import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/components/auth/AuthProvider'
import { useApi } from '@/hooks/useApi'
import { collectionsApi } from '@/services/api'
import VersionHistory from './VersionHistory'
import ImportModal from './ImportModal'

export default function CollectionsPage() {
  const { user } = useAuth()
  const [searchTerm, setSearchTerm] = useState('')
  const [versionHistoryModal, setVersionHistoryModal] = useState<{
    isOpen: boolean
    promptId: string
    promptName: string
  }>({
    isOpen: false,
    promptId: '',
    promptName: ''
  })
  const [importModalOpen, setImportModalOpen] = useState(false)
  
  // Fetch collections from API
  const { data: collectionsData, loading, error, refetch } = useApi(
    () => collectionsApi.list({ search: searchTerm }),
    [searchTerm]
  )

  const handleCreateCollection = async () => {
    try {
      const newCollection = {
        name: 'New Collection',
        description: 'A new collection for organizing prompts',
        type: 'private' as const,
        owner_id: user?.id || 'dev-user'
      }
      await collectionsApi.create(newCollection)
      refetch()
    } catch (error) {
      console.error('Error creating collection:', error)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Collections</h1>
          <p className="mt-1 text-sm text-gray-600">
            Organize and manage your prompt collections
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            type="button"
            onClick={() => setImportModalOpen(true)}
            className="bg-white text-gray-700 py-2 px-4 rounded-md border border-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            Import Prompts
          </button>
          <button
            type="button"
            onClick={handleCreateCollection}
            className="bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            New Collection
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search collections..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="block w-full max-w-md border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
        />
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading collections...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="text-center py-8">
          <p className="text-red-600">Error loading collections. Please try again.</p>
        </div>
      )}

      {/* Collections Grid */}
      {!loading && !error && (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {collectionsData?.items?.map((collection) => (
            <div key={collection.id} className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-indigo-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-medium">
                        {collection.name.charAt(0)}
                      </span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        {collection.name}
                      </dt>
                      <dd className="text-sm text-gray-900">
                        {collection.description}
                      </dd>
                    </dl>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>{collection.prompt_count || 0} prompts</span>
                    <span>Updated {formatDate(collection.updated_at)}</span>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3">
                <div className="flex justify-between items-center text-sm">
                  <Link
                    to={`/collections/${collection.id}`}
                    className="font-medium text-indigo-700 hover:text-indigo-900"
                  >
                    View collection
                  </Link>
                  <button
                    onClick={() => setVersionHistoryModal({
                      isOpen: true,
                      promptId: collection.id,
                      promptName: collection.name
                    })}
                    className="font-medium text-gray-600 hover:text-gray-900"
                  >
                    History
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* Empty state when no collections */}
          {collectionsData?.items?.length === 0 && (
            <div className="col-span-full text-center py-8">
              <p className="text-gray-500">No collections found. Create your first collection to get started!</p>
            </div>
          )}

          {/* Create New Collection Card */}
          <div className="bg-white overflow-hidden shadow rounded-lg border-2 border-dashed border-gray-300">
            <div className="p-5">
              <div className="text-center">
                <div className="w-8 h-8 bg-gray-400 rounded-md flex items-center justify-center mx-auto">
                  <span className="text-white text-sm font-medium">+</span>
                </div>
                <h3 className="mt-2 text-sm font-medium text-gray-900">Create new collection</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by creating a new prompt collection
                </p>
                <div className="mt-3">
                  <button
                    type="button"
                    onClick={handleCreateCollection}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
                  >
                    New Collection
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Version History Modal */}
      <VersionHistory
        isOpen={versionHistoryModal.isOpen}
        onClose={() => setVersionHistoryModal({ isOpen: false, promptId: '', promptName: '' })}
        promptId={versionHistoryModal.promptId}
        promptName={versionHistoryModal.promptName}
        onVersionRestore={(versionId) => {
          console.log('Restoring version:', versionId)
          // TODO: Implement version restore logic
        }}
      />

      {/* Import Modal */}
      <ImportModal
        isOpen={importModalOpen}
        onClose={() => setImportModalOpen(false)}
        onImport={(prompts) => {
          console.log('Importing prompts:', prompts)
          // TODO: Implement actual import logic
          // Create collections for each imported prompt
          prompts.forEach(async (prompt) => {
            try {
              await collectionsApi.create({
                name: prompt.title,
                description: prompt.description || 'Imported prompt',
                type: 'private' as const,
                owner_id: user?.id || 'dev-user',
                tags: ['imported', prompt.source.toLowerCase()]
              })
            } catch (error) {
              console.error('Error importing prompt:', error)
            }
          })
          refetch() // Refresh the collections list
        }}
      />
    </div>
  )
}
