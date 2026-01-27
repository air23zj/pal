import { weather } from '../utils/weather-api';
import { showLoading, showError, showSuccess } from '../utils/ui';
import { loadMainContent } from '../main.js';

export function loadWeatherInterface() {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <div class="max-w-7xl mx-auto px-4 py-6">
            <!-- Header -->
            <div class="flex justify-between items-center mb-8">
                <h2 class="text-2xl font-bold text-gray-900">Weather Dashboard</h2>
                <button id="backButton" class="text-gray-600 hover:text-gray-800">
                    <i class="fas fa-arrow-left mr-2"></i>Back
                </button>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <!-- Left Sidebar: Location Management -->
                <div class="lg:col-span-1">
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-lg font-semibold">My Locations</h3>
                            <button id="addLocationBtn" class="bg-primary-600 text-white px-3 py-1.5 rounded-md hover:bg-primary-700 text-sm">
                                <i class="fas fa-plus mr-1"></i>Add
                            </button>
                        </div>
                        <div id="locationsList" class="space-y-3">
                            <!-- Locations will be displayed here -->
                        </div>
                    </div>
                </div>

                <!-- Main Content Area -->
                <div class="lg:col-span-2">
                    <!-- Current Weather Card -->
                    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                        <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-6">
                            <div>
                                <h3 class="location-name text-2xl font-semibold mb-1">Select a location</h3>
                                <p class="current-date text-gray-600 text-sm"></p>
                            </div>
                            <div class="mt-4 md:mt-0 text-right">
                                <div class="current-temp text-4xl font-bold"></div>
                                <p class="weather-description text-gray-600 capitalize text-sm"></p>
                            </div>
                        </div>

                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <div class="bg-gray-50 rounded-lg p-3 text-center">
                                <p class="text-gray-600 text-sm">High</p>
                                <p class="high-temp text-xl font-semibold"></p>
                            </div>
                            <div class="bg-gray-50 rounded-lg p-3 text-center">
                                <p class="text-gray-600 text-sm">Low</p>
                                <p class="low-temp text-xl font-semibold"></p>
                            </div>
                            <div class="bg-gray-50 rounded-lg p-3 text-center">
                                <p class="text-gray-600 text-sm">Wind</p>
                                <p class="wind-speed text-xl font-semibold"></p>
                            </div>
                            <div class="bg-gray-50 rounded-lg p-3 text-center">
                                <p class="text-gray-600 text-sm">Rain</p>
                                <p class="precipitation text-xl font-semibold"></p>
                            </div>
                        </div>

                        <!-- Extra Weather Info -->
                        <div class="grid grid-cols-2 gap-4 mb-6">
                            <div class="bg-gray-50 rounded-lg p-3 text-center">
                                <p class="text-gray-600 text-sm">Feels Like</p>
                                <p class="feels-like text-xl font-semibold"></p>
                            </div>
                            <div class="bg-gray-50 rounded-lg p-3 text-center">
                                <p class="text-gray-600 text-sm">Humidity</p>
                                <p class="humidity text-xl font-semibold"></p>
                            </div>
                        </div>
                    </div>

                    <!-- Forecasts Tabs -->
                    <div class="bg-white rounded-lg shadow-md overflow-hidden">
                        <div class="border-b border-gray-200">
                            <nav class="flex" role="tablist">
                                <button class="flex-1 px-4 py-3 text-sm font-medium text-primary-600 border-b-2 border-primary-600" id="hourlyTab">
                                    Hourly Forecast
                                </button>
                                <button class="flex-1 px-4 py-3 text-sm font-medium text-gray-500 hover:text-gray-700" id="weeklyTab">
                                    7-Day Forecast
                                </button>
                            </nav>
                        </div>
                        
                        <!-- Hourly Forecast -->
                        <div id="hourlyForecast" class="p-4 overflow-x-auto">
                            <div class="inline-flex space-x-6 min-w-full">
                                <!-- Hourly forecast items will be displayed here -->
                            </div>
                        </div>

                        <!-- Weekly Forecast (hidden by default) -->
                        <div id="weeklyForecast" class="p-4 hidden">
                            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                                <!-- Weekly forecast items will be displayed here -->
                            </div>
                        </div>
                    </div>

                    <!-- Recommendations Section -->
                    <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <!-- Clothing Recommendations -->
                        <div class="bg-white rounded-lg shadow-md p-6">
                            <h4 class="font-medium text-primary-600 mb-4">Clothing Recommendations</h4>
                            <div id="clothingRecommendations" class="space-y-4">
                                <!-- Recommendations will be displayed here -->
                            </div>
                        </div>
                        
                        <!-- Temperature Settings -->
                        <div class="bg-white rounded-lg shadow-md p-6">
                            <h4 class="font-medium text-primary-600 mb-4">Home Temperature Settings</h4>
                            <div id="temperatureRecommendations" class="space-y-4">
                                <!-- Temperature recommendations will be displayed here -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Add Location Modal -->
        <div id="locationModal" class="fixed inset-0 bg-black bg-opacity-50 hidden flex items-center justify-center">
            <div class="bg-white rounded-lg p-6 w-full max-w-md">
                <h3 class="text-xl font-semibold mb-4">Add Location</h3>
                <form id="locationForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Location Name</label>
                        <input type="text" id="locationName" required 
                            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                            placeholder="Enter city name">
                    </div>
                    <div class="flex justify-end gap-4">
                        <button type="button" id="cancelLocationBtn" class="px-4 py-2 text-gray-600 hover:text-gray-800">
                            Cancel
                        </button>
                        <button type="submit" class="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700">
                            Add Location
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `;

    // Add back button functionality
    const backButton = document.getElementById('backButton');
    backButton.addEventListener('click', () => {
        history.pushState(null, '', '/');
        loadMainContent();
    });

    // Add location modal functionality
    const addLocationBtn = document.getElementById('addLocationBtn');
    const locationModal = document.getElementById('locationModal');
    const locationForm = document.getElementById('locationForm');
    const cancelLocationBtn = document.getElementById('cancelLocationBtn');

    addLocationBtn.addEventListener('click', () => {
        locationModal.classList.remove('hidden');
    });

    cancelLocationBtn.addEventListener('click', () => {
        locationModal.classList.add('hidden');
        locationForm.reset();
    });

    locationForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const locationName = document.getElementById('locationName').value;
        
        try {
            showLoading(true);
            await weather.addLocation({ name: locationName });
            locationModal.classList.add('hidden');
            locationForm.reset();
            await weatherInterface.loadLocations();
            showSuccess('Location added successfully');
        } catch (error) {
            console.error('Error adding location:', error);
            showError('Failed to add location');
        } finally {
            showLoading(false);
        }
    });

    const weatherInterface = {
        async loadLocations() {
            const locationsList = document.getElementById('locationsList');
            try {
                showLoading(true);
                locationsList.innerHTML = `
                    <div class="col-span-full flex justify-center items-center py-8">
                        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                        <span class="ml-2 text-gray-600">Loading locations...</span>
                    </div>
                `;
                
                const locations = await weather.getLocations();
                displayLocations(locations);
                if (locations.length > 0) {
                    await this.loadWeatherData(locations[0].id);
                } else {
                    locationsList.innerHTML = `
                        <div class="col-span-full text-center py-8">
                            <p class="text-gray-500">No locations added yet. Add your first location!</p>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading locations:', error);
                locationsList.innerHTML = `
                    <div class="col-span-full">
                        <div class="bg-red-50 border-l-4 border-red-500 p-4 rounded">
                            <div class="flex">
                                <div class="flex-shrink-0">
                                    <i class="fas fa-exclamation-circle text-red-400"></i>
                                </div>
                                <div class="ml-3">
                                    <p class="text-sm text-red-700">Failed to load locations. Please try again later.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } finally {
                showLoading(false);
            }
        },

        async loadWeatherData(locationId) {
            const weatherDisplay = document.querySelector('.bg-white.rounded-lg.shadow-md');
            try {
                weatherDisplay.classList.add('opacity-50');
                const loadingIndicator = document.createElement('div');
                loadingIndicator.className = 'absolute inset-0 flex items-center justify-center';
                loadingIndicator.innerHTML = `
                    <div class="flex items-center bg-white px-4 py-2 rounded-lg shadow-lg">
                        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
                        <span class="ml-2 text-gray-600">Loading weather data...</span>
                    </div>
                `;
                weatherDisplay.appendChild(loadingIndicator);

                const data = await weather.getWeatherData(locationId);
                displayCurrentWeather(data.current);
                displayHourlyForecast(data.hourly);
                displayWeeklyForecast(data.daily);
            } catch (error) {
                console.error('Error loading weather data:', error);
                weatherDisplay.innerHTML = `
                    <div class="p-6">
                        <div class="bg-red-50 border-l-4 border-red-500 p-4 rounded">
                            <div class="flex">
                                <div class="flex-shrink-0">
                                    <i class="fas fa-exclamation-circle text-red-400"></i>
                                </div>
                                <div class="ml-3">
                                    <p class="text-sm text-red-700">Failed to load weather data. Please try again later.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } finally {
                weatherDisplay.classList.remove('opacity-50');
                const loadingIndicator = weatherDisplay.querySelector('.absolute.inset-0');
                if (loadingIndicator) {
                    loadingIndicator.remove();
                }
            }
        },

        async removeLocation(locationId, event) {
            event.stopPropagation();
            try {
                showLoading(true);
                await weather.removeLocation(locationId);
                await this.loadLocations();
                showSuccess('Location removed successfully');
            } catch (error) {
                console.error('Error removing location:', error);
                showError('Failed to remove location');
            } finally {
                showLoading(false);
            }
        }
    };

    function displayLocations(locations) {
        const locationsList = document.getElementById('locationsList');
        locationsList.innerHTML = locations.map(location => `
            <div class="bg-gray-50 rounded-lg p-4 cursor-pointer hover:bg-gray-100 transition-colors duration-200" 
                 onclick="weatherInterface.loadWeatherData(${location.id})">
                <div class="flex justify-between items-center">
                    <h4 class="font-medium">${location.name}</h4>
                    <button class="text-red-600 hover:text-red-800 p-1" 
                            onclick="weatherInterface.removeLocation(${location.id}, event)"
                            title="Remove location">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                ${location.current_temp !== null ? 
                    `<p class="text-2xl font-semibold mt-2">${location.current_temp}°C</p>` :
                    `<p class="text-gray-500 text-sm mt-2">Temperature unavailable</p>`
                }
            </div>
        `).join('');
    }

    async function displayCurrentWeather(current) {
        document.querySelector('.location-name').textContent = current.location;
        document.querySelector('.current-date').textContent = new Date().toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        // Add weather icon
        const tempDisplay = document.querySelector('.current-temp');
        tempDisplay.innerHTML = `
            <div class="flex items-center justify-end">
                <img src="https://openweathermap.org/img/wn/${current.icon}@2x.png" 
                     alt="${current.description}"
                     class="w-16 h-16">
                <span>${current.temp}°C</span>
            </div>
        `;
        
        document.querySelector('.weather-description').textContent = current.description;
        document.querySelector('.high-temp').textContent = `${current.high}°C`;
        document.querySelector('.low-temp').textContent = `${current.low}°C`;
        document.querySelector('.wind-speed').textContent = `${current.wind_speed} m/s`;
        document.querySelector('.precipitation').textContent = `${current.precipitation}%`;
        document.querySelector('.feels-like').textContent = `${current.feels_like}°C`;
        document.querySelector('.humidity').textContent = `${current.humidity}%`;
        
        try {
            const recommendations = await weather.getWeatherRecommendations(current.id || current.locationId);
            
            // Update clothing recommendations
            const clothingSection = document.getElementById('clothingRecommendations');
            clothingSection.innerHTML = `
                <div class="space-y-3">
                    <div>
                        <h6 class="text-sm font-medium text-gray-600">What to Wear</h6>
                        <ul class="mt-1 list-disc list-inside text-sm">
                            ${recommendations.clothing.whatToWear.map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                    ${recommendations.clothing.specialItems.length > 0 ? `
                        <div>
                            <h6 class="text-sm font-medium text-gray-600">Special Items</h6>
                            <ul class="mt-1 list-disc list-inside text-sm">
                                ${recommendations.clothing.specialItems.map(item => `<li>${item}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    ${recommendations.clothing.tips.length > 0 ? `
                        <div>
                            <h6 class="text-sm font-medium text-gray-600">Tips</h6>
                            <ul class="mt-1 list-disc list-inside text-sm">
                                ${recommendations.clothing.tips.map(item => `<li>${item}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
            
            // Update temperature recommendations
            const tempSection = document.getElementById('temperatureRecommendations');
            tempSection.innerHTML = `
                <div class="space-y-3">
                    <div>
                        <h6 class="text-sm font-medium text-gray-600">Recommended Temperature</h6>
                        <p class="text-2xl font-bold mt-1">${recommendations.homeTemperature.recommendedTemp}°C</p>
                    </div>
                    ${recommendations.homeTemperature.energySavingTips.length > 0 ? `
                        <div>
                            <h6 class="text-sm font-medium text-gray-600">Energy Saving Tips</h6>
                            <ul class="mt-1 list-disc list-inside text-sm">
                                ${recommendations.homeTemperature.energySavingTips.map(tip => `<li>${tip}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    ${recommendations.homeTemperature.comfortTips.length > 0 ? `
                        <div>
                            <h6 class="text-sm font-medium text-gray-600">Comfort Tips</h6>
                            <ul class="mt-1 list-disc list-inside text-sm">
                                ${recommendations.homeTemperature.comfortTips.map(tip => `<li>${tip}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        } catch (error) {
            console.error('Error loading recommendations:', error);
            const sections = ['clothingRecommendations', 'temperatureRecommendations'];
            sections.forEach(id => {
                const section = document.getElementById(id);
                section.innerHTML = `
                    <div class="bg-red-50 border-l-4 border-red-500 p-4 rounded">
                        <div class="flex">
                            <div class="flex-shrink-0">
                                <i class="fas fa-exclamation-circle text-red-400"></i>
                            </div>
                            <div class="ml-3">
                                <p class="text-sm text-red-700">Failed to load recommendations</p>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
    }

    function displayHourlyForecast(hourly) {
        const hourlyContainer = document.querySelector('#hourlyForecast .inline-flex');
        hourlyContainer.innerHTML = hourly.map(hour => `
            <div class="flex-shrink-0 text-center p-2 ${hour.description === 'Forecast unavailable' ? 'opacity-50' : ''}">
                <div class="text-gray-600 text-sm">${new Date(hour.time).getHours()}:00</div>
                <img src="https://openweathermap.org/img/wn/${hour.icon}.png" 
                     alt="${hour.description}"
                     class="w-12 h-12 mx-auto my-1">
                <div class="text-lg font-medium">${hour.temp}°C</div>
                <div class="text-xs text-gray-600">${hour.precipitation}%</div>
                ${hour.description === 'Forecast unavailable' ? 
                    '<div class="text-xs text-yellow-600 mt-1"><i class="fas fa-exclamation-circle"></i></div>' : ''}
            </div>
        `).join('');
    }

    function displayWeeklyForecast(daily) {
        const weeklyContainer = document.querySelector('#weeklyForecast .grid');
        weeklyContainer.innerHTML = daily.map(day => `
            <div class="bg-gray-50 rounded-lg p-3 text-center ${day.description === 'Forecast unavailable' ? 'opacity-50' : ''}">
                <div class="font-medium text-sm">${new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}</div>
                <img src="https://openweathermap.org/img/wn/${day.icon}.png" 
                     alt="${day.description}"
                     class="w-12 h-12 mx-auto my-1">
                <div class="text-lg font-medium">${day.high}°C</div>
                <div class="text-sm text-gray-600">${day.low}°C</div>
                <div class="text-xs text-gray-600 mt-1">${day.precipitation}%</div>
                ${day.description === 'Forecast unavailable' ? 
                    '<div class="text-xs text-yellow-600 mt-1"><i class="fas fa-exclamation-circle"></i></div>' : ''}
            </div>
        `).join('');
    }

    // Add tab functionality
    const hourlyTab = document.getElementById('hourlyTab');
    const weeklyTab = document.getElementById('weeklyTab');
    const hourlyForecast = document.getElementById('hourlyForecast');
    const weeklyForecast = document.getElementById('weeklyForecast');

    hourlyTab.addEventListener('click', () => {
        hourlyTab.classList.add('text-primary-600', 'border-b-2', 'border-primary-600');
        weeklyTab.classList.remove('text-primary-600', 'border-b-2', 'border-primary-600');
        weeklyTab.classList.add('text-gray-500');
        hourlyForecast.classList.remove('hidden');
        weeklyForecast.classList.add('hidden');
    });

    weeklyTab.addEventListener('click', () => {
        weeklyTab.classList.add('text-primary-600', 'border-b-2', 'border-primary-600');
        hourlyTab.classList.remove('text-primary-600', 'border-b-2', 'border-primary-600');
        hourlyTab.classList.add('text-gray-500');
        weeklyForecast.classList.remove('hidden');
        hourlyForecast.classList.add('hidden');
    });

    // Make weatherInterface available globally
    window.weatherInterface = weatherInterface;

    // Load locations immediately
    weatherInterface.loadLocations();
} 