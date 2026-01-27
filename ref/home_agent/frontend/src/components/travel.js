import { travel } from '../utils/travel-api';
import { showLoading, showError, showSuccess, formatDate } from '../utils/ui';
import { loadMainContent } from '../main.js';

export function loadTravelInterface() {
    const mainContent = document.getElementById('mainContent');
    if (!mainContent) return;

    mainContent.innerHTML = `
        <div class="max-w-6xl mx-auto px-4 py-6">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-2xl font-bold text-gray-900">Travel Planning</h2>
                <button id="backButton" class="text-gray-600 hover:text-gray-800">
                    <i class="fas fa-arrow-left mr-2"></i>Back to Home
                </button>
            </div>
            
            <!-- Trip List and Create Trip Button -->
            <div class="mb-8">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold">My Trips</h3>
                    <button id="createTripBtn" class="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700">
                        <i class="fas fa-plus mr-2"></i>Create New Trip
                    </button>
                </div>
                <div id="tripsList" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <!-- Trips will be displayed here -->
                </div>
            </div>
        </div>

        <!-- Create Trip Modal -->
        <div id="tripModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div class="bg-white rounded-lg p-6 w-full max-w-md">
                <h3 class="text-xl font-semibold mb-4">Create New Trip</h3>
                <form id="tripForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Trip Title</label>
                        <input type="text" id="tripTitle" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Destination</label>
                        <input type="text" id="tripDestination" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Start Date</label>
                        <input type="date" id="tripStartDate" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">End Date</label>
                        <input type="date" id="tripEndDate" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Notes</label>
                        <textarea id="tripNotes" rows="3" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"></textarea>
                    </div>
                    <div class="flex justify-end gap-4">
                        <button type="button" id="cancelTripBtn" class="px-4 py-2 text-gray-600 hover:text-gray-800">
                            Cancel
                        </button>
                        <button type="submit" class="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700">
                            Create Trip
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Accommodation Modal -->
        <div id="accommodationModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div class="bg-white rounded-lg p-6 w-full max-w-md">
                <h3 class="text-xl font-semibold mb-4">Add Accommodation</h3>
                <form id="accommodationForm" class="space-y-4">
                    <input type="hidden" id="accommodationTripId">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Type</label>
                        <select id="accommodationType" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                            <option value="hotel">Hotel</option>
                            <option value="airbnb">Airbnb</option>
                            <option value="hostel">Hostel</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Name</label>
                        <input type="text" id="accommodationName" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Location</label>
                        <input type="text" id="accommodationLocation" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Check-in Date</label>
                        <input type="datetime-local" id="accommodationCheckIn" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Check-out Date</label>
                        <input type="datetime-local" id="accommodationCheckOut" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Price</label>
                        <input type="number" id="accommodationPrice" required step="0.01" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Booking Reference</label>
                        <input type="text" id="accommodationReference" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Notes</label>
                        <textarea id="accommodationNotes" rows="3" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"></textarea>
                    </div>
                    <div class="flex justify-end gap-4">
                        <button type="button" id="cancelAccommodationBtn" class="px-4 py-2 text-gray-600 hover:text-gray-800">Cancel</button>
                        <button type="submit" class="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700">Add Accommodation</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Flight Modal -->
        <div id="flightModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div class="bg-white rounded-lg p-6 w-full max-w-md">
                <h3 class="text-xl font-semibold mb-4">Add Flight</h3>
                <form id="flightForm" class="space-y-4">
                    <input type="hidden" id="flightTripId">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Airline</label>
                        <input type="text" id="flightAirline" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Flight Number</label>
                        <input type="text" id="flightNumber" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Departure Airport</label>
                        <input type="text" id="flightDepartureAirport" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Arrival Airport</label>
                        <input type="text" id="flightArrivalAirport" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Departure Time</label>
                        <input type="datetime-local" id="flightDepartureTime" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Arrival Time</label>
                        <input type="datetime-local" id="flightArrivalTime" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Price</label>
                        <input type="number" id="flightPrice" required step="0.01" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Booking Reference</label>
                        <input type="text" id="flightReference" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Notes</label>
                        <textarea id="flightNotes" rows="3" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"></textarea>
                    </div>
                    <div class="flex justify-end gap-4">
                        <button type="button" id="cancelFlightBtn" class="px-4 py-2 text-gray-600 hover:text-gray-800">Cancel</button>
                        <button type="submit" class="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700">Add Flight</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Car Rental Modal -->
        <div id="carRentalModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div class="bg-white rounded-lg p-6 w-full max-w-md">
                <h3 class="text-xl font-semibold mb-4">Add Car Rental</h3>
                <form id="carRentalForm" class="space-y-4">
                    <input type="hidden" id="carRentalTripId">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Company</label>
                        <input type="text" id="carRentalCompany" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Car Type</label>
                        <input type="text" id="carRentalType" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Pickup Location</label>
                        <input type="text" id="carRentalPickupLocation" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Dropoff Location</label>
                        <input type="text" id="carRentalDropoffLocation" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Pickup Time</label>
                        <input type="datetime-local" id="carRentalPickupTime" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Dropoff Time</label>
                        <input type="datetime-local" id="carRentalDropoffTime" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Price</label>
                        <input type="number" id="carRentalPrice" required step="0.01" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Booking Reference</label>
                        <input type="text" id="carRentalReference" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Notes</label>
                        <textarea id="carRentalNotes" rows="3" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"></textarea>
                    </div>
                    <div class="flex justify-end gap-4">
                        <button type="button" id="cancelCarRentalBtn" class="px-4 py-2 text-gray-600 hover:text-gray-800">Cancel</button>
                        <button type="submit" class="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700">Add Car Rental</button>
                    </div>
                </form>
            </div>
        </div>
    `;

    // Add event listeners
    const backButton = document.getElementById('backButton');
    const createTripBtn = document.getElementById('createTripBtn');
    const tripModal = document.getElementById('tripModal');
    const cancelTripBtn = document.getElementById('cancelTripBtn');
    const tripForm = document.getElementById('tripForm');

    backButton.addEventListener('click', () => {
        history.pushState(null, '', '/');
        loadMainContent();
    });

    createTripBtn.addEventListener('click', () => {
        tripModal.classList.remove('hidden');
    });

    cancelTripBtn.addEventListener('click', () => {
        tripModal.classList.add('hidden');
    });

    tripForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const tripData = {
            title: document.getElementById('tripTitle').value,
            destination: document.getElementById('tripDestination').value,
            start_date: new Date(document.getElementById('tripStartDate').value).toISOString(),
            end_date: new Date(document.getElementById('tripEndDate').value).toISOString(),
            notes: document.getElementById('tripNotes').value
        };
        
        try {
            await travel.createTrip(tripData);
            tripModal.classList.add('hidden');
            loadTrips();
            showSuccess('Trip created successfully');
        } catch (error) {
            showError('Failed to create trip');
        }
    });

    // Add modal form handlers
    const accommodationForm = document.getElementById('accommodationForm');
    const flightForm = document.getElementById('flightForm');
    const carRentalForm = document.getElementById('carRentalForm');

    // Accommodation form handler
    accommodationForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = {
            trip_id: parseInt(document.getElementById('accommodationTripId').value),
            type: document.getElementById('accommodationType').value,
            name: document.getElementById('accommodationName').value,
            location: document.getElementById('accommodationLocation').value,
            check_in: new Date(document.getElementById('accommodationCheckIn').value).toISOString(),
            check_out: new Date(document.getElementById('accommodationCheckOut').value).toISOString(),
            price: parseFloat(document.getElementById('accommodationPrice').value),
            booking_reference: document.getElementById('accommodationReference').value || null,
            notes: document.getElementById('accommodationNotes').value || null
        };

        try {
            await travel.createAccommodation(formData);
            hideAccommodationModal();
            loadTripDetails(formData.trip_id);
            showSuccess('Accommodation added successfully');
        } catch (error) {
            console.error('Error adding accommodation:', error);
            showError('Failed to add accommodation');
        }
    });

    // Flight form handler
    flightForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = {
            trip_id: parseInt(document.getElementById('flightTripId').value),
            airline: document.getElementById('flightAirline').value,
            flight_number: document.getElementById('flightNumber').value,
            departure_airport: document.getElementById('flightDepartureAirport').value,
            arrival_airport: document.getElementById('flightArrivalAirport').value,
            departure_time: new Date(document.getElementById('flightDepartureTime').value).toISOString(),
            arrival_time: new Date(document.getElementById('flightArrivalTime').value).toISOString(),
            price: parseFloat(document.getElementById('flightPrice').value),
            booking_reference: document.getElementById('flightReference').value || null,
            notes: document.getElementById('flightNotes').value || null
        };

        try {
            await travel.createFlight(formData);
            hideFlightModal();
            loadTripDetails(formData.trip_id);
            showSuccess('Flight added successfully');
        } catch (error) {
            console.error('Error adding flight:', error);
            showError('Failed to add flight');
        }
    });

    // Car rental form handler
    carRentalForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = {
            trip_id: parseInt(document.getElementById('carRentalTripId').value),
            company: document.getElementById('carRentalCompany').value,
            car_type: document.getElementById('carRentalType').value,
            pickup_location: document.getElementById('carRentalPickupLocation').value,
            dropoff_location: document.getElementById('carRentalDropoffLocation').value,
            pickup_time: new Date(document.getElementById('carRentalPickupTime').value).toISOString(),
            dropoff_time: new Date(document.getElementById('carRentalDropoffTime').value).toISOString(),
            price: parseFloat(document.getElementById('carRentalPrice').value),
            booking_reference: document.getElementById('carRentalReference').value || null,
            notes: document.getElementById('carRentalNotes').value || null
        };

        try {
            await travel.createCarRental(formData);
            hideCarRentalModal();
            loadTripDetails(formData.trip_id);
            showSuccess('Car rental added successfully');
        } catch (error) {
            console.error('Error adding car rental:', error);
            showError('Failed to add car rental');
        }
    });

    // Add modal cancel button handlers
    document.getElementById('cancelAccommodationBtn').addEventListener('click', hideAccommodationModal);
    document.getElementById('cancelFlightBtn').addEventListener('click', hideFlightModal);
    document.getElementById('cancelCarRentalBtn').addEventListener('click', hideCarRentalModal);

    // Load initial data
    loadTrips();
}

