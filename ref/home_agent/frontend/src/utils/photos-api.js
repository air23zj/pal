import { api } from './api';

export const photos = {
  list: async () => {
    const response = await api.get('/photos');
    return response.data;
  },

  upload: async (formData) => {
    const response = await api.post('/photos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  delete: async (photoId) => {
    const response = await api.delete(`/files/${photoId}`);
    return response.data;
  },

  share: async (photoId, username) => {
    const response = await api.post(`/files/${photoId}/share`, { username });
    return response.data;
  },

  getContent: async (photoId) => {
    const response = await api.get(`/files/${photoId}/content`, {
      responseType: 'blob'
    });
    return URL.createObjectURL(response.data);
  },

  getThumbnail: async (photoId) => {
    const response = await api.get(`/files/${photoId}/thumbnail`, {
      responseType: 'blob'
    });
    return URL.createObjectURL(response.data);
  },

  generateSubtitle: async (photoId) => {
    const response = await api.post(`/files/${photoId}/subtitle`);
    return response.data;
  }
}; 