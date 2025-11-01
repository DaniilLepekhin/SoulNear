import { useAppStore } from '../../stores/useAppStore';

interface VoiceChatScreenProps {
  isActive: boolean;
}

export const VoiceChatScreen = ({ isActive }: VoiceChatScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);

  const selectAgent = (agentType: string) => {
    if (agentType === 'general') {
      setScreen('generalVoice');
    } else if (agentType === 'analysis') {
      setScreen('analysis');
    } else if (agentType === 'dreams') {
      setScreen('dreamsChat');
    }
  };

  return (
    <div className={`screen agent-selection-screen ${isActive ? 'active' : ''}`}>
      <div className="voice-header">
        <div className="voice-left-controls">
          <button className="voice-back-btn" onClick={() => setScreen('main')}>←</button>
        </div>
        <h1 className="voice-title">Выбери помощника</h1>
        <div className="voice-avatar">
          <img src="/Robo.png" alt="SoulNear" />
        </div>
      </div>

      <div className="agent-description">
        <p>С чем тебе помочь сегодня? Выбери тему для работы:</p>
      </div>

      <div className="agent-cards">
        <div className="agent-card general" onClick={() => selectAgent('general')}>
          <div className="agent-card-icon">💬</div>
          <div className="agent-card-content">
            <h3>Общение с Soul.near</h3>
            <p>Поддержка, советы, разговор на любые темы</p>
          </div>
        </div>

        <div className="agent-card analysis" onClick={() => selectAgent('analysis')}>
          <div className="agent-card-icon">👤</div>
          <div className="agent-card-content">
            <h3>Анализ личности</h3>
            <p>Разбор отношений, денег, страхов и уверенности</p>
          </div>
        </div>

        <div className="agent-card dreams" onClick={() => selectAgent('dreams')}>
          <div className="agent-card-icon">💤</div>
          <div className="agent-card-content">
            <h3>Работа со снами</h3>
            <p>Анализ и толкование твоих снов</p>
          </div>
        </div>
      </div>

      {/* Bottom Navigation */}
      <div className="bottom-nav">
        <div className="nav-item" onClick={() => setScreen('main')}>
          <div className="nav-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" fill="currentColor"/>
            </svg>
          </div>
        </div>
        <div className="nav-item active" onClick={() => setScreen('voiceChat')}>
          <div className="nav-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z" fill="currentColor"/>
            </svg>
          </div>
        </div>
        <div className="nav-item" onClick={() => setScreen('practices')}>
          <div className="nav-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M6 6h4v4H6V6zm0 8h4v4H6v-4zm8-8h4v4h-4V6zm0 8h4v4h-4v-4z" fill="currentColor"/>
            </svg>
          </div>
        </div>
        <div className="nav-item" onClick={() => setScreen('profile')}>
          <div className="nav-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v1c0 .55.45 1 1 1h14c.55 0 1-.45 1-1v-1c0-2.66-5.33-4-8-4z" fill="currentColor"/>
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};
