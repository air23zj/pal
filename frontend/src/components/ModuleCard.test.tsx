import { render, screen, fireEvent } from '@testing-library/react'
import ModuleCard from './ModuleCard'
import { ModuleResult } from '@/types/brief'

describe('ModuleCard Component', () => {
  const mockModule: ModuleResult = {
    status: 'ok',
    new_count: 3,
    updated_count: 2,
    summary: 'You have 5 new updates',
    items: [
      {
        item_ref: 'item-1',
        source: 'gmail',
        type: 'email',
        timestamp_utc: '2026-01-19T10:00:00Z',
        title: 'Important Email',
        summary: 'This is an important email',
        why_it_matters: 'Requires immediate action',
        entities: [],
        novelty: {
          label: 'NEW',
          first_seen_utc: '2026-01-19T10:00:00Z',
          last_updated_utc: '2026-01-19T10:00:00Z',
          seen_count: 0,
        },
        ranking: {
          relevance: 0.9,
          urgency: 0.8,
          credibility: 0.95,
          actionability: 0.85,
          impact_score: 0.9,
          final_score: 0.89,
        },
        evidence: [],
        suggested_actions: [],
        source_id: 'email-1',
        url: null,
      },
      {
        item_ref: 'item-2',
        source: 'gmail',
        type: 'email',
        timestamp_utc: '2026-01-19T11:00:00Z',
        title: 'Updated Task',
        summary: 'Task has been updated',
        why_it_matters: 'Review changes',
        entities: [],
        novelty: {
          label: 'UPDATED',
          first_seen_utc: '2026-01-18T10:00:00Z',
          last_updated_utc: '2026-01-19T11:00:00Z',
          seen_count: 1,
        },
        ranking: {
          relevance: 0.7,
          urgency: 0.6,
          credibility: 0.8,
          actionability: 0.7,
          impact_score: 0.7,
          final_score: 0.71,
        },
        evidence: [],
        suggested_actions: [],
        source_id: 'email-2',
        url: null,
      },
    ],
  }

  describe('Rendering', () => {
    it('renders the module title', () => {
      render(<ModuleCard title="Test Module" module={mockModule} />)
      expect(screen.getByText('Test Module')).toBeInTheDocument()
    })

    it('renders status badge with correct label for ok status', () => {
      render(<ModuleCard title="Test Module" module={mockModule} />)
      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    it('renders status badge with correct label for degraded status', () => {
      const degradedModule = { ...mockModule, status: 'degraded' as const }
      render(<ModuleCard title="Test Module" module={degradedModule} />)
      expect(screen.getByText('Degraded')).toBeInTheDocument()
    })

    it('renders status badge with correct label for error status', () => {
      const errorModule = { ...mockModule, status: 'error' as const }
      render(<ModuleCard title="Test Module" module={errorModule} />)
      expect(screen.getByText('Error')).toBeInTheDocument()
    })

    it('renders status badge with correct label for skipped status', () => {
      const skippedModule = { ...mockModule, status: 'skipped' as const }
      render(<ModuleCard title="Test Module" module={skippedModule} />)
      expect(screen.getByText('Skipped')).toBeInTheDocument()
    })

    it('renders the summary when provided', () => {
      render(<ModuleCard title="Test Module" module={mockModule} />)
      expect(screen.getByText('You have 5 new updates')).toBeInTheDocument()
    })

    it('does not render summary section when summary is not provided', () => {
      const moduleWithoutSummary = { ...mockModule, summary: null }
      render(<ModuleCard title="Test Module" module={moduleWithoutSummary} />)
      expect(screen.queryByText('You have 5 new updates')).not.toBeInTheDocument()
    })
  })

  describe('Counts Display', () => {
    it('displays new count when greater than 0', () => {
      render(<ModuleCard title="Test Module" module={mockModule} />)
      expect(screen.getByText('3 new')).toBeInTheDocument()
    })

    it('displays updated count when greater than 0', () => {
      render(<ModuleCard title="Test Module" module={mockModule} />)
      expect(screen.getByText('2 updated')).toBeInTheDocument()
    })

    it('displays "No updates" when both counts are 0', () => {
      const moduleWithNoUpdates = { ...mockModule, new_count: 0, updated_count: 0 }
      render(<ModuleCard title="Test Module" module={moduleWithNoUpdates} />)
      expect(screen.getByText('No updates')).toBeInTheDocument()
    })

    it('does not display updated count when it is 0', () => {
      const moduleWithOnlyNew = { ...mockModule, updated_count: 0 }
      render(<ModuleCard title="Test Module" module={moduleWithOnlyNew} />)
      expect(screen.getByText('3 new')).toBeInTheDocument()
      expect(screen.queryByText(/updated/)).not.toBeInTheDocument()
    })

    it('does not display new count when it is 0', () => {
      const moduleWithOnlyUpdated = { ...mockModule, new_count: 0, updated_count: 2, summary: 'Only updated items' }
      render(<ModuleCard title="Test Module" module={moduleWithOnlyUpdated} />)
      expect(screen.getByText('2 updated')).toBeInTheDocument()
      expect(screen.queryByText(/\d+ new/)).not.toBeInTheDocument()
    })
  })

  describe('Items Expansion', () => {
    it('initially shows items collapsed', () => {
      render(<ModuleCard title="Test Module" module={mockModule} />)
      expect(screen.getByText('▶ Show 2 items')).toBeInTheDocument()
      expect(screen.queryByText('Important Email')).not.toBeInTheDocument()
    })

    it('expands to show items when clicked', () => {
      render(<ModuleCard title="Test Module" module={mockModule} />)
      const button = screen.getByText('▶ Show 2 items')
      fireEvent.click(button)
      expect(screen.getByText('▼ Hide 2 items')).toBeInTheDocument()
      expect(screen.getByText('Important Email')).toBeInTheDocument()
      expect(screen.getByText('Updated Task')).toBeInTheDocument()
    })

    it('collapses items when clicked again', () => {
      render(<ModuleCard title="Test Module" module={mockModule} />)
      const button = screen.getByText('▶ Show 2 items')
      
      // Expand
      fireEvent.click(button)
      expect(screen.getByText('Important Email')).toBeInTheDocument()
      
      // Collapse
      const hideButton = screen.getByText('▼ Hide 2 items')
      fireEvent.click(hideButton)
      expect(screen.queryByText('Important Email')).not.toBeInTheDocument()
    })

    it('displays correct item count', () => {
      render(<ModuleCard title="Test Module" module={mockModule} />)
      expect(screen.getByText(/2 items/)).toBeInTheDocument()
    })

    it('does not show expansion button when no items', () => {
      const moduleWithNoItems = { ...mockModule, items: [] }
      render(<ModuleCard title="Test Module" module={moduleWithNoItems} />)
      expect(screen.queryByText(/items/)).not.toBeInTheDocument()
    })
  })

  describe('Item Rendering', () => {
    beforeEach(() => {
      render(<ModuleCard title="Test Module" module={mockModule} />)
      const button = screen.getByText('▶ Show 2 items')
      fireEvent.click(button)
    })

    it('displays item title', () => {
      expect(screen.getByText('Important Email')).toBeInTheDocument()
      expect(screen.getByText('Updated Task')).toBeInTheDocument()
    })

    it('displays item summary', () => {
      expect(screen.getByText('This is an important email')).toBeInTheDocument()
      expect(screen.getByText('Task has been updated')).toBeInTheDocument()
    })

    it('displays why it matters', () => {
      expect(screen.getByText('Requires immediate action')).toBeInTheDocument()
      expect(screen.getByText('Review changes')).toBeInTheDocument()
    })

    it('displays NEW badge for new items', () => {
      const badges = screen.getAllByText('NEW')
      expect(badges.length).toBeGreaterThan(0)
    })

    it('displays UPDATED badge for updated items', () => {
      const badges = screen.getAllByText('UPDATED')
      expect(badges.length).toBeGreaterThan(0)
    })

    it('applies correct styling to NEW badge', () => {
      const newBadge = screen.getAllByText('NEW')[0]
      expect(newBadge).toHaveClass('bg-blue-100')
      expect(newBadge).toHaveClass('text-blue-700')
    })

    it('applies correct styling to UPDATED badge', () => {
      const updatedBadge = screen.getAllByText('UPDATED')[0]
      expect(updatedBadge).toHaveClass('bg-orange-100')
      expect(updatedBadge).toHaveClass('text-orange-700')
    })
  })

  describe('Status Styling', () => {
    it('applies correct styling for ok status', () => {
      render(<ModuleCard title="Test Module" module={mockModule} />)
      const badge = screen.getByText('Active')
      expect(badge).toHaveClass('bg-green-100')
      expect(badge).toHaveClass('text-green-800')
    })

    it('applies correct styling for degraded status', () => {
      const degradedModule = { ...mockModule, status: 'degraded' as const }
      render(<ModuleCard title="Test Module" module={degradedModule} />)
      const badge = screen.getByText('Degraded')
      expect(badge).toHaveClass('bg-yellow-100')
      expect(badge).toHaveClass('text-yellow-800')
    })

    it('applies correct styling for error status', () => {
      const errorModule = { ...mockModule, status: 'error' as const }
      render(<ModuleCard title="Test Module" module={errorModule} />)
      const badge = screen.getByText('Error')
      expect(badge).toHaveClass('bg-red-100')
      expect(badge).toHaveClass('text-red-800')
    })

    it('applies correct styling for skipped status', () => {
      const skippedModule = { ...mockModule, status: 'skipped' as const }
      render(<ModuleCard title="Test Module" module={skippedModule} />)
      const badge = screen.getByText('Skipped')
      expect(badge).toHaveClass('bg-gray-100')
      expect(badge).toHaveClass('text-gray-600')
    })
  })

  describe('Edge Cases', () => {
    it('handles single item correctly', () => {
      const singleItemModule = { ...mockModule, items: [mockModule.items[0]] }
      render(<ModuleCard title="Test Module" module={singleItemModule} />)
      expect(screen.getByText('▶ Show 1 items')).toBeInTheDocument()
    })

    it('handles empty summary string', () => {
      const moduleWithEmptySummary = { ...mockModule, summary: '' }
      render(<ModuleCard title="Test Module" module={moduleWithEmptySummary} />)
      expect(screen.queryByText('You have 5 new updates')).not.toBeInTheDocument()
    })

    it('handles long titles gracefully', () => {
      const longTitle = 'This is a very long module title that might wrap to multiple lines'
      render(<ModuleCard title={longTitle} module={mockModule} />)
      expect(screen.getByText(longTitle)).toBeInTheDocument()
    })

    it('renders correctly with minimum required props', () => {
      const minimalModule: ModuleResult = {
        status: 'ok',
        new_count: 0,
        updated_count: 0,
        summary: null,
        items: [],
      }
      render(<ModuleCard title="Minimal" module={minimalModule} />)
      expect(screen.getByText('Minimal')).toBeInTheDocument()
      expect(screen.getByText('No updates')).toBeInTheDocument()
    })
  })

  describe('Interaction', () => {
    it('maintains expansion state across re-renders', () => {
      const { rerender } = render(<ModuleCard title="Test Module" module={mockModule} />)
      
      // Expand
      fireEvent.click(screen.getByText('▶ Show 2 items'))
      expect(screen.getByText('Important Email')).toBeInTheDocument()
      
      // Re-render with same props
      rerender(<ModuleCard title="Test Module" module={mockModule} />)
      
      // Should still be expanded
      expect(screen.getByText('Important Email')).toBeInTheDocument()
    })

    it('button is keyboard accessible', () => {
      render(<ModuleCard title="Test Module" module={mockModule} />)
      const button = screen.getByText('▶ Show 2 items').closest('button')
      button?.focus()
      expect(document.activeElement).toBe(button)
    })
  })
})
