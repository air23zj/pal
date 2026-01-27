import { api } from './api';

export const weather = {
  async getLocations() {
    const response = await api.get('/weather/locations');
    return response.data;
  },

  async addLocation(location) {
    const response = await api.post('/weather/locations', location);
    return response.data;
  },

  async removeLocation(locationId) {
    const response = await api.delete(`/weather/locations/${locationId}`);
    return response.data;
  },

  async getWeatherData(locationId) {
    const response = await api.get(`/weather/${locationId}`);
    return response.data;
  },

  async getWeatherRecommendations(locationId) {
    const response = await api.get(`/weather/${locationId}/recommendations`);
    return response.data;
  }
}; 