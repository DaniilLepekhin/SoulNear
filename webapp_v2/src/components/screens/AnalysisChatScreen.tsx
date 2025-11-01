import { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../../stores/useAppStore';
import { api } from '../../services/api';
import { telegram } from '../../services/telegram';
import { MessageBubble } from '../chat/MessageBubble';
import { VoiceRecorder } from '../chat/VoiceRecorder';
import type { Message } from '../../types';

interface AnalysisChatScreenProps {
  isActive: boolean;
}

const TOPIC_TITLES = {
  relationships: 'Анализ отношений',
  money: 'Анализ денег',
  confidence: 'Анализ уверенности',
  fears: 'Анализ страхов',
};

const TOPIC_PLACEHOLDERS = {
  relationships: 'Расскажите о вашей ситуации...',
  money: 'Опишите вашу финансовую ситуацию...',
  confidence: 'Что вас беспокоит?',
  fears: 'О каких страхах хотите поговорить?',
};

export const AnalysisChatScreen = ({ isActive }: AnalysisChatScreenProps) => {
  const user = useAppStore((state) => state.user);
  const analysisMessages = useAppStore((state) => state.analysisMessages);
  const addAnalysisMessage = useAppStore((state) => state.addAnalysisMessage);
  const clearAnalysisMessages = useAppStore((state) => state.clearAnalysisMessages);
  const currentAnalysisTopic = useAppStore((state) => state.currentAnalysisTopic);
  const setScreen = useAppStore((state) => state.setScreen);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [analysisMessages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading || !user || !currentAnalysisTopic) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    addAnalysisMessage(userMessage);
    setInputValue('');
    setIsLoading(true);
    telegram.haptic('light');

    try {
      const response = await api.sendAnalysisMessage(user.id, currentAnalysisTopic, inputValue);

      if (response.success && response.data) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: (response.data as any).message || 'Извините, произошла ошибка',
          timestamp: new Date(),
        };
        addAnalysisMessage(assistantMessage);
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
      addAnalysisMessage(errorMessage);
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
    clearAnalysisMessages();
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
    addAnalysisMessage(userMessage);
    setIsLoading(true);

    try {
      const response = await api.sendVoiceMessage(user.id, audioBlob);

      if (response.success && response.data) {
        const transcription = (response.data as any).transcription || '🎤 Голосовое сообщение';
        const updatedUserMessage: Message = {
          ...userMessage,
          content: transcription,
        };
        clearAnalysisMessages();
        analysisMessages.forEach(msg => {
          if (msg.id !== userMessage.id) {
            addAnalysisMessage(msg);
          }
        });
        addAnalysisMessage(updatedUserMessage);

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: (response.data as any).message || 'Извините, произошла ошибка',
          timestamp: new Date(),
        };
        addAnalysisMessage(assistantMessage);
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
      addAnalysisMessage(errorMessage);
      telegram.hapticError();
    } finally {
      setIsLoading(false);
    }
  };

  const title = currentAnalysisTopic ? TOPIC_TITLES[currentAnalysisTopic] : 'Анализ';
  const placeholder = currentAnalysisTopic ? TOPIC_PLACEHOLDERS[currentAnalysisTopic] : 'Напишите сообщение...';

  return (
    <div className={`screen chat-screen ${isActive ? 'active' : ''}`} id="analysis-chat-screen">
      <div className="chat-header">
        <div className="chat-left-controls">
          <button className="chat-back-btn" onClick={() => setScreen('analysis')}>←</button>
          <div className="voice-multitask-icon" onClick={() => setScreen('chatHistory')}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="13" y="3" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="3" y="13" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="13" y="13" width="8" height="8" rx="2" fill="#4A90E2"/>
            </svg>
          </div>
        </div>
        <h1 className="chat-title">{title}</h1>
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

      <div className="chat-messages" id="analysisChatMessages">
        {analysisMessages.length === 0 && (
          <div className="chat-empty">
            <div className="empty-icon">💭</div>
            <h3>Начните разговор</h3>
            <p>{placeholder}</p>
          </div>
        )}

        {analysisMessages.map((message, index) => (
          <MessageBubble
            key={message.id}
            message={message}
            isLastUserMessage={
              message.role === 'user' &&
              index === analysisMessages.length - (isLoading ? 2 : 1)
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
          id="analysisChatInput"
          placeholder={placeholder}
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
