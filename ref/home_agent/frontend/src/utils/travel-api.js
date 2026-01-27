import { api } from './api';

export const travel = {
  async getTrips() {
    const response = await api.get('/travel/trips');
    return response.data;
  },

  async createTrip(data) {
    const response = await api.post('/travel/trips', data);
    return response.data;
  },

  async getTripDetails(tripId) {
    const response = await api.get(`/travel/trips/${tripId}/details`);
    return response.data;
  },

  async getTrip(tripId) {
    const response = await api.get(`/travel/trips/${tripId}`);
    return response.data;
  },

  async createAccommodation(data) {
    const response = await api.post('/travel/accommodations', data);
    return response.data;
  },

  async createFlight(data) {
    const response = await api.post('/travel/flights', data);
    return response.data;
  },

  async createCarRental(data) {
    const response = await api.post('/travel/car-rentals', data);
    return response.data;
  },

  async getTripRecommendations(tripId) {
    const response = await api.post(`/travel/trips/${tripId}/recommendations`);
    return response.data;
  }
}; 