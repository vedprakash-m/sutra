import { useState, useEffect } from 'react'
import { LightBulbIcon, XMarkIcon, CheckIcon } from '@heroicons/react/24/outline'

interface PromptCoachProps {
  promptContent: string
  intention: string
  contextDetails: Record<string, any>
  onSuggestionApply?: (suggestion: string) => void
  className?: string
}

interface Suggestion {
  id: string
  type: 'structure' | 'clarity' | 'specificity' | 'examples' | 'format'
  title: string
  description: string
  example?: string
  priority: 'high' | 'medium' | 'low'
}

export default function PromptCoach({ 
  promptContent, 
  intention, 
  contextDetails, 
  onSuggestionApply,
  className = '' 
}: PromptCoachProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [dismissedSuggestions, setDismissedSuggestions] = useState<Set<string>>(new Set())
  const [isExpanded, setIsExpanded] = useState(true)

  // Analyze prompt and generate suggestions
  useEffect(() => {
    if (!promptContent.trim()) {
      setSuggestions([])
      return
    }

    const newSuggestions: Suggestion[] = []

    // Check for role specification
    if (!promptContent.toLowerCase().includes('act as') && !promptContent.toLowerCase().includes('you are')) {
      newSuggestions.push({
        id: 'add-role',
        type: 'structure',
        title: 'Add Role Specification',
        description: 'Start with "Act as [role]" to set clear context for the AI',
        example: 'Act as a professional marketing copywriter...',
        priority: 'high'
      })
    }

    // Check for specific instructions
    if (promptContent.length < 50) {
      newSuggestions.push({
        id: 'add-details',
        type: 'specificity',
        title: 'Add More Specific Instructions',
        description: 'Provide more detailed requirements for better results',
        example: 'Include specific tone, format, length, and key points to cover',
        priority: 'high'
      })
    }

    // Check for examples
    if (!promptContent.toLowerCase().includes('example') && !promptContent.includes('like this:')) {
      newSuggestions.push({
        id: 'add-examples',
        type: 'examples',
        title: 'Include Examples',
        description: 'Add examples to clarify the expected output format',
        example: 'For example: "Subject: Welcome to our premium service"',
        priority: 'medium'
      })
    }

    // Check for output format specification
    if (!promptContent.toLowerCase().includes('format') && !promptContent.toLowerCase().includes('structure')) {
      newSuggestions.push({
        id: 'specify-format',
        type: 'format',
        title: 'Specify Output Format',
        description: 'Define the desired output structure (bullet points, paragraphs, etc.)',
        example: 'Format the response as a bulleted list with clear headings',
        priority: 'medium'
      })
    }

    // Check for variables usage
    const hasVariables = /\{\{.*?\}\}/.test(promptContent)
    if (!hasVariables && intention.toLowerCase().includes('template')) {
      newSuggestions.push({
        id: 'add-variables',
        type: 'specificity',
        title: 'Use Variables for Reusability',
        description: 'Add {{variables}} to make this prompt reusable',
        example: 'Write about {{product_name}} for {{target_audience}}',
        priority: 'medium'
      })
    }

    // Check for step-by-step instructions
    if (intention.toLowerCase().includes('complex') || intention.toLowerCase().includes('detailed')) {
      if (!promptContent.toLowerCase().includes('step') && !promptContent.toLowerCase().includes('first')) {
        newSuggestions.push({
          id: 'add-steps',
          type: 'structure',
          title: 'Use Step-by-Step Approach',
          description: 'Break down complex tasks into clear steps',
          example: 'Follow these steps: 1) Analyze the requirements, 2) Draft the content, 3) Review and refine',
          priority: 'medium'
        })
      }
    }

    // Check for constraints
    if (!promptContent.toLowerCase().includes('limit') && !promptContent.toLowerCase().includes('words') && !promptContent.toLowerCase().includes('length')) {
      newSuggestions.push({
        id: 'add-constraints',
        type: 'clarity',
        title: 'Set Clear Constraints',
        description: 'Specify length, word count, or other limitations',
        example: 'Keep the response under 200 words and use professional tone',
        priority: 'low'
      })
    }

    // Filter out dismissed suggestions
    const filteredSuggestions = newSuggestions.filter(s => !dismissedSuggestions.has(s.id))
    setSuggestions(filteredSuggestions)
  }, [promptContent, intention, contextDetails, dismissedSuggestions])

  const handleDismissSuggestion = (suggestionId: string) => {
    setDismissedSuggestions(prev => new Set([...prev, suggestionId]))
  }

  const handleApplySuggestion = (suggestion: Suggestion) => {
    if (onSuggestionApply && suggestion.example) {
      onSuggestionApply(suggestion.example)
    }
    handleDismissSuggestion(suggestion.id)
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200'
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'low': return 'text-green-600 bg-green-50 border-green-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'structure': return '🏗️'
      case 'clarity': return '🔍'
      case 'specificity': return '🎯'
      case 'examples': return '💡'
      case 'format': return '📄'
      default: return '💭'
    }
  }

  if (suggestions.length === 0) {
    return (
      <div className={`bg-green-50 border border-green-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center space-x-2">
          <CheckIcon className="h-5 w-5 text-green-600" />
          <span className="text-green-800 font-medium">Great prompt structure!</span>
        </div>
        <p className="text-green-700 text-sm mt-1">Your prompt follows best practices.</p>
      </div>
    )
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg ${className}`}>
      <div 
        className="flex items-center justify-between p-3 cursor-pointer border-b border-gray-200"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-2">
          <LightBulbIcon className="h-5 w-5 text-blue-600" />
          <span className="font-medium text-gray-900">PromptCoach</span>
          <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
            {suggestions.length} suggestion{suggestions.length !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="text-gray-400">
          {isExpanded ? '−' : '+'}
        </div>
      </div>

      {isExpanded && (
        <div className="p-3 space-y-3">
          {suggestions.map((suggestion) => (
            <div 
              key={suggestion.id}
              className={`border rounded-lg p-3 ${getPriorityColor(suggestion.priority)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-sm">{getTypeIcon(suggestion.type)}</span>
                    <h4 className="font-medium text-sm">{suggestion.title}</h4>
                    <span className="text-xs uppercase font-medium px-2 py-1 rounded bg-white bg-opacity-50">
                      {suggestion.priority}
                    </span>
                  </div>
                  <p className="text-sm opacity-80 mb-2">{suggestion.description}</p>
                  {suggestion.example && (
                    <div className="bg-white bg-opacity-50 rounded p-2 text-xs font-mono">
                      {suggestion.example}
                    </div>
                  )}
                </div>
                <div className="flex space-x-1 ml-2">
                  {suggestion.example && onSuggestionApply && (
                    <button
                      onClick={() => handleApplySuggestion(suggestion)}
                      className="p-1 hover:bg-white hover:bg-opacity-50 rounded"
                      title="Apply suggestion"
                    >
                      <CheckIcon className="h-4 w-4" />
                    </button>
                  )}
                  <button
                    onClick={() => handleDismissSuggestion(suggestion.id)}
                    className="p-1 hover:bg-white hover:bg-opacity-50 rounded"
                    title="Dismiss suggestion"
                  >
                    <XMarkIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
