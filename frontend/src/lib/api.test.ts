import { getLatestBrief, triggerBriefRun, recordFeedback, markItemSeen } from './api'

describe('API Client', () => {
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
    global.fetch = jest.fn()
  })

  afterEach(() => {
    jest.resetAllMocks()
  })

  describe('getLatestBrief', () => {
    it('fetches the latest brief successfully', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBrief,
      })

      const result = await getLatestBrief()

      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/brief/latest', {
        cache: 'no-store',
      })
      expect(result).toEqual(mockBrief)
    })

    it('throws an error when the fetch fails', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
      })

      await expect(getLatestBrief()).rejects.toThrow('Failed to fetch latest brief')
    })

    it('uses custom API base URL when env variable is set', async () => {
      const originalEnv = process.env.NEXT_PUBLIC_API_URL
      process.env.NEXT_PUBLIC_API_URL = 'https://api.example.com'

      // Reimport to get new env
      jest.resetModules()
      const { getLatestBrief: getLatestBriefWithEnv } = require('./api')

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBrief,
      })

      await getLatestBriefWithEnv()

      expect(global.fetch).toHaveBeenCalledWith('https://api.example.com/api/brief/latest', {
        cache: 'no-store',
      })

      process.env.NEXT_PUBLIC_API_URL = originalEnv
    })
  })

  describe('triggerBriefRun', () => {
    it('triggers a brief run successfully', async () => {
      const mockResponse = { run_id: 'run-123', status: 'queued' }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await triggerBriefRun()

      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/brief/run', {
        method: 'POST',
      })
      expect(result).toEqual(mockResponse)
    })

    it('throws an error when the fetch fails', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
      })

      await expect(triggerBriefRun()).rejects.toThrow('Failed to trigger brief run')
    })
  })

  describe('recordFeedback', () => {
    it('records feedback successfully', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
      })

      await recordFeedback('item-1', 'clicked', { button: 'primary' })

      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          item_ref: 'item-1',
          event_type: 'clicked',
          payload: { button: 'primary' },
        }),
      })
    })

    it('records feedback without payload', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
      })

      await recordFeedback('item-1', 'viewed')

      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          item_ref: 'item-1',
          event_type: 'viewed',
          payload: undefined,
        }),
      })
    })

    it('throws an error when the fetch fails', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
      })

      await expect(recordFeedback('item-1', 'clicked')).rejects.toThrow('Failed to record feedback')
    })
  })

  describe('markItemSeen', () => {
    it('marks an item as seen successfully', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
      })

      await markItemSeen('item-1')

      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/item/mark_seen', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          item_ref: 'item-1',
        }),
      })
    })

    it('throws an error when the fetch fails', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
      })

      await expect(markItemSeen('item-1')).rejects.toThrow('Failed to mark item as seen')
    })
  })
})
