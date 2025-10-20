import { useAppStore } from '../../stores/useAppStore';

interface AnalysisVoiceScreenProps {
  isActive: boolean;
}

export const AnalysisVoiceScreen = ({ isActive }: AnalysisVoiceScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);

  const createNewChat = () => {
    // TODO: Implement new chat creation
    console.log('Creating new chat');
  };

  const toggleAnalysisVoiceRecording = () => {
    // TODO: Implement voice recording
    console.log('Toggle analysis voice recording');
  };

  return (
    <div className={`screen voice-chat-screen ${isActive ? 'active' : ''}`} id="analysis-voice-screen">
      <div className="voice-header">
        <div className="voice-left-controls">
          <button className="voice-back-btn" onClick={() => setScreen('analysis')}>←</button>
          <div className="voice-multitask-icon" onClick={() => setScreen('chatHistory')}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="13" y="3" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="3" y="13" width="8" height="8" rx="2" fill="#4A90E2"/>
              <rect x="13" y="13" width="8" height="8" rx="2" fill="#4A90E2"/>
            </svg>
          </div>
        </div>
        <h1 className="voice-title" id="analysisVoiceTitle">Анализ отношений</h1>
        <div className="voice-avatar">
          <img src="/Robo.png" alt="SoulNear Assistant" />
        </div>
      </div>

      <div className="voice-messages" id="analysisVoiceMessages">
        {/* Голосовые сообщения анализа будут добавляться здесь */}
      </div>

      <div className="voice-bottom-controls">
        <button className="voice-add-btn" onClick={createNewChat}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 4V16M4 10H16" stroke="#4A90E2" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </button>
        <button className="voice-mic-btn" onClick={toggleAnalysisVoiceRecording}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14Z" fill="white"/>
            <path d="M19 11C19 14.53 16.39 17.44 13 17.93V21H11V17.93C7.61 17.44 5 14.53 5 11H7C7 13.76 9.24 16 12 16C14.76 16 17 13.76 17 11H19Z" fill="white"/>
          </svg>
        </button>
        <button className="voice-keyboard-btn" onClick={() => setScreen('analysisChat')}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <rect x="2" y="6" width="16" height="10" rx="2" stroke="#4A90E2" strokeWidth="1.5" fill="none"/>
            <rect x="4" y="8" width="1.5" height="1.5" rx="0.5" fill="#4A90E2"/>
            <rect x="6.5" y="8" width="1.5" height="1.5" rx="0.5" fill="#4A90E2"/>
            <rect x="9" y="8" width="1.5" height="1.5" rx="0.5" fill="#4A90E2"/>
            <rect x="11.5" y="8" width="1.5" height="1.5" rx="0.5" fill="#4A90E2"/>
            <rect x="14" y="8" width="1.5" height="1.5" rx="0.5" fill="#4A90E2"/>
            <rect x="5" y="11" width="1.5" height="1.5" rx="0.5" fill="#4A90E2"/>
            <rect x="7.5" y="11" width="5" height="1.5" rx="0.5" fill="#4A90E2"/>
            <rect x="13.5" y="11" width="1.5" height="1.5" rx="0.5" fill="#4A90E2"/>
          </svg>
        </button>
      </div>
    </div>
  );
};
