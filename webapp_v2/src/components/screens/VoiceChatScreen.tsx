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
      setScreen('dreams');
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
    </div>
  );
};
