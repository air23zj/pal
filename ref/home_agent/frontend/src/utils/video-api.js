import { api } from './api';

export const video = {
    async summarizeTranscription(text) {
        // Create a temporary document with the transcription text
        const response = await api.post('/documents', {
            title: 'Video Call Transcription',
            content: text
        });
        
        // Get the document ID and request a summary
        const docId = response.data.id;
        const summaryResponse = await api.post(`/documents/${docId}/summarize`);
        
        // Delete the temporary document
        await api.delete(`/documents/${docId}`);
        
        return summaryResponse.data;
    }
}; 