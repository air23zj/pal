import { render, screen } from '@testing-library/react'
import Home from './page'
import * as api from '@/lib/api'

jest.mock('@/lib/api')
jest.mock('@/components/Dashboard', () => {
  return function MockDashboard({ brief }: any) {
    return <div data-testid="dashboard">Dashboard with brief: {brief.run_id}</div>
  }
})

describe('Home Page', () => {
  const mockBrief = {
    run_id: 'test-run-1',
    user_id: 'user-1',
    generated_at_utc: '2026-01-19T10:00:00Z',
    since_timestamp_utc: '2026-01-18T10:00:00Z',
    timezone: 'UTC',
    brief_date_local: '2026-01-19',
    top_highlights: [],
    modules: {},
    run_metadata: {},
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Successful Load', () => {
    it('fetches and displays the brief', async () => {
      ;(api.getLatestBrief as jest.Mock).mockResolvedValue(mockBrief)

      const HomePage = await Home()
      render(HomePage)

      expect(api.getLatestBrief).toHaveBeenCalledTimes(1)
      expect(screen.getByTestId('dashboard')).toBeInTheDocument()
      expect(screen.getByText(/Dashboard with brief: test-run-1/)).toBeInTheDocument()
    })

    it('renders main container with correct styling', async () => {
      ;(api.getLatestBrief as jest.Mock).mockResolvedValue(mockBrief)

      const HomePage = await Home()
      const { container } = render(HomePage)

      const main = container.querySelector('main')
      expect(main).toHaveClass('min-h-screen')
      expect(main).toHaveClass('bg-gray-50')
    })

    it('passes the brief to Dashboard component', async () => {
      ;(api.getLatestBrief as jest.Mock).mockResolvedValue(mockBrief)

      const HomePage = await Home()
      render(HomePage)

      expect(screen.getByText(/test-run-1/)).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('displays error message when fetch fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      const error = new Error('API Error')
      ;(api.getLatestBrief as jest.Mock).mockRejectedValue(error)

      const HomePage = await Home()
      render(HomePage)

      expect(consoleSpy).toHaveBeenCalledWith('Failed to fetch brief:', error)
      expect(screen.getByText('Failed to Load Brief')).toBeInTheDocument()
      expect(screen.getByText('Unable to connect to the backend server. Please ensure the API is running.')).toBeInTheDocument()

      consoleSpy.mockRestore()
    })

    it('shows backend URL in error message', async () => {
      jest.spyOn(console, 'error').mockImplementation()
      ;(api.getLatestBrief as jest.Mock).mockRejectedValue(new Error('API Error'))

      const HomePage = await Home()
      render(HomePage)

      expect(screen.getByText(/Backend URL: http:\/\/localhost:8000/)).toBeInTheDocument()
    })

    it('shows custom backend URL when env variable is set', async () => {
      const originalEnv = process.env.NEXT_PUBLIC_API_URL
      process.env.NEXT_PUBLIC_API_URL = 'https://api.example.com'

      jest.spyOn(console, 'error').mockImplementation()
      ;(api.getLatestBrief as jest.Mock).mockRejectedValue(new Error('API Error'))

      const HomePage = await Home()
      render(HomePage)

      expect(screen.getByText(/Backend URL: https:\/\/api\.example\.com/)).toBeInTheDocument()

      process.env.NEXT_PUBLIC_API_URL = originalEnv
    })

    it('renders error page with correct styling', async () => {
      jest.spyOn(console, 'error').mockImplementation()
      ;(api.getLatestBrief as jest.Mock).mockRejectedValue(new Error('API Error'))

      const HomePage = await Home()
      const { container } = render(HomePage)

      const main = container.querySelector('main')
      expect(main).toHaveClass('min-h-screen')
      expect(main).toHaveClass('bg-gray-50')
      expect(main).toHaveClass('flex')
      expect(main).toHaveClass('items-center')
      expect(main).toHaveClass('justify-center')
    })

    it('error heading has correct styling', async () => {
      jest.spyOn(console, 'error').mockImplementation()
      ;(api.getLatestBrief as jest.Mock).mockRejectedValue(new Error('API Error'))

      const HomePage = await Home()
      render(HomePage)

      const heading = screen.getByText('Failed to Load Brief')
      expect(heading.tagName).toBe('H1')
      expect(heading).toHaveClass('text-2xl')
      expect(heading).toHaveClass('font-bold')
      expect(heading).toHaveClass('text-red-600')
    })
  })

  describe('Different Error Scenarios', () => {
    it('handles network error', async () => {
      jest.spyOn(console, 'error').mockImplementation()
      ;(api.getLatestBrief as jest.Mock).mockRejectedValue(new Error('Network Error'))

      const HomePage = await Home()
      render(HomePage)

      expect(screen.getByText('Failed to Load Brief')).toBeInTheDocument()
    })

    it('handles timeout error', async () => {
      jest.spyOn(console, 'error').mockImplementation()
      ;(api.getLatestBrief as jest.Mock).mockRejectedValue(new Error('Timeout'))

      const HomePage = await Home()
      render(HomePage)

      expect(screen.getByText('Failed to Load Brief')).toBeInTheDocument()
    })

    it('handles generic error', async () => {
      jest.spyOn(console, 'error').mockImplementation()
      ;(api.getLatestBrief as jest.Mock).mockRejectedValue(new Error('Unknown error'))

      const HomePage = await Home()
      render(HomePage)

      expect(screen.getByText('Failed to Load Brief')).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles brief with minimal data', async () => {
      const minimalBrief = {
        run_id: 'minimal',
        user_id: 'user-1',
        generated_at_utc: '2026-01-19T10:00:00Z',
        since_timestamp_utc: '2026-01-18T10:00:00Z',
        timezone: 'UTC',
        brief_date_local: '2026-01-19',
        top_highlights: [],
        modules: {},
        run_metadata: {},
      }
      ;(api.getLatestBrief as jest.Mock).mockResolvedValue(minimalBrief)

      const HomePage = await Home()
      render(HomePage)

      expect(screen.getByTestId('dashboard')).toBeInTheDocument()
    })

    it('handles brief with complex data', async () => {
      const complexBrief = {
        ...mockBrief,
        run_id: 'complex',
        top_highlights: Array(10).fill(null).map((_, i) => ({
          item_ref: `item-${i}`,
          source: 'gmail',
          type: 'email',
          timestamp_utc: '2026-01-19T10:00:00Z',
          title: `Item ${i}`,
          summary: 'Summary',
          why_it_matters: 'Matters',
          entities: [],
          novelty: {
            label: 'NEW' as const,
            first_seen_utc: '2026-01-19T10:00:00Z',
            last_updated_utc: '2026-01-19T10:00:00Z',
            seen_count: 0,
          },
          ranking: {
            relevance: 0.5,
            urgency: 0.5,
            credibility: 0.5,
            actionability: 0.5,
            impact_score: 0.5,
            final_score: 0.5,
          },
          evidence: [],
          suggested_actions: [],
          source_id: `source-${i}`,
          url: null,
        })),
        modules: {
          gmail: {
            status: 'ok' as const,
            new_count: 100,
            updated_count: 50,
            summary: 'Many emails',
            items: [],
          },
        },
      }
      ;(api.getLatestBrief as jest.Mock).mockResolvedValue(complexBrief)

      const HomePage = await Home()
      render(HomePage)

      expect(screen.getByText(/complex/)).toBeInTheDocument()
    })
  })
})
