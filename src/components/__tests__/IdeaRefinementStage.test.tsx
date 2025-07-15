/**
 * IdeaRefinementStage.test.tsx - Unit tests for the IdeaRefinementStage component
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import IdeaRefinementStage from '../forge/IdeaRefinementStage';

// Mock the Heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  SparklesIcon: () => <div data-testid="sparkles-icon" />,
  LightBulbIcon: () => <div data-testid="lightbulb-icon" />,
  UserGroupIcon: () => <div data-testid="usergroup-icon" />,
  ChartBarIcon: () => <div data-testid="chartbar-icon" />,
  GlobeAltIcon: () => <div data-testid="globealt-icon" />,
  CogIcon: () => <div data-testid="cog-icon" />,
  CheckCircleIcon: () => <div data-testid="checkcircle-icon" />,
  ExclamationTriangleIcon: () => <div data-testid="exclamationtriangle-icon" />,
  DocumentTextIcon: () => <div data-testid="documenttext-icon" />,
  ArrowRightIcon: () => <div data-testid="arrowright-icon" />
}));

const mockProps = {
  projectId: 'test-project-id',
  selectedLLM: 'gpt-4',
  onDataUpdate: vi.fn(),
  onStageComplete: vi.fn()
};

describe('IdeaRefinementStage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the initial idea input section', () => {
    render(<IdeaRefinementStage {...mockProps} />);
    
    expect(screen.getByText('Idea Refinement')).toBeInTheDocument();
    expect(screen.getByText('Transform your concept into a structured opportunity through systematic analysis')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Describe your project idea/)).toBeInTheDocument();
    expect(screen.getByText('Start Analysis')).toBeInTheDocument();
  });

  it('shows the selected LLM in the header', () => {
    render(<IdeaRefinementStage {...mockProps} selectedLLM="claude-3" />);
    
    expect(screen.getByText('claude-3')).toBeInTheDocument();
  });

  it('enables the Start Analysis button when idea is entered', () => {
    render(<IdeaRefinementStage {...mockProps} />);
    
    const textarea = screen.getByPlaceholderText(/Describe your project idea/);
    const button = screen.getByText('Start Analysis');
    
    // Initially disabled
    expect(button).toBeDisabled();
    
    // Enable after typing
    fireEvent.change(textarea, { target: { value: 'My innovative app idea' } });
    expect(button).not.toBeDisabled();
  });

  it('calls onDataUpdate when data changes', () => {
    render(<IdeaRefinementStage {...mockProps} />);
    
    const textarea = screen.getByPlaceholderText(/Describe your project idea/);
    fireEvent.change(textarea, { target: { value: 'Test idea' } });
    
    expect(mockProps.onDataUpdate).toHaveBeenCalled();
  });

  it('moves to analysis section when Start Analysis is clicked', async () => {
    render(<IdeaRefinementStage {...mockProps} />);
    
    const textarea = screen.getByPlaceholderText(/Describe your project idea/);
    const button = screen.getByText('Start Analysis');
    
    fireEvent.change(textarea, { target: { value: 'My innovative app idea' } });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(screen.getByText('Multi-Dimensional Analysis')).toBeInTheDocument();
    });
  });

  it('shows analysis dimensions', async () => {
    render(<IdeaRefinementStage {...mockProps} />);
    
    const textarea = screen.getByPlaceholderText(/Describe your project idea/);
    const button = screen.getByText('Start Analysis');
    
    fireEvent.change(textarea, { target: { value: 'My innovative app idea' } });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(screen.getByText('Problem Definition')).toBeInTheDocument();
      expect(screen.getByText('Market Analysis')).toBeInTheDocument();
      expect(screen.getByText('User Focus')).toBeInTheDocument();
      expect(screen.getByText('Technical Scope')).toBeInTheDocument();
      expect(screen.getByText('Competitive Edge')).toBeInTheDocument();
    });
  });

  it('populates initial data when provided', () => {
    const initialData = {
      initialIdea: 'Pre-filled idea',
      problemStatement: 'Pre-filled problem',
      targetAudience: 'Pre-filled audience'
    };
    
    render(<IdeaRefinementStage {...mockProps} initialData={initialData} />);
    
    expect(screen.getByDisplayValue('Pre-filled idea')).toBeInTheDocument();
  });

  it('handles competitor addition and removal', async () => {
    render(<IdeaRefinementStage {...mockProps} />);
    
    // Navigate to refinement section
    const textarea = screen.getByPlaceholderText(/Describe your project idea/);
    fireEvent.change(textarea, { target: { value: 'Test idea' } });
    fireEvent.click(screen.getByText('Start Analysis'));
    
    // Wait for analysis to complete and move to refinement
    await waitFor(() => {
      expect(screen.getByText('Refine Your Idea')).toBeInTheDocument();
    }, { timeout: 3000 });
    
    // Add a competitor
    const competitorInput = screen.getByPlaceholderText(/Add a competitor/);
    fireEvent.change(competitorInput, { target: { value: 'Competitor Corp' } });
    fireEvent.click(screen.getByText('Add'));
    
    await waitFor(() => {
      expect(screen.getByText('Competitor Corp')).toBeInTheDocument();
    });
  });

  it('handles technical complexity selection', async () => {
    render(<IdeaRefinementStage {...mockProps} />);
    
    // Navigate to refinement section
    const textarea = screen.getByPlaceholderText(/Describe your project idea/);
    fireEvent.change(textarea, { target: { value: 'Test idea' } });
    fireEvent.click(screen.getByText('Start Analysis'));
    
    await waitFor(() => {
      expect(screen.getByText('Technical Complexity')).toBeInTheDocument();
    }, { timeout: 3000 });
    
    const complexitySelect = screen.getByDisplayValue('Medium - Moderate complexity');
    fireEvent.change(complexitySelect, { target: { value: 'high' } });
    
    expect(complexitySelect.value).toBe('high');
  });

  it('calls onStageComplete when stage is completed', async () => {
    render(<IdeaRefinementStage {...mockProps} />);
    
    // Navigate through the flow
    const textarea = screen.getByPlaceholderText(/Describe your project idea/);
    fireEvent.change(textarea, { target: { value: 'Test idea' } });
    fireEvent.click(screen.getByText('Start Analysis'));
    
    // Wait for refinement section
    await waitFor(() => {
      expect(screen.getByText('Complete Idea Refinement')).toBeInTheDocument();
    }, { timeout: 3000 });
    
    // Fill required fields
    const problemTextarea = screen.getByPlaceholderText(/Clearly define the problem/);
    const audienceTextarea = screen.getByPlaceholderText(/Describe who will use/);
    const valueTextarea = screen.getByPlaceholderText(/Explain the unique value/);
    
    fireEvent.change(problemTextarea, { target: { value: 'Test problem' } });
    fireEvent.change(audienceTextarea, { target: { value: 'Test audience' } });
    fireEvent.change(valueTextarea, { target: { value: 'Test value' } });
    
    // Complete the stage
    const completeButton = screen.getByText('Complete Idea Refinement');
    fireEvent.click(completeButton);
    
    expect(mockProps.onStageComplete).toHaveBeenCalled();
  });
});
