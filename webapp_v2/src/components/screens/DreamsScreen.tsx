import { useAppStore } from '../../stores/useAppStore';
import { telegram } from '../../services/telegram';

interface DreamsScreenProps {
  isActive: boolean;
}

export const DreamsScreen = ({ isActive }: DreamsScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);

  const startDream = () => {
    telegram.haptic('light');
    setScreen('dreamsChat');
  };

  return (
    <div className={`screen voice-chat-screen ${isActive ? 'active' : ''}`} id="dreams-screen">
      <div className="voice-header">
        <div className="voice-left-controls">
          <button className="voice-back-btn" onClick={() => setScreen('main')}>←</button>
        </div>
        <h1 className="voice-title">Толкование снов</h1>
        <div className="voice-avatar">
          <img src="/Robo.png" alt="SoulNear" />
        </div>
      </div>

      <div className="agent-description">
        <p>Расскажите свой сон текстом или голосом, и получите его глубокий анализ</p>
      </div>

      <div className="analysis-cards">
        <div className="analysis-card" onClick={startDream}>
          <div className="analysis-icon">🌙</div>
          <h3>Анализ<br/>сна</h3>
          <p>Расскажите о вашем сне</p>
        </div>
      </div>
    </div>
  );
};
