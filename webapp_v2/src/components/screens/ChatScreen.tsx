import { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../../stores/useAppStore';
import { api } from '../../services/api';
import { telegram } from '../../services/telegram';
import { MessageBubble } from '../chat/MessageBubble';
import type { Message } from '../../types';

interface ChatScreenProps {
  isActive: boolean;
}

export const ChatScreen = ({ isActive }: ChatScreenProps) => {
  const user = useAppStore((state) => state.user);
  const chatMessages = useAppStore((state) => state.chatMessages);
  const addChatMessage = useAppStore((state) => state.addChatMessage);
  const updateChatMessage = useAppStore((state) => state.updateChatMessage);
  const setScreen = useAppStore((state) => state.setScreen);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

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

    addChatMessage(userMessage);
    setInputValue('');
    setIsLoading(true);
    telegram.haptic('light');

    try {
      const response = await api.sendChatMessage(user.id, inputValue, 'helper');

      if (response.success && response.data) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: (response.data as any).message || 'Извините, произошла ошибка',
          timestamp: new Date(),
        };
        addChatMessage(assistantMessage);
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
      addChatMessage(errorMessage);
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

  const handleReaction = (messageId: string, reaction: 'like' | 'dislike') => {
    if (updateChatMessage) {
      updateChatMessage(messageId, { reaction });
      // TODO: Send reaction to backend API for analytics
      console.log('Reaction:', messageId, reaction);
    }
  };

  const handleEdit = (messageId: string) => {
    const message = chatMessages.find(m => m.id === messageId);
    if (message && message.role === 'user') {
      setInputValue(message.content);
      telegram.haptic('light');
      // TODO: Remove messages after the edited one and resend
    }
  };

  return (
    <div className={`screen chat-screen ${isActive ? 'active' : ''}`}>
      <div className="chat-header">
        <div className="chat-left-controls">
          <button className="chat-back-btn" onClick={() => setScreen('voiceChat')}>←</button>
          <div className="voice-multitask-icon" onClick={() => setScreen('chatHistory')}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="13" y="3" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="3" y="13" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="13" y="13" width="8" height="8" rx="2" fill="#4A90E2"/>
            </svg>
          </div>
        </div>
        <h1 className="chat-title">Soul Near GPT</h1>
        <div className="chat-avatar">
          <img src="/Robo.png" alt="SoulNear Assistant" />
        </div>
      </div>

      <div className="chat-messages" id="chatMessages">
        {chatMessages.length === 0 && (
          <div className="chat-empty">
            <div className="empty-icon">💭</div>
            <h3>Начните разговор</h3>
            <p>Задайте любой вопрос или расскажите о своих мыслях</p>
          </div>
        )}

        {chatMessages.map((message, index) => (
          <MessageBubble
            key={message.id}
            message={message}
            onReaction={handleReaction}
            onEdit={handleEdit}
            isLastUserMessage={
              message.role === 'user' &&
              index === chatMessages.length - (isLoading ? 2 : 1)
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
        <button className="chat-voice-btn" onClick={() => setScreen('generalVoice')}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14Z" fill="white"/>
            <path d="M19 11C19 14.53 16.39 17.44 13 17.93V21H11V17.93C7.61 17.44 5 14.53 5 11H7C7 13.76 9.24 16 12 16C14.76 16 17 13.76 17 11H19Z" fill="white"/>
          </svg>
        </button>
        <input
          type="text"
          id="chatInput"
          placeholder="Чем я могу помочь?"
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
