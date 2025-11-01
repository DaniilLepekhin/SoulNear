import { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../../stores/useAppStore';
import { api } from '../../services/api';
import { telegram } from '../../services/telegram';
import { MessageBubble } from '../chat/MessageBubble';
import { VoiceRecorder } from '../chat/VoiceRecorder';
import type { Message } from '../../types';

interface GeneralVoiceScreenProps {
  isActive: boolean;
}

export const GeneralVoiceScreen = ({ isActive }: GeneralVoiceScreenProps) => {
  const user = useAppStore((state) => state.user);
  const chatMessages = useAppStore((state) => state.chatMessages);
  const currentThreadId = useAppStore((state) => state.currentThreadId);
  const addChatMessage = useAppStore((state) => state.addChatMessage);
  const updateChatMessage = useAppStore((state) => state.updateChatMessage);
  const clearChatMessages = useAppStore((state) => state.clearChatMessages);
  const setCurrentThreadId = useAppStore((state) => state.setCurrentThreadId);
  const setScreen = useAppStore((state) => state.setScreen);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const skipNextLoad = useRef(false);

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  // Load chat history when thread changes
  useEffect(() => {
    if (user) {
      // Skip loading if we just created a new thread (to avoid clearing messages before they're saved)
      if (skipNextLoad.current) {
        skipNextLoad.current = false;
        return;
      }
      clearChatMessages();
      loadHistory();
    }
  }, [currentThreadId]);

  const loadHistory = async () => {
    if (!user) return;
    try {
      const response = await api.loadChatHistory(user.id, 'helper', currentThreadId, 50);
      if (response.success && response.data) {
        const messages = (response.data as any[]).map((msg: any) => ({
          id: msg.message_id || msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.timestamp || msg.created_at),
        }));
        messages.forEach((msg: Message) => addChatMessage(msg));
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading || !user) return;

    // Create new thread if this is the first message and we're on default thread
    let threadId = currentThreadId;
    if (currentThreadId === 'main' && chatMessages.length === 0) {
      const newThreadResponse = await api.createChatThread(user.id, 'helper');
      if (newThreadResponse.success && newThreadResponse.threadId) {
        threadId = newThreadResponse.threadId;
        skipNextLoad.current = true; // Skip the next load to avoid clearing messages
        setCurrentThreadId(threadId);
      }
    }

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

        // Save both messages to database
        await api.saveChatMessage(user.id, userMessage.id, 'user', userMessage.content, 'helper', threadId);
        await api.saveChatMessage(user.id, assistantMessage.id, 'assistant', assistantMessage.content, 'helper', threadId);
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

  const createNewChat = async () => {
    if (!user) return;
    telegram.haptic('light');

    // Create new thread
    const response = await api.createChatThread(user.id, 'helper');
    if (response.success && response.threadId) {
      setCurrentThreadId(response.threadId);
    }
  };

  const handleVoiceRecording = async (audioBlob: Blob) => {
    if (!user) return;

    // Create new thread if this is the first message and we're on default thread
    let threadId = currentThreadId;
    if (currentThreadId === 'main' && chatMessages.length === 0) {
      const newThreadResponse = await api.createChatThread(user.id, 'helper');
      if (newThreadResponse.success && newThreadResponse.threadId) {
        threadId = newThreadResponse.threadId;
        skipNextLoad.current = true; // Skip the next load to avoid clearing messages
        setCurrentThreadId(threadId);
      }
    }

    // Add user message placeholder
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: '🎤 Голосовое сообщение...',
      timestamp: new Date(),
    };
    addChatMessage(userMessage);
    setIsLoading(true);

    try {
      const response = await api.sendVoiceMessage(user.id, audioBlob);

      if (response.success && response.data) {
        // Update user message with transcription
        const transcription = (response.data as any).transcription || '🎤 Голосовое сообщение';
        updateChatMessage(userMessage.id, { content: transcription });

        // Add assistant response
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: (response.data as any).message || 'Извините, произошла ошибка',
          timestamp: new Date(),
        };
        addChatMessage(assistantMessage);
        telegram.hapticSuccess();

        // Save both messages to database
        await api.saveChatMessage(user.id, userMessage.id, 'user', transcription, 'helper', threadId);
        await api.saveChatMessage(user.id, assistantMessage.id, 'assistant', assistantMessage.content, 'helper', threadId);
      }
    } catch (error) {
      console.error('Voice error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Извините, не удалось обработать голосовое сообщение. Попробуйте позже.',
        timestamp: new Date(),
      };
      addChatMessage(errorMessage);
      telegram.hapticError();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`screen chat-screen ${isActive ? 'active' : ''}`} id="general-voice-screen">
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
        <div className="chat-right-controls">
          <button className="chat-new-btn" onClick={createNewChat} title="Новый чат">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="#4A90E2"/>
            </svg>
          </button>
          <div className="chat-avatar">
            <img src="/Robo.png" alt="SoulNear Assistant" />
          </div>
        </div>
      </div>

      <div className="chat-messages" id="generalVoiceMessages">
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

      <div className={`chat-input-container ${isVoiceActive ? 'voice-active' : ''}`}>
        <VoiceRecorder
          onRecordingComplete={handleVoiceRecording}
          onStateChange={setIsVoiceActive}
        />
        {!isVoiceActive && (
          <>
            <input
              type="text"
              id="generalVoiceInput"
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
          </>
        )}
      </div>
    </div>
  );
};
