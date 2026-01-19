import { getLatestBrief } from '@/lib/api'
import Dashboard from '@/components/Dashboard'

export default async function Home() {
  try {
    const brief = await getLatestBrief()

    return (
      <main className="min-h-screen bg-gray-50">
        <Dashboard brief={brief} />
      </main>
    )
  } catch (error) {
    console.error('Failed to fetch brief:', error)

    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center p-8 bg-white rounded-lg shadow-md">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Failed to Load Brief</h1>
          <p className="text-gray-600 mb-4">
            Unable to connect to the backend server. Please ensure the API is running.
          </p>
          <p className="text-sm text-gray-500">
            Backend URL: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
          </p>
        </div>
      </main>
    )
  }
}