async function loadTrips() {
    try {
        const trips = await travel.getTrips();
        displayTrips(trips);
    } catch (error) {
        console.error('Error loading trips:', error);
        showError('Failed to load trips');
    }
}

function displayTrips(trips) {
    const tripsList = document.getElementById('tripsList');
    if (trips.length === 0) {
        tripsList.innerHTML = `
            <div class="col-span-full text-center py-8">
                <p class="text-gray-500">No trips planned yet. Create your first trip!</p>
            </div>
        `;
        return;
    }

    tripsList.innerHTML = trips.map(trip => `
        <div class="trip-card bg-white rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow duration-300" data-trip-id="${trip.id}">
            <h3 class="text-lg font-semibold mb-2">${trip.title}</h3>
            <p class="text-gray-600 mb-1"><i class="fas fa-map-marker-alt mr-2"></i>${trip.destination}</p>
            <p class="text-gray-600"><i class="fas fa-calendar mr-2"></i>${formatDate(trip.start_date)} - ${formatDate(trip.end_date)}</p>
            ${trip.notes ? `<p class="text-gray-500 mt-2 text-sm">${trip.notes}</p>` : ''}
            <div class="mt-4 flex justify-end">
                <span class="text-primary-600 hover:text-primary-700">
                    <i class="fas fa-chevron-right"></i>
                </span>
            </div>
        </div>
    `).join('');

    // Add event delegation for trip clicks
    tripsList.addEventListener('click', async (e) => {
        const tripCard = e.target.closest('.trip-card');
        if (!tripCard) return;

        const tripId = tripCard.dataset.tripId;
        if (!tripId) return;

        // Show loading state on the clicked card
        const originalContent = tripCard.innerHTML;
        tripCard.innerHTML = `
            <div class="flex justify-center items-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                <span class="ml-2 text-gray-600">Loading trip details...</span>
            </div>
        `;

        try {
            await loadTripDetails(parseInt(tripId));
        } catch (error) {
            // Restore original content if there's an error
            tripCard.innerHTML = originalContent;
        }
    });
}

