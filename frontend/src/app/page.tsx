import { getLatestBrief } from '@/lib/api'
import Dashboard from '@/components/Dashboard'

export default async function Home() {
  try {
    const brief = await getLatestBrief()

    return (
      <main className="min-h-screen bg-neutral-50">
        <Dashboard brief={brief} />
      </main>
    )
  } catch (error) {
    console.error('Failed to fetch brief:', error)

    return (
      <main className="min-h-screen bg-neutral-50 flex items-center justify-center p-4">
        <div className="text-center p-8 surface rounded-xl max-w-md w-full animate-fade-in">
          <div className="w-16 h-16 mx-auto mb-6 bg-error-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-error-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h1 className="text-2xl font-semibold text-neutral-900 mb-3">Connection Error</h1>
          <p className="text-neutral-600 mb-6 leading-relaxed">
            Unable to connect to the backend server. Please ensure the API is running and try again.
          </p>
          <div className="text-sm text-neutral-500 bg-neutral-50 px-4 py-3 rounded-lg font-mono">
            Backend URL: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
          </div>
        </div>
      </main>
    )
  }
}
