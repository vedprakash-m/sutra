import React, { useState } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { Fragment } from 'react'
import { 
  XMarkIcon, 
  DocumentArrowUpIcon, 
  ClipboardDocumentIcon,
  ChatBubbleLeftRightIcon,
  CodeBracketIcon
} from '@heroicons/react/24/outline'

interface ImportModalProps {
  isOpen: boolean
  onClose: () => void
  onImport: (prompts: ImportedPrompt[]) => void
}

interface ImportedPrompt {
  title: string
  content: string
  description?: string
  source: string
  variables?: Record<string, any>
}

export default function ImportModal({ isOpen, onClose, onImport }: ImportModalProps) {
  const [importMethod, setImportMethod] = useState<'file' | 'text' | 'chatgpt' | 'gemini'>('text')
  const [textInput, setTextInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [previewPrompts, setPreviewPrompts] = useState<ImportedPrompt[]>([])

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      setIsProcessing(true)
      const content = await file.text()
      
      if (file.name.endsWith('.json')) {
        // Handle JSON format (ChatGPT export format)
        const data = JSON.parse(content)
        const prompts = parseChatGPTExport(data)
        setPreviewPrompts(prompts)
      } else if (file.name.endsWith('.txt') || file.name.endsWith('.md')) {
        // Handle text/markdown files
        const prompts = parseTextFile(content)
        setPreviewPrompts(prompts)
      } else {
        alert('Unsupported file format. Please use JSON, TXT, or MD files.')
      }
    } catch (error) {
      console.error('Error processing file:', error)
      alert('Error processing file. Please check the format and try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleTextImport = () => {
    if (!textInput.trim()) return
    
    setIsProcessing(true)
    try {
      const prompts = parseTextInput(textInput)
      setPreviewPrompts(prompts)
    } catch (error) {
      console.error('Error parsing text:', error)
      alert('Error parsing text. Please check the format and try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  const parseChatGPTExport = (data: any): ImportedPrompt[] => {
    // Parse ChatGPT export format
    const prompts: ImportedPrompt[] = []
    
    if (data.conversations) {
      data.conversations.forEach((conversation: any, index: number) => {
        const title = conversation.title || `Imported Chat ${index + 1}`
        let content = ''
        
        // Extract user messages that look like prompts
        conversation.messages?.forEach((message: any) => {
          if (message.author === 'user' && message.content) {
            content += message.content + '\n\n'
          }
        })
        
        if (content.trim()) {
          prompts.push({
            title,
            content: content.trim(),
            description: `Imported from ChatGPT conversation`,
            source: 'ChatGPT',
            variables: extractVariables(content)
          })
        }
      })
    }
    
    return prompts
  }

  const parseTextFile = (content: string): ImportedPrompt[] => {
    const prompts: ImportedPrompt[] = []
    
    // Split by double newlines or markdown headers
    const sections = content.split(/\n\n+|\n#+\s/g)
    
    sections.forEach((section, index) => {
      const lines = section.trim().split('\n')
      if (lines.length === 0) return
      
      const title = lines[0].replace(/^#+\s*/, '').trim() || `Imported Prompt ${index + 1}`
      const content = lines.slice(1).join('\n').trim() || lines[0]
      
      if (content) {
        prompts.push({
          title,
          content,
          description: `Imported from text file`,
          source: 'Text File',
          variables: extractVariables(content)
        })
      }
    })
    
    return prompts
  }

  const parseTextInput = (text: string): ImportedPrompt[] => {
    const prompts: ImportedPrompt[] = []
    
    // Try to split by common separators
    const sections = text.split(/\n---+\n|\n===+\n|\n\n\n+/)
    
    sections.forEach((section, index) => {
      const content = section.trim()
      if (!content) return
      
      // Try to extract title from first line if it looks like a header
      const lines = content.split('\n')
      let title = `Imported Prompt ${index + 1}`
      let promptContent = content
      
      if (lines[0].length < 100 && lines.length > 1) {
        title = lines[0].replace(/^#+\s*/, '').trim()
        promptContent = lines.slice(1).join('\n').trim()
      }
      
      prompts.push({
        title,
        content: promptContent,
        description: 'Imported from manual input',
        source: 'Manual Input',
        variables: extractVariables(promptContent)
      })
    })
    
    return prompts
  }

  const extractVariables = (content: string): Record<string, any> => {
    const variables: Record<string, any> = {}
    
    // Look for {{variable}} patterns
    const matches = content.match(/\{\{([^}]+)\}\}/g)
    if (matches) {
      matches.forEach(match => {
        const varName = match.replace(/\{\{|\}\}/g, '').trim()
        variables[varName] = {
          type: 'string',
          label: varName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          description: `Variable extracted from prompt`
        }
      })
    }
    
    return variables
  }

  const handleImport = () => {
    if (previewPrompts.length > 0) {
      onImport(previewPrompts)
      onClose()
      setPreviewPrompts([])
      setTextInput('')
    }
  }

  const handleClose = () => {
    setPreviewPrompts([])
    setTextInput('')
    onClose()
  }

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
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
              <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex items-center justify-between mb-6">
                  <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-gray-900">
                    Import Prompts
                  </Dialog.Title>
                  <button
                    onClick={handleClose}
                    className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                {previewPrompts.length === 0 ? (
                  <div>
                    {/* Import Method Selection */}
                    <div className="mb-6">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Choose import method:</h4>
                      <div className="grid grid-cols-2 gap-3">
                        <button
                          onClick={() => setImportMethod('text')}
                          className={`p-4 border-2 rounded-lg text-left ${
                            importMethod === 'text' 
                              ? 'border-indigo-500 bg-indigo-50' 
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <ClipboardDocumentIcon className="h-6 w-6 text-gray-600 mb-2" />
                          <div className="font-medium">Paste Text</div>
                          <div className="text-sm text-gray-500">Copy and paste your prompts</div>
                        </button>
                        
                        <button
                          onClick={() => setImportMethod('file')}
                          className={`p-4 border-2 rounded-lg text-left ${
                            importMethod === 'file' 
                              ? 'border-indigo-500 bg-indigo-50' 
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <DocumentArrowUpIcon className="h-6 w-6 text-gray-600 mb-2" />
                          <div className="font-medium">Upload File</div>
                          <div className="text-sm text-gray-500">JSON, TXT, or MD files</div>
                        </button>
                        
                        <button
                          onClick={() => setImportMethod('chatgpt')}
                          className={`p-4 border-2 rounded-lg text-left ${
                            importMethod === 'chatgpt' 
                              ? 'border-indigo-500 bg-indigo-50' 
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <ChatBubbleLeftRightIcon className="h-6 w-6 text-gray-600 mb-2" />
                          <div className="font-medium">ChatGPT Export</div>
                          <div className="text-sm text-gray-500">Import from ChatGPT conversations</div>
                        </button>
                        
                        <button
                          onClick={() => setImportMethod('gemini')}
                          className={`p-4 border-2 rounded-lg text-left ${
                            importMethod === 'gemini' 
                              ? 'border-indigo-500 bg-indigo-50' 
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <CodeBracketIcon className="h-6 w-6 text-gray-600 mb-2" />
                          <div className="font-medium">Gemini Export</div>
                          <div className="text-sm text-gray-500">Import from Google Gemini</div>
                        </button>
                      </div>
                    </div>

                    {/* Import Content */}
                    <div className="space-y-4">
                      {importMethod === 'text' && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Paste your prompts here:
                          </label>
                          <textarea
                            value={textInput}
                            onChange={(e) => setTextInput(e.target.value)}
                            rows={10}
                            className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                            placeholder="Paste multiple prompts separated by --- or empty lines..."
                          />
                          <p className="mt-2 text-sm text-gray-500">
                            Separate multiple prompts with "---" or double line breaks
                          </p>
                        </div>
                      )}

                      {importMethod === 'file' && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Choose file to upload:
                          </label>
                          <input
                            type="file"
                            accept=".json,.txt,.md"
                            onChange={handleFileUpload}
                            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                          />
                          <p className="mt-2 text-sm text-gray-500">
                            Supported formats: JSON (ChatGPT export), TXT, MD
                          </p>
                        </div>
                      )}

                      {(importMethod === 'chatgpt' || importMethod === 'gemini') && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <h5 className="font-medium text-blue-900 mb-2">
                            {importMethod === 'chatgpt' ? 'ChatGPT Export Instructions:' : 'Gemini Export Instructions:'}
                          </h5>
                          <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                            {importMethod === 'chatgpt' ? (
                              <>
                                <li>Go to ChatGPT Settings → Data Controls</li>
                                <li>Click "Export data" and download your conversations</li>
                                <li>Upload the conversations.json file here</li>
                              </>
                            ) : (
                              <>
                                <li>Go to Gemini activity page</li>
                                <li>Export your conversation history</li>
                                <li>Upload the exported file here</li>
                              </>
                            )}
                          </ol>
                        </div>
                      )}
                    </div>

                    <div className="flex justify-end space-x-3 mt-6">
                      <button
                        onClick={handleClose}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={importMethod === 'text' ? handleTextImport : undefined}
                        disabled={isProcessing || (importMethod === 'text' && !textInput.trim())}
                        className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 disabled:opacity-50"
                      >
                        {isProcessing ? 'Processing...' : 'Preview Import'}
                      </button>
                    </div>
                  </div>
                ) : (
                  /* Preview Screen */
                  <div>
                    <div className="mb-4">
                      <h4 className="text-lg font-medium text-gray-900">Import Preview</h4>
                      <p className="text-sm text-gray-600">
                        Found {previewPrompts.length} prompt{previewPrompts.length !== 1 ? 's' : ''} to import
                      </p>
                    </div>

                    <div className="max-h-96 overflow-y-auto space-y-4 mb-6">
                      {previewPrompts.map((prompt, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex items-start justify-between mb-2">
                            <h5 className="font-medium text-gray-900">{prompt.title}</h5>
                            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                              {prompt.source}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{prompt.description}</p>
                          <div className="bg-gray-50 rounded p-3 text-sm">
                            <p className="line-clamp-3">{prompt.content}</p>
                          </div>
                          {Object.keys(prompt.variables || {}).length > 0 && (
                            <div className="mt-2">
                              <span className="text-xs text-gray-500">
                                Variables: {Object.keys(prompt.variables || {}).join(', ')}
                              </span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>

                    <div className="flex justify-end space-x-3">
                      <button
                        onClick={() => setPreviewPrompts([])}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                      >
                        Back
                      </button>
                      <button
                        onClick={handleImport}
                        className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700"
                      >
                        Import {previewPrompts.length} Prompt{previewPrompts.length !== 1 ? 's' : ''}
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
