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
      const result = await response.json();
      // API returns {status: "success", data: {transcription, message}}
      if (result.status === 'success') {
        return { success: true, data: result.data };
      } else {
        return { success: false, error: result.message || 'API returned error status' };
      }
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

  async saveChatMessage(userId: number, messageId: string, role: string, content: string, assistantType: string = 'helper', threadId: string = 'main', reaction?: string, status?: string) {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, thread_id: threadId, message_id: messageId, role, content, assistant_type: assistantType, reaction, status })
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async loadChatHistory(userId: number, assistantType: string = 'helper', threadId: string = 'main', limit: number = 100, offset: number = 0) {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat/history/${userId}?assistant_type=${assistantType}&thread_id=${threadId}&limit=${limit}&offset=${offset}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data: data.messages || [] };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async createChatThread(userId: number, assistantType: string = 'helper', title?: string) {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat/thread/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, assistant_type: assistantType, title })
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, threadId: data.thread_id };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async getChatThreads(userId: number) {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat/threads/${userId}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data: data.threads || [] };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async getUserInfo(userId: number) {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/${userId}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const result = await response.json();
      if (result.status === 'success') {
        return { success: true, data: result.data };
      } else {
        return { success: false, error: result.message || 'Unknown error' };
      }
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async saveMood(userId: number, date: string, moodValue: number, emoji: string) {
    try {
      const response = await fetch(`${this.baseUrl}/api/mood/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, date, mood_value: moodValue, emoji })
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async getMoodHistory(userId: number, days: number = 30) {
    try {
      const response = await fetch(`${this.baseUrl}/api/mood/history/${userId}?days=${days}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data: data.moods || [] };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  // ==========================================
  // 🧠 AI PATTERNS & INSIGHTS (NEW)
  // ==========================================

  async getUserProfile(userId: number) {
    try {
      const response = await fetch(`${this.baseUrl}/api/profile/${userId}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async getPatterns(userId: number) {
    try {
      const response = await fetch(`${this.baseUrl}/api/profile/${userId}/patterns`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data: data.patterns || [] };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async getInsights(userId: number) {
    try {
      const response = await fetch(`${this.baseUrl}/api/profile/${userId}/insights`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data: data.insights || [] };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async getEmotionalState(userId: number) {
    try {
      const response = await fetch(`${this.baseUrl}/api/profile/${userId}/emotional-state`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  // ==========================================
  // 🎯 ADAPTIVE QUIZZES (NEW)
  // ==========================================

  async startQuiz(userId: number, category: string) {
    try {
      const response = await fetch(`${this.baseUrl}/api/quiz/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, category })
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async getQuizQuestion(sessionId: string) {
    try {
      const response = await fetch(`${this.baseUrl}/api/quiz/${sessionId}/question`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async submitQuizAnswer(sessionId: string, questionId: string, answer: string) {
    try {
      const response = await fetch(`${this.baseUrl}/api/quiz/${sessionId}/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: questionId, answer })
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async getQuizResult(sessionId: string) {
    try {
      const response = await fetch(`${this.baseUrl}/api/quiz/${sessionId}/result`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async getActiveQuizzes(userId: number) {
    try {
      const response = await fetch(`${this.baseUrl}/api/quiz/active/${userId}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: true, data: data.quizzes || [] };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }
}

export const api = new ApiService();
