import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Dashboard from './Dashboard'
import { BriefBundle } from '@/types/brief'
import * as api from '@/lib/api'

jest.mock('@/lib/api')

describe('Dashboard Component', () => {
  const mockBrief: BriefBundle = {
    brief_id: 'brief_123',
    user_id: 'user-1',
    generated_at_utc: '2026-01-19T10:00:00Z',
    since_timestamp_utc: '2026-01-18T10:00:00Z',
    timezone: 'UTC',
    brief_date_local: '2026-01-19',
    top_highlights: [
      {
        item_ref: 'highlight-1',
        source: 'gmail',
        type: 'email',
        timestamp_utc: '2026-01-19T09:00:00Z',
        title: 'Important Email',
        summary: 'This is a very important email',
        why_it_matters: 'Requires immediate action',
        entities: [],
        novelty: {
          label: 'NEW',
          reason: 'High priority match',
          first_seen_utc: '2026-01-19T09:00:00Z',
          seen_count: 1,
        },
        ranking: {
          relevance_score: 0.95,
          urgency_score: 0.9,
          credibility_score: 0.95,
          impact_score: 0.95,
          actionability_score: 0.9,
          final_score: 0.93,
        },
        evidence: [],
        suggested_actions: [],
        source_id: 'email-1',
        url: null,
      },
    ],
    modules: {
      gmail: {
        status: 'ok',
        new_count: 3,
        updated_count: 1,
        summary: 'You have 4 new emails',
        items: [],
      },
      calendar: {
        status: 'ok',
        new_count: 2,
        updated_count: 0,
        summary: 'You have 2 upcoming events',
        items: [],
      },
      tasks: {
        status: 'skipped',
        new_count: 0,
        updated_count: 0,
        summary: 'Skipped',
        items: [],
      },
    },
    run_metadata: {
      status: 'ok',
      latency_ms: 1234,
      cost_estimate_usd: 0.0,
      agents_used: ['gmail', 'calendar'],
      warnings: [],
    },
    actions: [],
    evidence_log: [],
  }

  beforeEach(() => {
    jest.clearAllMocks()
      ; (api.getLatestBrief as jest.Mock).mockResolvedValue(mockBrief)
      ; (api.triggerBriefRun as jest.Mock).mockResolvedValue({ run_id: 'new-run', status: 'queued' })
      ; (api.getRunStatus as jest.Mock).mockResolvedValue({ status: 'ok' })
  })

  describe('Initial Rendering', () => {
    it('renders the Dashboard with brief data', () => {
      render(<Dashboard brief={mockBrief} />)
      expect(screen.getByText('Good morning')).toBeInTheDocument()
    })

    it('displays top highlights section', () => {
      render(<Dashboard brief={mockBrief} />)
      expect(screen.getByText('Top Highlights')).toBeInTheDocument()
      expect(screen.getByText('Important Email')).toBeInTheDocument()
    })

    it('displays module cards', () => {
      render(<Dashboard brief={mockBrief} />)
      expect(screen.getByText(/📧 Inbox/)).toBeInTheDocument()
      expect(screen.getByText(/📅 Calendar/)).toBeInTheDocument()
    })

    it('filters out skipped modules with no items', () => {
      render(<Dashboard brief={mockBrief} />)
      expect(screen.queryByText(/Tasks/)).not.toBeInTheDocument()
    })

    it('displays metadata with latency', () => {
      render(<Dashboard brief={mockBrief} />)
      expect(screen.getByText(/1234ms/)).toBeInTheDocument()
    })

    it('displays generated timestamp', () => {
      render(<Dashboard brief={mockBrief} />)
      expect(screen.getByText(/Generated:/)).toBeInTheDocument()
    })
  })

  describe('Top Highlights', () => {
    it('renders all top highlights', () => {
      const briefWithMultipleHighlights = {
        ...mockBrief,
        top_highlights: [
          ...mockBrief.top_highlights,
          {
            ...mockBrief.top_highlights[0],
            item_ref: 'highlight-2',
            title: 'Second Important Item',
          },
        ],
      }
      render(<Dashboard brief={briefWithMultipleHighlights} />)
      expect(screen.getByText('Important Email')).toBeInTheDocument()
      expect(screen.getByText('Second Important Item')).toBeInTheDocument()
    })

    it('does not render top highlights section when empty', () => {
      const briefWithoutHighlights = { ...mockBrief, top_highlights: [] }
      render(<Dashboard brief={briefWithoutHighlights} />)
      expect(screen.queryByText('Top Highlights')).not.toBeInTheDocument()
    })

    it('displays highlight summary and why_it_matters', () => {
      render(<Dashboard brief={mockBrief} />)
      expect(screen.getByText('This is a very important email')).toBeInTheDocument()
      expect(screen.getByText('Requires immediate action')).toBeInTheDocument()
    })
  })

  describe('Module Display', () => {
    it('displays module with emoji and title', () => {
      render(<Dashboard brief={mockBrief} />)
      expect(screen.getByText(/📧 Inbox/)).toBeInTheDocument()
    })

    it('handles unknown module type with default icon', () => {
      const briefWithUnknownModule = {
        ...mockBrief,
        modules: {
          ...mockBrief.modules,
          unknown: {
            status: 'ok' as const,
            new_count: 1,
            updated_count: 0,
            summary: 'Unknown module',
            items: [],
          },
        },
      }
      render(<Dashboard brief={briefWithUnknownModule} />)
      expect(screen.getByText(/📦 Unknown/)).toBeInTheDocument()
    })

    it('displays message when no modules available', () => {
      const briefWithNoModules = { ...mockBrief, modules: {} }
      render(<Dashboard brief={briefWithNoModules} />)
      expect(screen.getByText('No modules available yet.')).toBeInTheDocument()
      expect(screen.getByText('Configure your data sources to get started.')).toBeInTheDocument()
    })

    it('includes skipped modules if they have items', () => {
      const briefWithSkippedModuleWithItems = {
        ...mockBrief,
        modules: {
          ...mockBrief.modules,
          tasks: {
            status: 'skipped' as const,
            new_count: 1,
            updated_count: 0,
            summary: 'Has items',
            items: [
              {
                item_ref: 'task-1',
                source: 'tasks',
                type: 'task',
                timestamp_utc: '2026-01-19T10:00:00Z',
                title: 'Task',
                summary: 'Summary',
                why_it_matters: 'Matters',
                entities: [],
                novelty: {
                  label: 'NEW' as const,
                  reason: 'Initial scan',
                  first_seen_utc: '2026-01-19T10:00:00Z',
                  seen_count: 1,
                },
                ranking: {
                  relevance_score: 0.5,
                  urgency_score: 0.5,
                  credibility_score: 0.5,
                  impact_score: 0.5,
                  actionability_score: 0.5,
                  final_score: 0.5,
                },
                evidence: [],
                suggested_actions: [],
                url: null,
              },
            ],
          },
        },
      }
      render(<Dashboard brief={briefWithSkippedModuleWithItems} />)
      expect(screen.getByText(/✅ Tasks/)).toBeInTheDocument()
    })
  })

  describe('Refresh Functionality', () => {
    it('calls triggerBriefRun and getLatestBrief when refresh is clicked', async () => {
      ; (api.triggerBriefRun as jest.Mock).mockResolvedValue({ run_id: 'new-run', status: 'queued' })
        ; (api.getLatestBrief as jest.Mock).mockResolvedValue(mockBrief)

      render(<Dashboard brief={mockBrief} />)

      const refreshButton = screen.getByText('Refresh')
      fireEvent.click(refreshButton)

      await waitFor(() => {
        expect(api.triggerBriefRun).toHaveBeenCalled()
      }, { timeout: 5000 })

      await waitFor(() => {
        expect(api.getLatestBrief).toHaveBeenCalled()
      }, { timeout: 5000 })
    })

    it('shows refreshing state during refresh', async () => {
      // Make the API calls take longer to keep refreshing state visible
      ; (api.triggerBriefRun as jest.Mock).mockImplementation(() =>
        new Promise(resolve => setTimeout(() => resolve({ run_id: 'new-run', status: 'queued' }), 100))
      )
        ; (api.getLatestBrief as jest.Mock).mockResolvedValue(mockBrief)

      render(<Dashboard brief={mockBrief} />)

      const refreshButton = screen.getByText('Refresh')
      fireEvent.click(refreshButton)

      // Should show refreshing state immediately
      await waitFor(() => {
        expect(screen.getByText('Refreshing...')).toBeInTheDocument()
      })
      expect(screen.getByText('Refreshing your brief...')).toBeInTheDocument()

      // Wait for refresh to complete
      await waitFor(() => {
        expect(screen.queryByText('Refreshing...')).not.toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('displays error message when refresh fails', async () => {
      ; (api.triggerBriefRun as jest.Mock).mockRejectedValue(new Error('API Error'))
        ; (api.getLatestBrief as jest.Mock).mockResolvedValue(mockBrief)

      render(<Dashboard brief={mockBrief} />)

      const refreshButton = screen.getByText('Refresh')
      fireEvent.click(refreshButton)

      await waitFor(() => {
        expect(screen.getByText('Failed to refresh brief. Please try again.')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('hides error message on subsequent successful refresh', async () => {
      ; (api.triggerBriefRun as jest.Mock).mockRejectedValueOnce(new Error('API Error'))
        .mockResolvedValueOnce({ run_id: 'new-run', status: 'queued' })

      render(<Dashboard brief={mockBrief} />)

      // First refresh - fails
      const refreshButton = screen.getByText('Refresh')
      fireEvent.click(refreshButton)

      await waitFor(() => {
        expect(screen.getByText('Failed to refresh brief. Please try again.')).toBeInTheDocument()
      })

      // Second refresh - succeeds
      const refreshButton2 = screen.getByText('Refresh')
      fireEvent.click(refreshButton2)

      await waitFor(() => {
        expect(screen.queryByText('Failed to refresh brief. Please try again.')).not.toBeInTheDocument()
      })
    })

    it('logs error to console when refresh fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      const error = new Error('API Error')
        ; (api.triggerBriefRun as jest.Mock).mockRejectedValue(error)

      render(<Dashboard brief={mockBrief} />)

      const refreshButton = screen.getByText('Refresh')
      fireEvent.click(refreshButton)

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to refresh brief:', error)
      })

      consoleSpy.mockRestore()
    })
  })

  describe('Warnings Display', () => {
    it('displays warnings from run_metadata', () => {
      const briefWithWarnings = {
        ...mockBrief,
        run_metadata: {
          status: 'ok',
          latency_ms: 1234,
          cost_estimate_usd: 0.0,
          agents_used: [],
          warnings: ['Warning 1', 'Warning 2'],
        },
      }
      render(<Dashboard brief={briefWithWarnings} />)
      expect(screen.getByText('Warning 1, Warning 2')).toBeInTheDocument()
    })

    it('does not display warnings section when warnings array is empty', () => {
      render(<Dashboard brief={mockBrief} />)
      // Should not have any yellow/warning text
      const metadataSection = screen.getByText(/Latency: 1234ms/).closest('div')
      expect(metadataSection?.textContent).not.toContain('Warning')
    })

    it('handles missing run_metadata gracefully', () => {
      const briefWithoutMetadata = { ...mockBrief, run_metadata: undefined }
      render(<Dashboard brief={briefWithoutMetadata} />)
      expect(screen.getByText(/Latency: N\/A/)).toBeInTheDocument()
    })
  })

  describe('Module Icons', () => {
    it('displays correct icon for gmail', () => {
      render(<Dashboard brief={mockBrief} />)
      expect(screen.getByText(/📧/)).toBeInTheDocument()
    })

    it('displays correct icon for calendar', () => {
      render(<Dashboard brief={mockBrief} />)
      expect(screen.getByText(/📅/)).toBeInTheDocument()
    })

    it('displays correct icon for twitter/x', () => {
      const briefWithTwitter = {
        ...mockBrief,
        modules: {
          ...mockBrief.modules,
          twitter: {
            status: 'ok' as const,
            new_count: 1,
            updated_count: 0,
            summary: 'Twitter',
            items: [],
          },
        },
      }
      render(<Dashboard brief={briefWithTwitter} />)
      expect(screen.getByText(/🐦/)).toBeInTheDocument()
    })

    it('displays correct icon for linkedin', () => {
      const briefWithLinkedIn = {
        ...mockBrief,
        modules: {
          ...mockBrief.modules,
          linkedin: {
            status: 'ok' as const,
            new_count: 1,
            updated_count: 0,
            summary: 'LinkedIn',
            items: [],
          },
        },
      }
      render(<Dashboard brief={briefWithLinkedIn} />)
      expect(screen.getByText(/💼/)).toBeInTheDocument()
    })

    const iconTests = [
      { key: 'news', icon: '📰' },
      { key: 'arxiv', icon: '📄' },
      { key: 'research', icon: '🔬' },
      { key: 'podcasts', icon: '🎙️' },
      { key: 'weather', icon: '☀️' },
      { key: 'commute', icon: '🚗' },
    ]

    iconTests.forEach(({ key, icon }) => {
      it(`displays correct icon for ${key}`, () => {
        const briefWithModule = {
          ...mockBrief,
          modules: {
            [key]: {
              status: 'ok' as const,
              new_count: 1,
              updated_count: 0,
              summary: 'Test',
              items: [],
            },
          },
        }
        render(<Dashboard brief={briefWithModule} />)
        expect(screen.getByText(new RegExp(icon))).toBeInTheDocument()
      })
    })
  })

  describe('Layout and Styling', () => {
    it('applies grid layout to modules', () => {
      const { container } = render(<Dashboard brief={mockBrief} />)
      const grid = container.querySelector('.grid')
      expect(grid).toBeInTheDocument()
      expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3')
    })

    it('applies max-width container', () => {
      const { container } = render(<Dashboard brief={mockBrief} />)
      const mainContainer = container.querySelector('.max-w-7xl')
      expect(mainContainer).toBeInTheDocument()
    })

    it('renders error message with correct styling', async () => {
      ; (api.triggerBriefRun as jest.Mock).mockRejectedValue(new Error('API Error'))

      render(<Dashboard brief={mockBrief} />)

      const refreshButton = screen.getByText('Refresh')
      fireEvent.click(refreshButton)

      await waitFor(() => {
        const errorDiv = screen.getByText('Failed to refresh brief. Please try again.').closest('div')
        expect(errorDiv).toHaveClass('bg-red-100')
      })
    })
  })

  describe('Edge Cases', () => {
    it('handles brief with no top highlights and no modules', () => {
      const emptyBrief = {
        ...mockBrief,
        top_highlights: [],
        modules: {},
      }
      render(<Dashboard brief={emptyBrief} />)
      expect(screen.getByText('No modules available yet.')).toBeInTheDocument()
    })

    it('handles very long module names', () => {
      const briefWithLongModuleName = {
        ...mockBrief,
        modules: {
          verylongmodulenamethatmightwrap: {
            status: 'ok' as const,
            new_count: 1,
            updated_count: 0,
            summary: 'Long module',
            items: [],
          },
        },
      }
      render(<Dashboard brief={briefWithLongModuleName} />)
      expect(screen.getByText(/Verylongmodulenamethatmightwrap/)).toBeInTheDocument()
    })

    it('handles null latency in metadata', () => {
      const briefWithNullLatency = {
        ...mockBrief,
        run_metadata: {
          status: 'ok',
          latency_ms: null as any,
          cost_estimate_usd: 0.0,
          agents_used: [],
          warnings: [],
        },
      }
      render(<Dashboard brief={briefWithNullLatency} />)
      expect(screen.getByText(/Latency: N\/A/)).toBeInTheDocument()
    })
  })
})
