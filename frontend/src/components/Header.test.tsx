import { render, screen, fireEvent } from '@testing-library/react'
import Header from './Header'
import { BriefBundle } from '@/types/brief'

describe('Header Component', () => {
  const mockBrief: BriefBundle = {
    run_id: 'test-run-1',
    user_id: 'user-1',
    generated_at_utc: '2026-01-19T10:00:00Z',
    since_timestamp_utc: '2026-01-18T15:30:00Z',
    timezone: 'America/New_York',
    brief_date_local: '2026-01-19',
    top_highlights: [],
    modules: {},
    run_metadata: {},
  }

  const mockOnRefresh = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders the header with greeting', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} />)
      expect(screen.getByText('Good morning')).toBeInTheDocument()
    })

    it('displays the since timestamp correctly formatted', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} />)
      expect(screen.getByText(/Brief since January 18, 2026/)).toBeInTheDocument()
    })

    it('displays the timezone', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} />)
      expect(screen.getByText('America/New_York')).toBeInTheDocument()
    })

    it('displays the generated time', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} />)
      // Time is displayed in local timezone, so just check it exists with valid format
      // Use getAllByText since there might be multiple time displays
      const timeElements = screen.getAllByText(/\d{1,2}:\d{2}\s+(AM|PM)/i)
      expect(timeElements.length).toBeGreaterThan(0)
      expect(timeElements[0]).toBeInTheDocument()
    })

    it('renders the refresh button', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} />)
      expect(screen.getByText('Refresh')).toBeInTheDocument()
    })

    it('renders the settings button', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} />)
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })
  })

  describe('Refresh Button', () => {
    it('calls onRefresh when clicked', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} />)
      const refreshButton = screen.getByText('Refresh')
      fireEvent.click(refreshButton)
      expect(mockOnRefresh).toHaveBeenCalledTimes(1)
    })

    it('shows refreshing state when isRefreshing is true', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} isRefreshing={true} />)
      expect(screen.getByText('Refreshing...')).toBeInTheDocument()
      expect(screen.queryByText('Refresh')).not.toBeInTheDocument()
    })

    it('disables the button when refreshing', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} isRefreshing={true} />)
      const button = screen.getByText('Refreshing...').closest('button')
      expect(button).toBeDisabled()
    })

    it('does not call onRefresh when disabled', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} isRefreshing={true} />)
      const button = screen.getByText('Refreshing...').closest('button')
      fireEvent.click(button!)
      expect(mockOnRefresh).not.toHaveBeenCalled()
    })

    it('applies correct styling when refreshing', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} isRefreshing={true} />)
      const button = screen.getByText('Refreshing...').closest('button')
      expect(button).toHaveClass('bg-gray-400')
      expect(button).toHaveClass('cursor-not-allowed')
    })

    it('applies correct styling when not refreshing', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} isRefreshing={false} />)
      const button = screen.getByText('Refresh').closest('button')
      expect(button).toHaveClass('bg-blue-600')
      expect(button).not.toHaveClass('cursor-not-allowed')
    })

    it('shows spinner icon when refreshing', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} isRefreshing={true} />)
      const svg = screen.getByText('Refreshing...').closest('button')?.querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).toHaveClass('animate-spin')
    })
  })

  describe('Date Formatting', () => {
    it('formats different timezones correctly', () => {
      const briefWithDifferentTZ = { ...mockBrief, timezone: 'Europe/London' }
      render(<Header brief={briefWithDifferentTZ} onRefresh={mockOnRefresh} />)
      expect(screen.getByText('Europe/London')).toBeInTheDocument()
    })

    it('handles different date formats', () => {
      const briefWithDifferentDate = {
        ...mockBrief,
        since_timestamp_utc: '2026-12-31T23:59:59Z',
      }
      render(<Header brief={briefWithDifferentDate} onRefresh={mockOnRefresh} />)
      expect(screen.getByText(/Brief since December 31, 2026/)).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('refresh button is keyboard accessible', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} />)
      const button = screen.getByText('Refresh').closest('button')
      button?.focus()
      expect(document.activeElement).toBe(button)
    })

    it('maintains proper heading hierarchy', () => {
      render(<Header brief={mockBrief} onRefresh={mockOnRefresh} />)
      const heading = screen.getByText('Good morning')
      expect(heading.tagName).toBe('H1')
    })
  })
})
