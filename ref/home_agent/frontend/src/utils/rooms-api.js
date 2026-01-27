import { api } from './api';

export const rooms = {
  createRoom: async () => {
    const response = await api.post('/rooms');
    return response.data;
  },
  
  getRooms: async () => {
    const response = await api.get('/rooms');
    return response.data;
  },
  
  deleteRoom: async (roomId) => {
    const response = await api.delete(`/rooms/${roomId}`);
    return response.data;
  }
}; 