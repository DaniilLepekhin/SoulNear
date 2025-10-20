import { useAppStore } from '../../stores/useAppStore';

interface AnalysisChatScreenProps {
  isActive: boolean;
}

export const AnalysisChatScreen = ({ isActive }: AnalysisChatScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);

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
        <h1 className="chat-title">Анализ отношений</h1>
        <div className="chat-avatar">
          <img src="/Robo.png" alt="SoulNear" />
        </div>
      </div>
      <div className="chat-messages"></div>
      <div className="chat-input-container">
        <button className="chat-voice-btn" onClick={() => setScreen('analysisVoice')}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14Z" fill="white"/>
            <path d="M19 11C19 14.53 16.39 17.44 13 17.93V21H11V17.93C7.61 17.44 5 14.53 5 11H7C7 13.76 9.24 16 12 16C14.76 16 17 13.76 17 11H19Z" fill="white"/>
          </svg>
        </button>
        <input type="text" placeholder="Напишите сообщение..." />
        <button className="chat-send-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" fill="white"/>
          </svg>
        </button>
      </div>
    </div>
  );
};
