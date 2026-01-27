import { api } from './api';

export const search = {
  search: async (query) => {
    return await api.post('/search', { query });
  },

  getAnswer: async (query, contexts) => {
    return await api.post('/get_answer', { query, contexts });
  },

  getRelatedQuestions: async (query, contexts) => {
    return await api.post('/get_related_questions', { query, contexts });
  },

  youtube: async (url) => {
    return await api.post('/youtube/summarize', { url });
  }
}; 