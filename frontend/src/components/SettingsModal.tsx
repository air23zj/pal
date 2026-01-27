'use client'

import { useState, useEffect } from 'react'
import { BriefBundle } from '@/types/brief'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (settings: UserSettings) => void
  currentSettings?: UserSettings
}

export interface UserSettings {
  topics: string[]
  vip_people: string[]
  projects: string[]
  enabled_modules: string[]
  upcoming_trips?: Array<{
    departure_airport: string
    arrival_airport: string
    departure_date: string
    return_date?: string
  }>
  favorite_restaurants?: Array<{
    name: string
    location: string
  }>
  travel_interests?: string[]
  upcoming_destinations?: Array<{
    name: string
    location: string
    type?: string
  }>
  local_interests?: string[]
  local_services_needed?: Array<{
    service_type: string
    location: string
  }>
  shopping_interests?: string[]
  products_to_track?: Array<{
    name: string
    category?: string
  }>
}

const AVAILABLE_MODULES = [
  { key: 'gmail', name: 'Gmail', description: 'Email inbox monitoring' },
  { key: 'calendar', name: 'Calendar', description: 'Upcoming events' },
  { key: 'tasks', name: 'Tasks', description: 'Pending tasks' },
  { key: 'keep', name: 'Keep', description: 'Notes and reminders from Google Keep' },
  { key: 'news', name: 'News', description: 'Latest news articles from Google News' },
  { key: 'research', name: 'Research', description: 'Web search for latest developments' },
  { key: 'flights', name: 'Flights', description: 'Flight information and travel planning' },
  { key: 'dining', name: 'Dining', description: 'Restaurant reviews and dining recommendations' },
  { key: 'travel', name: 'Travel', description: 'Hotels, attractions, and travel destinations' },
  { key: 'local', name: 'Local', description: 'Local business and service recommendations' },
  { key: 'shopping', name: 'Shopping', description: 'Product recommendations and shopping insights' },
  { key: 'twitter', name: 'Twitter/X', description: 'Social media monitoring' },
  { key: 'linkedin', name: 'LinkedIn', description: 'Professional network updates' },
]

