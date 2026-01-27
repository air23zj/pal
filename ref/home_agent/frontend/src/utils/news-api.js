import { api } from './api';

export const news = {
  getRecommendations: async () => {
    const response = await api.get('/news/recommendations');
    return response.data;
  }
}; 