// Add global event delegation for trip clicks
document.addEventListener('click', async (e) => {
    // Handle trip card clicks
    const tripCard = e.target.closest('[data-trip-id]');
    if (tripCard) {
        const tripId = parseInt(tripCard.dataset.tripId);
        await loadTripDetails(tripId);
        return;
    }

    // Handle accommodation modal
    if (e.target.matches('[data-action="show-accommodation-modal"]')) {
        const tripId = parseInt(e.target.dataset.tripId);
        showAccommodationModal(tripId);
        return;
    }

    // Handle flight modal
    if (e.target.matches('[data-action="show-flight-modal"]')) {
        const tripId = parseInt(e.target.dataset.tripId);
        showFlightModal(tripId);
        return;
    }

    // Handle car rental modal
    if (e.target.matches('[data-action="show-car-rental-modal"]')) {
        const tripId = parseInt(e.target.dataset.tripId);
        showCarRentalModal(tripId);
        return;
    }
});

async function loadTripDetails(tripId) {
    try {
        showLoading(true);
        
        // First load and display basic trip details
        const tripDetails = await travel.getTripDetails(tripId);
        displayTripDetails(tripDetails);
        
        // Then load recommendations in the background
        const recommendationsSection = document.getElementById('tripRecommendations');
        if (recommendationsSection) {
            recommendationsSection.innerHTML = `
                <div class="flex justify-center items-center py-4">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                    <span class="ml-2 text-gray-600">Loading recommendations...</span>
                </div>
            `;
            
            try {
                const recommendations = await travel.getTripRecommendations(tripId);
                displayTripRecommendations(recommendations);
            } catch (error) {
                console.error('Error loading recommendations:', error);
                recommendationsSection.innerHTML = `
                    <div class="text-center py-4">
                        <p class="text-gray-500">Unable to load recommendations at this time.</p>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('Error loading trip details:', error);
        showError('Failed to load trip details');
    } finally {
        showLoading(false);
    }
}

function displayTripDetails(tripDetails) {
    const tripsList = document.getElementById('tripsList');
    tripsList.innerHTML = `
        <div class="col-span-full">
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-semibold">${tripDetails.title}</h3>
                    <button class="text-gray-600 hover:text-gray-800" onclick="loadTrips()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <div class="mb-6">
                            <h4 class="font-medium mb-2">Trip Details</h4>
                            <p class="text-gray-600">Destination: ${tripDetails.destination}</p>
                            <p class="text-gray-600">Dates: ${formatDate(tripDetails.start_date)} - ${formatDate(tripDetails.end_date)}</p>
                            ${tripDetails.notes ? `<p class="text-gray-600 mt-2">Notes: ${tripDetails.notes}</p>` : ''}
                        </div>

                        <div class="space-y-2">
                            <button onclick="showAccommodationModal(${tripDetails.id})" class="w-full bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700">
                                <i class="fas fa-hotel mr-2"></i>Add Accommodation
                            </button>
                            <button onclick="showFlightModal(${tripDetails.id})" class="w-full bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700">
                                <i class="fas fa-plane mr-2"></i>Add Flight
                            </button>
                            <button onclick="showCarRentalModal(${tripDetails.id})" class="w-full bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700">
                                <i class="fas fa-car mr-2"></i>Add Car Rental
                            </button>
                        </div>
                    </div>

                    <div>
                        <div class="mb-6">
                            <h4 class="font-medium mb-2">Accommodations</h4>
                            ${tripDetails.accommodations && tripDetails.accommodations.length > 0 ? 
                                tripDetails.accommodations.map(acc => `
                                    <div class="bg-gray-50 rounded p-3 mb-2">
                                        <div class="font-medium">${acc.name}</div>
                                        <p class="text-sm text-gray-600">${acc.location}</p>
                                        <p class="text-sm text-gray-600">${formatDate(acc.check_in)} - ${formatDate(acc.check_out)}</p>
                                        <p class="text-sm text-gray-600">$${acc.price}</p>
                                    </div>
                                `).join('') :
                                '<p class="text-gray-500">No accommodations added yet</p>'
                            }
                        </div>

                        <div class="mb-6">
                            <h4 class="font-medium mb-2">Flights</h4>
                            ${tripDetails.flights && tripDetails.flights.length > 0 ?
                                tripDetails.flights.map(flight => `
                                    <div class="bg-gray-50 rounded p-3 mb-2">
                                        <div class="font-medium">${flight.airline} - ${flight.flight_number}</div>
                                        <p class="text-sm text-gray-600">${flight.departure_airport} → ${flight.arrival_airport}</p>
                                        <p class="text-sm text-gray-600">${formatDate(flight.departure_time)} - ${formatDate(flight.arrival_time)}</p>
                                        <p class="text-sm text-gray-600">$${flight.price}</p>
                                    </div>
                                `).join('') :
                                '<p class="text-gray-500">No flights added yet</p>'
                            }
                        </div>

                        <div class="mb-6">
                            <h4 class="font-medium mb-2">Car Rentals</h4>
                            ${tripDetails.car_rentals && tripDetails.car_rentals.length > 0 ?
                                tripDetails.car_rentals.map(rental => `
                                    <div class="bg-gray-50 rounded p-3 mb-2">
                                        <div class="font-medium">${rental.company} - ${rental.car_type}</div>
                                        <p class="text-sm text-gray-600">${rental.pickup_location} → ${rental.dropoff_location}</p>
                                        <p class="text-sm text-gray-600">${formatDate(rental.pickup_time)} - ${formatDate(rental.dropoff_time)}</p>
                                        <p class="text-sm text-gray-600">$${rental.price}</p>
                                    </div>
                                `).join('') :
                                '<p class="text-gray-500">No car rentals added yet</p>'
                            }
                        </div>
                    </div>
                </div>

                <div id="tripRecommendations" class="mt-6">
                    <!-- Recommendations will be loaded here -->
                </div>
            </div>
        </div>
    `;
}

function displayTripRecommendations(recommendations) {
    const recommendationsSection = document.getElementById('tripRecommendations');
    if (!recommendationsSection) return;

    recommendationsSection.innerHTML = `
        <h4 class="font-medium mb-2">AI Travel Recommendations</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            ${recommendations.map(rec => `
                <div class="bg-gray-50 rounded p-4">
                    <h5 class="font-medium mb-2">${rec.title}</h5>
                    <p class="text-sm text-gray-600 mb-3">${rec.description}</p>
                    ${rec.actionItems && rec.actionItems.length > 0 ? `
                        <ul class="text-sm text-gray-600 list-disc list-inside">
                            ${rec.actionItems.map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    ` : ''}
                </div>
            `).join('')}
        </div>
    `;
}

// Modal control functions
function showAccommodationModal(tripId) {
    document.getElementById('accommodationTripId').value = tripId;
    document.getElementById('accommodationModal').classList.remove('hidden');
}

function hideAccommodationModal() {
    document.getElementById('accommodationForm').reset();
    document.getElementById('accommodationModal').classList.add('hidden');
}

function showFlightModal(tripId) {
    document.getElementById('flightTripId').value = tripId;
    document.getElementById('flightModal').classList.remove('hidden');
}

function hideFlightModal() {
    document.getElementById('flightForm').reset();
    document.getElementById('flightModal').classList.add('hidden');
}

function showCarRentalModal(tripId) {
    document.getElementById('carRentalTripId').value = tripId;
    document.getElementById('carRentalModal').classList.remove('hidden');
}

function hideCarRentalModal() {
    document.getElementById('carRentalForm').reset();
    document.getElementById('carRentalModal').classList.add('hidden');
} 