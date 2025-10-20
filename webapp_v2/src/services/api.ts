// API Service - Connected to Real Backend
// Use relative path to work with nginx proxy
const API_URL = import.meta.env.VITE_API_URL || '';

class ApiService {
  private baseUrl = API_URL;

  async sendChatMessage(userId: number, message: string, assistantType: string = 'helper') {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, message: message, assistant_type: assistantType })
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data: { message: data.response } };
    } catch (error) {
      console.error('Chat API error:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async getChatHistory(userId: number) {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat/history/${userId}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async sendVoiceMessage(userId: number, audioBlob: Blob) {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob);
      formData.append('user_id', userId.toString());
      const response = await fetch(`${this.baseUrl}/api/voice`, { method: 'POST', body: formData });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async getPractices() {
    try {
      const response = await fetch(`${this.baseUrl}/api/practices`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const result = await response.json();

      // API returns {status: "success", data: {...}}
      // We need to return just the data part
      if (result.status === 'success') {
        return { success: true, data: result.data };
      } else {
        return { success: false, error: 'API returned error status' };
      }
    } catch (error) {
      console.error('❌ getPractices error:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async sendAnalysisMessage(userId: number, topic: string, message: string) {
    return this.sendChatMessage(userId, message, `analysis_${topic}`);
  }

  async sendDreamMessage(userId: number, message: string) {
    return this.sendChatMessage(userId, message, 'dreams');
  }

  async updateMood(userId: number, mood: string) {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/mood`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, mood })
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }
}

export const api = new ApiService();
