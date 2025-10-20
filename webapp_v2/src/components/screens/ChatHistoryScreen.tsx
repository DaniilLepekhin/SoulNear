import { useAppStore } from '../../stores/useAppStore';

interface ChatHistoryScreenProps {
  isActive: boolean;
}

export const ChatHistoryScreen = ({ isActive }: ChatHistoryScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);

  const goBackFromHistory = () => {
    // TODO: Implement navigation to previous screen
    setScreen('generalVoice');
  };

  const createNewChat = () => {
    // TODO: Implement new chat creation
    console.log('Creating new chat');
  };

  const openChat = (chatId: number) => {
    // TODO: Load specific chat
    console.log('Opening chat:', chatId);
    setScreen('chat');
  };

  const startVoiceInput = () => {
    // TODO: Implement voice input
    console.log('Starting voice input');
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
        <div className="history-group">
          <h4 className="history-date">Сегодня</h4>
          <div className="history-item" onClick={() => openChat(1)}>Как справляться со стрессом</div>
          <div className="history-item" onClick={() => openChat(2)}>Проблемы на работе</div>
        </div>

        <div className="history-group">
          <h4 className="history-date">Вчера</h4>
          <div className="history-item" onClick={() => openChat(3)}>Поссорились с парнем</div>
        </div>
      </div>

      <div className="chat-bottom-panel" style={{display: 'none'}}>
        <button className="chat-new-btn" onClick={createNewChat}>+</button>
        <input type="text" className="chat-quick-input" placeholder="Чем я могу помочь?" />
        <button className="chat-mic-btn" onClick={startVoiceInput}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" fill="#E8F0FE"/>
            <path d="M12 15c1.66 0 3-1.34 3-3V6c0-1.66-1.34-3-3-3S9 4.34 9 6v6c0 1.66 1.34 3 3 3z" fill="#4A90E2"/>
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" fill="#4A90E2"/>
          </svg>
        </button>
      </div>
    </div>
  );
};
