import { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../../stores/useAppStore';
import { api } from '../../services/api';
import { telegram } from '../../services/telegram';
import { MessageBubble } from '../chat/MessageBubble';
import type { Message } from '../../types';

interface DreamsVoiceScreenProps {
  isActive: boolean;
}

export const DreamsVoiceScreen = ({ isActive }: DreamsVoiceScreenProps) => {
  const user = useAppStore((state) => state.user);
  const dreamMessages = useAppStore((state) => state.dreamMessages);
  const addDreamMessage = useAppStore((state) => state.addDreamMessage);
  const clearDreamMessages = useAppStore((state) => state.clearDreamMessages);
  const setScreen = useAppStore((state) => state.setScreen);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [dreamMessages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading || !user) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    addDreamMessage(userMessage);
    setInputValue('');
    setIsLoading(true);
    telegram.haptic('light');

    try {
      const response = await api.sendDreamMessage(user.id, inputValue);

      if (response.success && response.data) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: (response.data as any).message || 'Извините, произошла ошибка',
          timestamp: new Date(),
        };
        addDreamMessage(assistantMessage);
        telegram.hapticSuccess();
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Извините, не удалось получить ответ. Попробуйте позже.',
        timestamp: new Date(),
      };
      addDreamMessage(errorMessage);
      telegram.hapticError();
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const createNewChat = () => {
    clearDreamMessages();
    telegram.haptic('light');
  };

  return (
    <div className={`screen voice-chat-screen ${isActive ? 'active' : ''}`} id="dreams-voice-screen">
      <div className="voice-header">
        <div className="voice-left-controls">
          <button className="voice-back-btn" onClick={() => setScreen('dreams')}>←</button>
          <div className="voice-multitask-icon" onClick={() => setScreen('chatHistory')}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="13" y="3" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="3" y="13" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="13" y="13" width="8" height="8" rx="2" fill="#4A90E2"/>
            </svg>
          </div>
        </div>
        <h1 className="voice-title">Анализ снов</h1>
        <div className="voice-avatar">
          <img src="/Robo.png" alt="SoulNear Assistant" />
        </div>
      </div>

      <div className="voice-messages" id="dreamsVoiceMessages">
        {dreamMessages.length === 0 && (
          <div className="chat-empty">
            <div className="empty-icon">🌙</div>
            <h3>Расскажите о своём сне</h3>
            <p>Опишите детали вашего сна для глубокого анализа</p>
          </div>
        )}

        {dreamMessages.map((message, index) => (
          <MessageBubble
            key={message.id}
            message={message}
            isLastUserMessage={
              message.role === 'user' &&
              index === dreamMessages.length - (isLoading ? 2 : 1)
            }
          />
        ))}

        {isLoading && (
          <div className="message assistant">
            <div className="message-bubble typing">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <button className="chat-voice-btn" onClick={createNewChat} title="Новый чат">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14Z" fill="white"/>
            <path d="M19 11C19 14.53 16.39 17.44 13 17.93V21H11V17.93C7.61 17.44 5 14.53 5 11H7C7 13.76 9.24 16 12 16C14.76 16 17 13.76 17 11H19Z" fill="white"/>
          </svg>
        </button>
        <input
          type="text"
          id="dreamsVoiceInput"
          placeholder="Расскажите о своём сне..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
        />
        <button className="chat-send-btn" onClick={handleSend} disabled={!inputValue.trim() || isLoading}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" fill="white"/>
          </svg>
        </button>
      </div>
    </div>
  );
};