export default function SettingsModal({ isOpen, onClose, onSave, currentSettings }: SettingsModalProps) {
  const [settings, setSettings] = useState<UserSettings>({
    topics: [],
    vip_people: [],
    projects: [],
    enabled_modules: ['gmail', 'calendar', 'tasks', 'news', 'research', 'flights', 'dining', 'travel', 'local', 'shopping'],
    upcoming_trips: [],
    favorite_restaurants: [],
    travel_interests: [],
    upcoming_destinations: [],
    local_interests: [],
    local_services_needed: [],
    shopping_interests: [],
    products_to_track: [],
  })

  const [newTopic, setNewTopic] = useState('')
  const [newVip, setNewVip] = useState('')
  const [newProject, setNewProject] = useState('')
  const [newTrip, setNewTrip] = useState({
    departure_airport: '',
    arrival_airport: '',
    departure_date: '',
    return_date: '',
  })
  const [newRestaurant, setNewRestaurant] = useState({
    name: '',
    location: 'New York',
  })
  const [newTravelInterest, setNewTravelInterest] = useState('')
  const [newDestination, setNewDestination] = useState({
    name: '',
    location: 'New York',
    type: 'ATTRACTION',
  })
  const [newLocalInterest, setNewLocalInterest] = useState('')
  const [newServiceNeeded, setNewServiceNeeded] = useState({
    service_type: '',
    location: 'New York',
  })
  const [newShoppingInterest, setNewShoppingInterest] = useState('')
  const [newProductToTrack, setNewProductToTrack] = useState({
    name: '',
    category: 'aps',
  })

  useEffect(() => {
    if (currentSettings) {
      setSettings(currentSettings)
    }
  }, [currentSettings])

  if (!isOpen) return null

  const addItem = (field: keyof Pick<UserSettings, 'topics' | 'vip_people' | 'projects'>, value: string) => {
    if (!value.trim()) return

    setSettings(prev => ({
      ...prev,
      [field]: [...prev[field], value.trim()]
    }))

    // Clear input
    if (field === 'topics') setNewTopic('')
    if (field === 'vip_people') setNewVip('')
    if (field === 'projects') setNewProject('')
  }

  const removeItem = (field: keyof Pick<UserSettings, 'topics' | 'vip_people' | 'projects'>, index: number) => {
    setSettings(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }))
  }

  const toggleModule = (moduleKey: string) => {
    setSettings(prev => ({
      ...prev,
      enabled_modules: prev.enabled_modules.includes(moduleKey)
        ? prev.enabled_modules.filter(m => m !== moduleKey)
        : [...prev.enabled_modules, moduleKey]
    }))
  }

  const handleSave = () => {
    onSave(settings)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>

          {/* Topics */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3">Topics of Interest</h3>
            <p className="text-sm text-gray-600 mb-3">
              Keywords that help rank items by relevance (e.g., "AI", "startups", "product management")
            </p>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newTopic}
                onChange={(e) => setNewTopic(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addItem('topics', newTopic)}
                placeholder="Add a topic..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => addItem('topics', newTopic)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {settings.topics.map((topic, index) => (
                <span
                  key={index}
                  className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center gap-2"
                >
                  {topic}
                  <button
                    onClick={() => removeItem('topics', index)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* VIP People */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3">VIP People</h3>
            <p className="text-sm text-gray-600 mb-3">
              Email addresses or names of important contacts whose messages should be prioritized
            </p>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newVip}
                onChange={(e) => setNewVip(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addItem('vip_people', newVip)}
                placeholder="Add VIP email or name..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => addItem('vip_people', newVip)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {settings.vip_people.map((vip, index) => (
                <span
                  key={index}
                  className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm flex items-center gap-2"
                >
                  {vip}
                  <button
                    onClick={() => removeItem('vip_people', index)}
                    className="text-green-600 hover:text-green-800"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

  {/* Projects */}
  <div className="mb-6">
    <h3 className="text-lg font-semibold mb-3">Active Projects</h3>
    <p className="text-sm text-gray-600 mb-3">
      Current projects to help contextualize information (e.g., "Q4 planning", "product launch")
    </p>
    <div className="flex gap-2 mb-3">
      <input
        type="text"
        value={newProject}
        onChange={(e) => setNewProject(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && addItem('projects', newProject)}
        placeholder="Add a project..."
        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        onClick={() => addItem('projects', newProject)}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        Add
      </button>
    </div>
    <div className="flex flex-wrap gap-2">
      {settings.projects.map((project, index) => (
        <span
          key={index}
          className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm flex items-center gap-2"
        >
          {project}
          <button
            onClick={() => removeItem('projects', index)}
            className="text-purple-600 hover:text-purple-800"
          >
            ×
          </button>
        </span>
      ))}
    </div>
  </div>

  {/* Upcoming Trips */}
  <div className="mb-6">
    <h3 className="text-lg font-semibold mb-3">Upcoming Trips</h3>
    <p className="text-sm text-gray-600 mb-3">
      Add your upcoming travel plans to get flight information and travel insights
    </p>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
      <input
        type="text"
        value={newTrip.departure_airport}
        onChange={(e) => setNewTrip(prev => ({ ...prev, departure_airport: e.target.value.toUpperCase() }))}
        placeholder="From (e.g., LAX)"
        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-center"
        maxLength={3}
      />
      <input
        type="text"
        value={newTrip.arrival_airport}
        onChange={(e) => setNewTrip(prev => ({ ...prev, arrival_airport: e.target.value.toUpperCase() }))}
        placeholder="To (e.g., AUS)"
        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-center"
        maxLength={3}
      />
      <input
        type="date"
        value={newTrip.departure_date}
        onChange={(e) => setNewTrip(prev => ({ ...prev, departure_date: e.target.value }))}
        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <input
        type="date"
        value={newTrip.return_date}
        onChange={(e) => setNewTrip(prev => ({ ...prev, return_date: e.target.value }))}
        placeholder="Return (optional)"
        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>
    <button
      onClick={() => {
        if (newTrip.departure_airport && newTrip.arrival_airport && newTrip.departure_date) {
          setSettings(prev => ({
            ...prev,
            upcoming_trips: [...(prev.upcoming_trips || []), { ...newTrip }]
          }))
          setNewTrip({
            departure_airport: '',
            arrival_airport: '',
            departure_date: '',
            return_date: '',
          })
        }
      }}
      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 mb-3"
    >
      Add Trip
    </button>
    <div className="space-y-2">
      {(settings.upcoming_trips || []).map((trip, index) => (
        <div
          key={index}
          className="bg-green-50 border border-green-200 rounded-lg p-3 flex justify-between items-center"
        >
          <div className="text-sm">
            <span className="font-medium">{trip.departure_airport} → {trip.arrival_airport}</span>
            <span className="text-gray-600 ml-2">
              {new Date(trip.departure_date).toLocaleDateString()}
              {trip.return_date && ` - ${new Date(trip.return_date).toLocaleDateString()}`}
            </span>
          </div>
          <button
            onClick={() => {
              setSettings(prev => ({
                ...prev,
                upcoming_trips: (prev.upcoming_trips || []).filter((_, i) => i !== index)
              }))
            }}
            className="text-red-600 hover:text-red-800 text-lg"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  </div>

  {/* Favorite Restaurants */}
  <div className="mb-6">
    <h3 className="text-lg font-semibold mb-3">Favorite Restaurants</h3>
    <p className="text-sm text-gray-600 mb-3">
      Add your favorite restaurants to get the latest reviews and dining insights
    </p>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
      <input
        type="text"
        value={newRestaurant.name}
        onChange={(e) => setNewRestaurant(prev => ({ ...prev, name: e.target.value }))}
        placeholder="Restaurant name (e.g., Le Bernardin)"
        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <input
        type="text"
        value={newRestaurant.location}
        onChange={(e) => setNewRestaurant(prev => ({ ...prev, location: e.target.value }))}
        placeholder="Location (e.g., New York)"
        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>
    <button
      onClick={() => {
        if (newRestaurant.name.trim()) {
          setSettings(prev => ({
            ...prev,
            favorite_restaurants: [...(prev.favorite_restaurants || []), { ...newRestaurant }]
          }))
          setNewRestaurant({
            name: '',
            location: 'New York',
          })
        }
      }}
      className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 mb-3"
    >
      Add Restaurant
    </button>
    <div className="space-y-2">
      {(settings.favorite_restaurants || []).map((restaurant, index) => (
        <div
          key={index}
          className="bg-orange-50 border border-orange-200 rounded-lg p-3 flex justify-between items-center"
        >
          <div className="text-sm">
            <span className="font-medium">{restaurant.name}</span>
            <span className="text-gray-600 ml-2">in {restaurant.location}</span>
          </div>
          <button
            onClick={() => {
              setSettings(prev => ({
                ...prev,
                favorite_restaurants: (prev.favorite_restaurants || []).filter((_, i) => i !== index)
              }))
            }}
            className="text-red-600 hover:text-red-800 text-lg"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  </div>

  {/* Travel Interests */}
  <div className="mb-6">
    <h3 className="text-lg font-semibold mb-3">Travel Interests</h3>
    <p className="text-sm text-gray-600 mb-3">
      Add topics you're interested in for travel recommendations (e.g., "luxury hotels", "family attractions", "fine dining")
    </p>
    <div className="flex gap-2 mb-3">
      <input
        type="text"
        value={newTravelInterest}
        onChange={(e) => setNewTravelInterest(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && addItem('travel_interests', newTravelInterest)}
        placeholder="Add a travel interest..."
        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        onClick={() => addItem('travel_interests', newTravelInterest)}
        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
      >
        Add
      </button>
    </div>
    <div className="flex flex-wrap gap-2">
      {(settings.travel_interests || []).map((interest, index) => (
        <span
          key={index}
          className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm flex items-center gap-2"
        >
          {interest}
          <button
            onClick={() => removeItem('travel_interests', index)}
            className="text-purple-600 hover:text-purple-800"
          >
            ×
          </button>
        </span>
      ))}
    </div>
  </div>

  {/* Upcoming Destinations */}
  <div className="mb-6">
    <h3 className="text-lg font-semibold mb-3">Upcoming Destinations</h3>
    <p className="text-sm text-gray-600 mb-3">
      Add specific destinations you're planning to visit for personalized recommendations
    </p>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
      <input
        type="text"
        value={newDestination.name}
        onChange={(e) => setNewDestination(prev => ({ ...prev, name: e.target.value }))}
        placeholder="Destination name"
        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <input
        type="text"
        value={newDestination.location}
        onChange={(e) => setNewDestination(prev => ({ ...prev, location: e.target.value }))}
        placeholder="Location"
        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <select
        value={newDestination.type}
        onChange={(e) => setNewDestination(prev => ({ ...prev, type: e.target.value }))}
        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="ATTRACTION">Attraction</option>
        <option value="ACCOMMODATION">Hotel</option>
        <option value="EATERY">Restaurant</option>
        <option value="GEO">Location</option>
        <option value="VACATION_RENTAL">Vacation Rental</option>
      </select>
    </div>
    <button
      onClick={() => {
        if (newDestination.name.trim()) {
          setSettings(prev => ({
            ...prev,
            upcoming_destinations: [...(prev.upcoming_destinations || []), { ...newDestination }]
          }))
          setNewDestination({
            name: '',
            location: 'New York',
            type: 'ATTRACTION',
          })
        }
      }}
      className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 mb-3"
    >
      Add Destination
    </button>
    <div className="space-y-2">
      {(settings.upcoming_destinations || []).map((destination, index) => (
        <div
          key={index}
          className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 flex justify-between items-center"
        >
          <div className="text-sm">
            <span className="font-medium">{destination.name}</span>
            <span className="text-gray-600 ml-2">in {destination.location}</span>
            <span className="text-xs bg-indigo-200 text-indigo-800 px-2 py-1 rounded ml-2">
              {destination.type}
            </span>
          </div>
          <button
            onClick={() => {
              setSettings(prev => ({
                ...prev,
                upcoming_destinations: (prev.upcoming_destinations || []).filter((_, i) => i !== index)
              }))
            }}
            className="text-red-600 hover:text-red-800 text-lg"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  </div>

  {/* Local Interests */}
  <div className="mb-6">
    <h3 className="text-lg font-semibold mb-3">Local Interests</h3>
    <p className="text-sm text-gray-600 mb-3">
      Add types of local businesses you're interested in discovering (e.g., "coffee shops", "bookstores", "grocery stores")
    </p>
    <div className="flex gap-2 mb-3">
      <input
        type="text"
        value={newLocalInterest}
        onChange={(e) => setNewLocalInterest(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && addItem('local_interests', newLocalInterest)}
        placeholder="Add a local interest..."
        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        onClick={() => addItem('local_interests', newLocalInterest)}
        className="px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700"
      >
        Add
      </button>
    </div>
    <div className="flex flex-wrap gap-2">
      {(settings.local_interests || []).map((interest, index) => (
        <span
          key={index}
          className="bg-teal-100 text-teal-800 px-3 py-1 rounded-full text-sm flex items-center gap-2"
        >
          {interest}
          <button
            onClick={() => removeItem('local_interests', index)}
            className="text-teal-600 hover:text-teal-800"
          >
            ×
          </button>
        </span>
      ))}
    </div>
  </div>

  {/* Local Services Needed */}
  <div className="mb-6">
    <h3 className="text-lg font-semibold mb-3">Local Services Needed</h3>
    <p className="text-sm text-gray-600 mb-3">
      Add specific services you need locally (e.g., "plumbers", "dentists", "auto repair")
    </p>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
      <input
        type="text"
        value={newServiceNeeded.service_type}
        onChange={(e) => setNewServiceNeeded(prev => ({ ...prev, service_type: e.target.value }))}
        placeholder="Service type (e.g., plumbers)"
        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <input
        type="text"
        value={newServiceNeeded.location}
        onChange={(e) => setNewServiceNeeded(prev => ({ ...prev, location: e.target.value }))}
        placeholder="Location"
        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>
    <button
      onClick={() => {
        if (newServiceNeeded.service_type.trim()) {
          setSettings(prev => ({
            ...prev,
            local_services_needed: [...(prev.local_services_needed || []), { ...newServiceNeeded }]
          }))
          setNewServiceNeeded({
            service_type: '',
            location: 'New York',
          })
        }
      }}
      className="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 mb-3"
    >
      Add Service
    </button>
    <div className="space-y-2">
      {(settings.local_services_needed || []).map((service, index) => (
        <div
          key={index}
          className="bg-cyan-50 border border-cyan-200 rounded-lg p-3 flex justify-between items-center"
        >
          <div className="text-sm">
            <span className="font-medium">{service.service_type}</span>
            <span className="text-gray-600 ml-2">in {service.location}</span>
          </div>
          <button
            onClick={() => {
              setSettings(prev => ({
                ...prev,
                local_services_needed: (prev.local_services_needed || []).filter((_, i) => i !== index)
              }))
            }}
            className="text-red-600 hover:text-red-800 text-lg"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  </div>

  {/* Shopping Interests */}
  <div className="mb-6">
    <h3 className="text-lg font-semibold mb-3">Shopping Interests</h3>
    <p className="text-sm text-gray-600 mb-3">
      Add product categories you're interested in shopping for (e.g., "wireless headphones", "coffee makers", "fitness gear")
    </p>
    <div className="flex gap-2 mb-3">
      <input
        type="text"
        value={newShoppingInterest}
        onChange={(e) => setNewShoppingInterest(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && addItem('shopping_interests', newShoppingInterest)}
        placeholder="Add a shopping interest..."
        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        onClick={() => addItem('shopping_interests', newShoppingInterest)}
        className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
      >
        Add
      </button>
    </div>
    <div className="flex flex-wrap gap-2">
      {(settings.shopping_interests || []).map((interest, index) => (
        <span
          key={index}
          className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm flex items-center gap-2"
        >
          {interest}
          <button
            onClick={() => removeItem('shopping_interests', index)}
            className="text-yellow-600 hover:text-yellow-800"
          >
            ×
          </button>
        </span>
      ))}
    </div>
  </div>

  {/* Products to Track */}
  <div className="mb-6">
    <h3 className="text-lg font-semibold mb-3">Products to Track</h3>
    <p className="text-sm text-gray-600 mb-3">
      Add specific products you want to track for price changes and availability
    </p>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
      <input
        type="text"
        value={newProductToTrack.name}
        onChange={(e) => setNewProductToTrack(prev => ({ ...prev, name: e.target.value }))}
        placeholder="Product name"
        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <select
        value={newProductToTrack.category}
        onChange={(e) => setNewProductToTrack(prev => ({ ...prev, category: e.target.value }))}
        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="aps">All Departments</option>
        <option value="electronics">Electronics</option>
        <option value="fashion">Fashion</option>
        <option value="home-garden">Home & Garden</option>
        <option value="sports">Sports & Outdoors</option>
        <option value="books">Books</option>
        <option value="toys">Toys & Games</option>
      </select>
    </div>
    <button
      onClick={() => {
        if (newProductToTrack.name.trim()) {
          setSettings(prev => ({
            ...prev,
            products_to_track: [...(prev.products_to_track || []), { ...newProductToTrack }]
          }))
          setNewProductToTrack({
            name: '',
            category: 'aps',
          })
        }
      }}
      className="px-4 py-2 bg-lime-600 text-white rounded-lg hover:bg-lime-700 mb-3"
    >
      Add Product
    </button>
    <div className="space-y-2">
      {(settings.products_to_track || []).map((product, index) => (
        <div
          key={index}
          className="bg-lime-50 border border-lime-200 rounded-lg p-3 flex justify-between items-center"
        >
          <div className="text-sm">
            <span className="font-medium">{product.name}</span>
            <span className="text-xs bg-lime-200 text-lime-800 px-2 py-1 rounded ml-2">
              {product.category}
            </span>
          </div>
          <button
            onClick={() => {
              setSettings(prev => ({
                ...prev,
                products_to_track: (prev.products_to_track || []).filter((_, i) => i !== index)
              }))
            }}
            className="text-red-600 hover:text-red-800 text-lg"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  </div>

          {/* Enabled Modules */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3">Enabled Modules</h3>
            <p className="text-sm text-gray-600 mb-3">
              Choose which data sources to include in your brief
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {AVAILABLE_MODULES.map((module) => (
                <label key={module.key} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                  <input
                    type="checkbox"
                    checked={settings.enabled_modules.includes(module.key)}
                    onChange={() => toggleModule(module.key)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div>
                    <div className="font-medium">{module.name}</div>
                    <div className="text-sm text-gray-500">{module.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}