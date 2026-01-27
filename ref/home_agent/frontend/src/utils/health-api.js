import { api } from './api';

export const health = {
  // Weight endpoints
  async saveWeight(data) {
    const response = await api.post('/health/weight', data);
    return response.data;
  },

  async getWeightHistory() {
    const response = await api.get('/health/weight');
    return response.data;
  },

  // Height endpoints
  async saveHeight(data) {
    const response = await api.post('/health/height', data);
    return response.data;
  },

  async getHeightHistory() {
    const response = await api.get('/health/height');
    return response.data;
  },

  // Heart rate endpoints
  async saveHeartRate(data) {
    const response = await api.post('/health/heart-rate', data);
    return response.data;
  },

  async getHeartRateHistory() {
    const response = await api.get('/health/heart-rate');
    return response.data;
  },

  // Blood pressure endpoints
  async saveBloodPressure(data) {
    const response = await api.post('/health/blood-pressure', data);
    return response.data;
  },

  async getBloodPressureHistory() {
    const response = await api.get('/health/blood-pressure');
    return response.data;
  },

  // Doctor visits
  async saveDoctorVisit(data) {
    const response = await api.post('/health/visits', data);
    return response.data;
  },

  async getDoctorVisits() {
    const response = await api.get('/health/visits');
    return response.data;
  },

  // Exercise goals
  async saveExerciseGoals(data) {
    const response = await api.post('/health/goals/exercise', data);
    return response.data;
  },

  async getExerciseGoals() {
    const response = await api.get('/health/goals/exercise');
    return response.data;
  },

  // Dietary goals
  async saveDietaryGoals(data) {
    const response = await api.post('/health/goals/dietary', data);
    return response.data;
  },

  async getDietaryGoals() {
    const response = await api.get('/health/goals/dietary');
    return response.data;
  },

  // Health recommendations
  async getRecommendations(healthData) {
    const response = await api.post('/health/recommendations', healthData);
    return response.data;
  }
}; 