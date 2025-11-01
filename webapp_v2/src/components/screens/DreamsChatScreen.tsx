import { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../../stores/useAppStore';
import { api } from '../../services/api';
import { telegram } from '../../services/telegram';
import { MessageBubble } from '../chat/MessageBubble';
import { VoiceRecorder } from '../chat/VoiceRecorder';
import type { Message } from '../../types';

interface DreamsChatScreenProps {
  isActive: boolean;
}

export const DreamsChatScreen = ({ isActive }: DreamsChatScreenProps) => {
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

  const handleVoiceRecording = async (audioBlob: Blob) => {
    if (!user) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: '🎤 Голосовое сообщение...',
      timestamp: new Date(),
    };
    addDreamMessage(userMessage);
    setIsLoading(true);

    try {
      const response = await api.sendVoiceMessage(user.id, audioBlob);

      if (response.success && response.data) {
        const transcription = (response.data as any).transcription || '🎤 Голосовое сообщение';
        const updatedUserMessage: Message = {
          ...userMessage,
          content: transcription,
        };
        clearDreamMessages();
        dreamMessages.forEach(msg => {
          if (msg.id !== userMessage.id) {
            addDreamMessage(msg);
          }
        });
        addDreamMessage(updatedUserMessage);

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
      console.error('Voice error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Извините, не удалось обработать голосовое сообщение. Попробуйте позже.',
        timestamp: new Date(),
      };
      addDreamMessage(errorMessage);
      telegram.hapticError();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`screen chat-screen ${isActive ? 'active' : ''}`} id="dreams-chat-screen">
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
        <h1 className="chat-title">Анализ снов</h1>
        <div className="chat-right-controls">
          <button className="chat-new-btn" onClick={createNewChat} title="Новый чат">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="#4A90E2"/>
            </svg>
          </button>
          <div className="chat-avatar">
            <img src="/Robo.png" alt="SoulNear" />
          </div>
        </div>
      </div>

      <div className="chat-messages" id="dreamsChatMessages">
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
        <div className="chat-voice-btn-wrapper">
          <VoiceRecorder onRecordingComplete={handleVoiceRecording} />
        </div>
        <input
          type="text"
          id="dreamsInput"
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
