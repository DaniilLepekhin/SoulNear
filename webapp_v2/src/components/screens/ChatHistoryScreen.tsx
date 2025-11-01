import { useState, useEffect } from 'react';
import { useAppStore } from '../../stores/useAppStore';
import { telegram } from '../../services/telegram';
import { api } from '../../services/api';

interface ChatHistoryScreenProps {
  isActive: boolean;
}

interface ChatThread {
  thread_id: string;
  title: string | null;
  assistant_type: string;
  created_at: string;
  updated_at: string;
  first_message: string | null;
  last_message: string | null;
}


export const ChatHistoryScreen = ({ isActive }: ChatHistoryScreenProps) => {
  const user = useAppStore((state) => state.user);
  const setScreen = useAppStore((state) => state.setScreen);
  const previousScreen = useAppStore((state) => state.previousScreen);
  const setCurrentThreadId = useAppStore((state) => state.setCurrentThreadId);

  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load threads from database
  useEffect(() => {
    if (isActive && user) {
      loadThreads();
    }
  }, [isActive, user]);

  const loadThreads = async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      const response = await api.getChatThreads(user.id);
      if (response.success && response.data) {
        setThreads(response.data as ChatThread[]);
      }
    } catch (error) {
      console.error('Failed to load threads:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const goBackFromHistory = () => {
    if (previousScreen && ['chat', 'generalVoice', 'analysisChat', 'dreamsChat'].includes(previousScreen)) {
      setScreen(previousScreen);
    } else {
      setScreen('chat');
    }
    telegram.haptic('light');
  };

  const createNewChat = async () => {
    if (!user) return;
    telegram.haptic('light');

    // Create new thread
    const response = await api.createChatThread(user.id, 'helper');
    if (response.success && response.threadId) {
      setCurrentThreadId(response.threadId);
      setScreen('generalVoice');
    }
  };

  const openThread = (threadId: string) => {
    telegram.haptic('light');
    setCurrentThreadId(threadId);
    setScreen('generalVoice');
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return 'Сегодня';
    } else if (diffDays === 1) {
      return 'Вчера';
    } else if (diffDays < 7) {
      return `${diffDays} дн. назад`;
    } else {
      return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
    }
  };

  const generateTitle = (firstMessage: string | null) => {
    if (firstMessage && firstMessage.length > 0) {
      return firstMessage.substring(0, 50) + (firstMessage.length > 50 ? '...' : '');
    }
    return `Новый диалог`;
  };

  return (
    <div className={`screen ${isActive ? 'active' : ''}`} id="chat-history-screen">
      <div className="chat-history-header">
        <div className="history-left-controls">
          <button className="back-btn" onClick={goBackFromHistory}>←</button>
          <div className="chat-history-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="13" y="3" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="3" y="13" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="13" y="13" width="8" height="8" rx="2" fill="#4A90E2"/>
            </svg>
          </div>
        </div>
        <h3 className="chat-history-title">Soul Near GPT</h3>
        <div className="history-right-controls">
          <button className="new-chat-btn" onClick={createNewChat}>+</button>
        </div>
      </div>

      <div className="history-content">
        {isLoading ? (
          <div className="history-loading">
            <div className="spinner"></div>
            <p>Загрузка диалогов...</p>
          </div>
        ) : threads.length === 0 ? (
          <div className="history-empty">
            <div className="empty-icon">💬</div>
            <h3>Нет диалогов</h3>
            <p>Начните новый разговор с ассистентом</p>
          </div>
        ) : (
          <div className="history-group">
            <h4 className="history-date">Все диалоги</h4>
            {threads.map((thread) => (
              <div key={thread.thread_id} className="history-item" onClick={() => openThread(thread.thread_id)}>
                <div className="history-item-title">
                  {thread.title || generateTitle(thread.first_message)}
                </div>
                <div className="history-item-preview">
                  {thread.last_message ? thread.last_message.substring(0, 100) + (thread.last_message.length > 100 ? '...' : '') : 'Нет сообщений'}
                </div>
                <div className="history-item-meta">
                  {formatDate(thread.updated_at)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
