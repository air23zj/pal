import { api } from './api';

export const voiceMemos = {
  createMemo: async (formData) => {
    const response = await api.post('/voice-memos', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  getMemos: async () => {
    const response = await api.get('/voice-memos');
    return response.data;
  },
  
  deleteMemo: async (memoId) => {
    const response = await api.delete(`/voice-memos/${memoId}`);
    return response.data;
  },
  
  getMemoAudio: async (memoId) => {
    const response = await api.get(`/voice-memos/${memoId}/audio`, {
      responseType: 'blob'
    });
    return response.data;
  },

  transcribeMemo: async (memoId) => {
    const response = await api.post(`/voice-memos/${memoId}/transcribe`);
    return response.data;
  },

  transcribeNew: async (formData) => {
    const response = await api.post('/voice-memos/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }
}; 