import { api } from './api';

export const documents = {
  list: async () => {
    try {
      const response = await api.get('/documents');
      return response.data;
    } catch (error) {
      console.error('Error listing documents:', error.response?.data || error.message);
      throw error;
    }
  },

  listShared: async () => {
    const response = await api.get('/documents/shared');
    return response.data;
  },

  create: async (document) => {
    try {
      const response = await api.post('/documents', document);
      return response.data;
    } catch (error) {
      console.error('Error creating document:', error.response?.data || error.message);
      throw error;
    }
  },

  update: async (id, document) => {
    try {
      const response = await api.put(`/documents/${id}`, document);
      return response.data;
    } catch (error) {
      console.error('Error updating document:', error.response?.data || error.message);
      throw error;
    }
  },

  delete: async (id) => {
    try {
      await api.delete(`/documents/${id}`);
    } catch (error) {
      console.error('Error deleting document:', error.response?.data || error.message);
      throw error;
    }
  },

  share: async (id, shareData) => {
    try {
      const response = await api.post(`/documents/${id}/share`, shareData);
      return response.data;
    } catch (error) {
      console.error('Error sharing document:', error.response?.data || error.message);
      throw error;
    }
  },

  move: async (id, folderId) => {
    try {
      const response = await api.post(`/documents/${id}/move`, { folder_id: folderId });
      return response.data;
    } catch (error) {
      console.error('Error moving document:', error.response?.data || error.message);
      throw error;
    }
  },

  summarize: async (id) => {
    try {
      console.log('Requesting summary for document:', id);
      const response = await api.post(`/documents/${id}/summarize`);
      console.log('Summary response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error summarizing document:', error.response?.data || error.message);
      throw error;
    }
  },

  // File-related methods
  listFiles: async () => {
    try {
      const response = await api.get('/files');
      return response.data;
    } catch (error) {
      console.error('Error listing files:', error.response?.data || error.message);
      throw error;
    }
  },

  uploadFile: async (formData) => {
    try {
      const response = await api.post('/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading file:', error.response?.data || error.message);
      throw error;
    }
  },

  downloadFile: async (id) => {
    try {
      const response = await api.get(`/files/${id}/download`);
      return response.data;
    } catch (error) {
      console.error('Error downloading file:', error.response?.data || error.message);
      throw error;
    }
  },

  deleteFile: async (id) => {
    try {
      await api.delete(`/files/${id}`);
    } catch (error) {
      console.error('Error deleting file:', error.response?.data || error.message);
      throw error;
    }
  },

  shareFile: async (id, shareData) => {
    try {
      const response = await api.post(`/files/${id}/share`, shareData);
      return response.data;
    } catch (error) {
      console.error('Error sharing file:', error.response?.data || error.message);
      throw error;
    }
  },

  getThumbnail: async (id) => {
    try {
      const response = await api.get(`/files/${id}/thumbnail`);
      return response.data;
    } catch (error) {
      console.error('Error getting thumbnail:', error.response?.data || error.message);
      throw error;
    }
  },

  getContent: async (id) => {
    try {
      const response = await api.get(`/files/${id}/content`);
      return response.data;
    } catch (error) {
      console.error('Error getting file content:', error.response?.data || error.message);
      throw error;
    }
  },

  addSubtitle: async (id, subtitleData) => {
    try {
      const response = await api.post(`/files/${id}/subtitle`, subtitleData);
      return response.data;
    } catch (error) {
      console.error('Error adding subtitle:', error.response?.data || error.message);
      throw error;
    }
  }
}; 