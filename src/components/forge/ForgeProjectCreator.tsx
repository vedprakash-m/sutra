/**
 * ForgeProjectCreator - Component for creating new Forge projects
 */
import React, { useState } from 'react';
import { XMarkIcon, SparklesIcon } from '@heroicons/react/24/outline';
// import { forgeApiService } from '../services/forgeApi';

interface ForgeProject {
  id: string;
  name: string;
  description: string;
  currentStage: 'idea_refinement' | 'prd_generation' | 'ux_requirements' | 'technical_analysis' | 'implementation_playbook';
  status: 'draft' | 'active' | 'on_hold' | 'completed' | 'archived' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  progressPercentage: number;
  createdAt: string;
  updatedAt: string;
  tags: string[];
  collaboratorsCount: number;
  artifactsCount: number;
  ownerId: string;
}

interface ForgeProjectCreatorProps {
  onProjectCreated: (project: ForgeProject) => void;
  onCancel: () => void;
}

const PROJECT_TEMPLATES = [
  {
    id: 'ai-app',
    name: 'AI Application',
    description: 'Build an AI-powered application with systematic analysis',
    icon: '🤖',
    tags: ['ai', 'application', 'technology'],
    sampleIdea: 'An AI-powered customer support chatbot that can handle common inquiries and escalate complex issues to human agents. Need comprehensive analysis of user flows, technical architecture, and implementation strategy.'
  },
  {
    id: 'saas-product',
    name: 'SaaS Product',
    description: 'Create a software-as-a-service product with detailed requirements',
    icon: '💼',
    tags: ['saas', 'product', 'business'],
    sampleIdea: 'A project management tool that helps remote teams collaborate more effectively. Requires thorough market analysis, user journey mapping, and technical specification for scalable architecture.'
  },
  {
    id: 'mobile-app',
    name: 'Mobile App',
    description: 'Develop a mobile application with comprehensive planning',
    icon: '📱',
    tags: ['mobile', 'app', 'ios', 'android'],
    sampleIdea: 'A fitness tracking app that gamifies workouts and connects users with personal trainers. Need detailed UX requirements, technical stack analysis, and step-by-step implementation guide.'
  },
  {
    id: 'ecommerce',
    name: 'E-commerce Platform',
    description: 'Build an online marketplace with detailed specifications',
    icon: '🛒',
    tags: ['ecommerce', 'marketplace', 'retail'],
    sampleIdea: 'A sustainable fashion marketplace that connects eco-conscious consumers with ethical clothing brands. Requires market validation, complex user flows, and scalable technical architecture.'
  },
  {
    id: 'data-platform',
    name: 'Data Platform',
    description: 'Create a data analytics platform with systematic design',
    icon: '📊',
    tags: ['data', 'analytics', 'visualization'],
    sampleIdea: 'A business intelligence platform that automatically generates insights from company data. Need comprehensive technical analysis for data processing, visualization requirements, and implementation roadmap.'
  },
  {
    id: 'custom',
    name: 'Custom Project',
    description: 'Start from scratch with systematic idea development',
    icon: '✨',
    tags: ['custom'],
    sampleIdea: ''
  }
];

export default function ForgeProjectCreator({ onProjectCreated, onCancel }: ForgeProjectCreatorProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    priority: 'medium' as const,
    tags: [] as string[],
    initialIdea: ''
  });
  const [tagInput, setTagInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplate(templateId);
    const template = PROJECT_TEMPLATES.find(t => t.id === templateId);
    if (template) {
      setFormData(prev => ({
        ...prev,
        tags: [...template.tags],
        initialIdea: template.sampleIdea
      }));
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleAddTag = () => {
    const tag = tagInput.trim().toLowerCase();
    if (tag && !formData.tags.includes(tag)) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tag]
      }));
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Project name is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Project description is required';
    }

    if (!formData.initialIdea.trim()) {
      newErrors.initialIdea = 'Initial idea is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      const projectData = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        priority: formData.priority,
        tags: formData.tags,
        templateId: selectedTemplate !== 'custom' ? selectedTemplate : undefined,
        customFields: {
          initialIdea: formData.initialIdea.trim()
        }
      };

      // TODO: Implement forgeApiService.createProject
      // const project = await forgeApiService.createProject(projectData);
      const project: ForgeProject = {
        id: Date.now().toString(),
        name: projectData.name,
        description: projectData.description,
        currentStage: 'idea_refinement',
        status: 'active',
        priority: projectData.priority,
        progressPercentage: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        tags: projectData.tags,
        collaboratorsCount: 1,
        artifactsCount: 0,
        ownerId: 'current-user'
      };
      
      onProjectCreated(project);
    } catch (error) {
      console.error('Error creating project:', error);
      setErrors({ submit: 'Failed to create project. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Create New Project</h1>
          <p className="mt-2 text-gray-600">
            Start your journey from idea to deployment with AI-powered guidance
          </p>
        </div>
        <button
          onClick={onCancel}
          className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full"
        >
          <XMarkIcon className="h-6 w-6" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Template Selection */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Choose a Template</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {PROJECT_TEMPLATES.map((template) => (
              <div
                key={template.id}
                className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  selectedTemplate === template.id
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleTemplateSelect(template.id)}
              >
                <div className="text-3xl mb-2">{template.icon}</div>
                <h3 className="font-semibold text-gray-900 mb-1">{template.name}</h3>
                <p className="text-sm text-gray-600">{template.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Project Details */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Project Details</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Project Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Project Name *
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 ${
                  errors.name ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Enter project name"
              />
              {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
            </div>

            {/* Priority */}
            <div>
              <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-2">
                Priority
              </label>
              <select
                id="priority"
                value={formData.priority}
                onChange={(e) => handleInputChange('priority', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          {/* Description */}
          <div className="mt-6">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Project Description *
            </label>
            <textarea
              id="description"
              rows={3}
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 ${
                errors.description ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Describe your project in a few sentences"
            />
            {errors.description && <p className="mt-1 text-sm text-red-600">{errors.description}</p>}
          </div>

          {/* Initial Idea */}
          <div className="mt-6">
            <div className="flex items-center mb-2">
              <label htmlFor="initialIdea" className="block text-sm font-medium text-gray-700">
                Initial Idea *
              </label>
              <SparklesIcon className="h-4 w-4 text-indigo-500 ml-2" />
            </div>
            <textarea
              id="initialIdea"
              rows={4}
              value={formData.initialIdea}
              onChange={(e) => handleInputChange('initialIdea', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 ${
                errors.initialIdea ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Describe your initial idea in detail. What problem does it solve? Who is your target audience?"
            />
            {errors.initialIdea && <p className="mt-1 text-sm text-red-600">{errors.initialIdea}</p>}
            <p className="mt-1 text-sm text-gray-500">
              This will be enhanced with AI suggestions in the Conception stage
            </p>
          </div>

          {/* Tags */}
          <div className="mt-6">
            <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-2">
              Tags
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              {formData.tags.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(tag)}
                    className="ml-1 h-4 w-4 text-indigo-600 hover:text-indigo-800"
                  >
                    <XMarkIcon className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={handleKeyPress}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Add a tag"
              />
              <button
                type="button"
                onClick={handleAddTag}
                className="px-4 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 text-gray-600 hover:bg-gray-100"
              >
                Add
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {errors.submit && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{errors.submit}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Creating...' : 'Create Project'}
          </button>
        </div>
      </form>
    </div>
  );
}
