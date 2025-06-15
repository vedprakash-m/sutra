import { useState, useEffect } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { Fragment } from 'react'
import { XMarkIcon, ClockIcon, UserIcon, EyeIcon, ArrowUturnLeftIcon } from '@heroicons/react/24/outline'

interface VersionHistoryProps {
  isOpen: boolean
  onClose: () => void
  promptId: string
  promptName: string
  onVersionRestore?: (versionId: string) => void
}

interface PromptVersion {
  id: string
  versionNumber: number
  promptText: string
  contextDetails: Record<string, any>
  createdAt: string
  createdBy: string
  changeNote?: string
  llmEvaluations: Array<{
    llm: string
    score: string
    feedback: string
  }>
}

export default function VersionHistory({ 
  isOpen, 
  onClose, 
  promptId, 
  promptName,
  onVersionRestore
}: VersionHistoryProps) {
  const [versions, setVersions] = useState<PromptVersion[]>([])
  const [selectedVersions, setSelectedVersions] = useState<[string, string] | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [showDiff, setShowDiff] = useState(false)

  // Mock data for demonstration
  useEffect(() => {
    if (isOpen && promptId) {
      setIsLoading(true)
      // Simulate API call
      setTimeout(() => {
        setVersions([
          {
            id: 'v3',
            versionNumber: 3,
            promptText: `Act as a senior marketing expert specializing in {{product_category}}.

Write a compelling marketing email for {{product_name}} targeting {{target_audience}}.

Key requirements:
- Use persuasive language that resonates with {{target_audience}}
- Highlight the main benefit: {{main_benefit}}
- Include a clear call-to-action
- Keep the tone {{tone_preference}}
- Limit to 150 words

Example format:
Subject: [Compelling subject line]
Body: [Personalized greeting + benefit + proof + CTA]`,
            contextDetails: {
              intention: 'Marketing email template',
              tone: 'persuasive',
              audience: 'professionals'
            },
            createdAt: '2025-06-15T10:30:00Z',
            createdBy: 'John Doe',
            changeNote: 'Added example format and character limit',
            llmEvaluations: [
              { llm: 'GPT-4o', score: 'Excellent', feedback: 'Clear structure and good examples' },
              { llm: 'Claude-3', score: 'Good', feedback: 'Well-structured but could be more specific' }
            ]
          },
          {
            id: 'v2',
            versionNumber: 2,
            promptText: `Act as a marketing expert for {{product_name}}.

Write a marketing email targeting {{target_audience}}.

Requirements:
- Use {{tone_preference}} tone
- Highlight {{main_benefit}}
- Include call-to-action
- Keep concise`,
            contextDetails: {
              intention: 'Marketing email',
              tone: 'persuasive',
              audience: 'general'
            },
            createdAt: '2025-06-14T15:45:00Z',
            createdBy: 'Jane Smith',
            changeNote: 'Added more variables and refined tone',
            llmEvaluations: [
              { llm: 'GPT-4o', score: 'Good', feedback: 'Solid structure' }
            ]
          },
          {
            id: 'v1',
            versionNumber: 1,
            promptText: `Write a marketing email for {{product_name}}.

Make it persuasive and include a call to action.`,
            contextDetails: {
              intention: 'Marketing email',
              tone: 'professional'
            },
            createdAt: '2025-06-14T09:20:00Z',
            createdBy: 'John Doe',
            changeNote: 'Initial version',
            llmEvaluations: [
              { llm: 'GPT-4o', score: 'Fair', feedback: 'Too generic, needs more specificity' }
            ]
          }
        ])
        setIsLoading(false)
      }, 500)
    }
  }, [isOpen, promptId])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const handleVersionSelect = (versionId: string) => {
    if (!selectedVersions) {
      setSelectedVersions([versionId, versionId])
    } else if (selectedVersions[0] === versionId) {
      setSelectedVersions(null)
    } else {
      setSelectedVersions([selectedVersions[0], versionId])
      setShowDiff(true)
    }
  }

  const handleRestoreVersion = (versionId: string) => {
    if (onVersionRestore) {
      onVersionRestore(versionId)
      onClose()
    }
  }

  const renderDiff = () => {
    if (!selectedVersions || selectedVersions[0] === selectedVersions[1]) return null

    const version1 = versions.find(v => v.id === selectedVersions[0])
    const version2 = versions.find(v => v.id === selectedVersions[1])

    if (!version1 || !version2) return null

    return (
      <div className="mt-6 border-t border-gray-200 pt-6">
        <h4 className="text-lg font-medium text-gray-900 mb-4">
          Comparing Version {version1.versionNumber} with Version {version2.versionNumber}
        </h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h5 className="text-sm font-medium text-gray-700 mb-2">
              Version {version1.versionNumber} ({formatDate(version1.createdAt)})
            </h5>
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <pre className="text-sm text-red-800 whitespace-pre-wrap">{version1.promptText}</pre>
            </div>
          </div>
          <div>
            <h5 className="text-sm font-medium text-gray-700 mb-2">
              Version {version2.versionNumber} ({formatDate(version2.createdAt)})
            </h5>
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <pre className="text-sm text-green-800 whitespace-pre-wrap">{version2.promptText}</pre>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-6xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex items-center justify-between mb-6">
                  <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-gray-900">
                    Version History: {promptName}
                  </Dialog.Title>
                  <button
                    onClick={onClose}
                    className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                {isLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                  </div>
                ) : (
                  <div>
                    <div className="mb-4">
                      <p className="text-sm text-gray-600">
                        Click versions to select for comparison. Selected: {selectedVersions ? selectedVersions.length : 0}
                      </p>
                    </div>

                    <div className="space-y-4 max-h-96 overflow-y-auto">
                      {versions.map((version) => {
                        const isSelected = selectedVersions?.includes(version.id)
                        return (
                          <div
                            key={version.id}
                            className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                              isSelected 
                                ? 'border-indigo-500 bg-indigo-50' 
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                            onClick={() => handleVersionSelect(version.id)}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-3 mb-2">
                                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                    Version {version.versionNumber}
                                  </span>
                                  <div className="flex items-center text-sm text-gray-500">
                                    <ClockIcon className="h-4 w-4 mr-1" />
                                    {formatDate(version.createdAt)}
                                  </div>
                                  <div className="flex items-center text-sm text-gray-500">
                                    <UserIcon className="h-4 w-4 mr-1" />
                                    {version.createdBy}
                                  </div>
                                </div>
                                
                                {version.changeNote && (
                                  <p className="text-sm text-gray-700 mb-2">{version.changeNote}</p>
                                )}

                                <div className="bg-gray-50 rounded p-3 mb-3">
                                  <p className="text-sm text-gray-600 line-clamp-3">
                                    {version.promptText}
                                  </p>
                                </div>

                                {version.llmEvaluations.length > 0 && (
                                  <div className="flex space-x-4 text-xs">
                                    {version.llmEvaluations.map((evaluation, idx) => (
                                      <div key={idx} className="flex items-center space-x-1">
                                        <span className="font-medium">{evaluation.llm}:</span>
                                        <span className={`px-2 py-1 rounded ${
                                          evaluation.score === 'Excellent' ? 'bg-green-100 text-green-800' :
                                          evaluation.score === 'Good' ? 'bg-blue-100 text-blue-800' :
                                          'bg-yellow-100 text-yellow-800'
                                        }`}>
                                          {evaluation.score}
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>

                              <div className="flex space-x-2 ml-4">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    // Show full version details
                                  }}
                                  className="p-2 text-gray-400 hover:text-gray-500 rounded-md hover:bg-gray-100"
                                  title="View details"
                                >
                                  <EyeIcon className="h-4 w-4" />
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleRestoreVersion(version.id)
                                  }}
                                  className="p-2 text-blue-600 hover:text-blue-700 rounded-md hover:bg-blue-50"
                                  title="Restore this version"
                                >
                                  <ArrowUturnLeftIcon className="h-4 w-4" />
                                </button>
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>

                    {showDiff && renderDiff()}

                    <div className="flex justify-end space-x-3 mt-6">
                      {selectedVersions && selectedVersions[0] !== selectedVersions[1] && (
                        <button
                          onClick={() => setShowDiff(!showDiff)}
                          className="px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-100 border border-transparent rounded-md hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                          {showDiff ? 'Hide Diff' : 'Show Diff'}
                        </button>
                      )}
                      <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        Close
                      </button>
                    </div>
                  </div>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}
