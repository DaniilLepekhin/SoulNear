import { useAppStore } from '../../stores/useAppStore';

interface AnalysisScreenProps {
  isActive: boolean;
}

export const AnalysisScreen = ({ isActive }: AnalysisScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);

  const startAnalysis = (topic: string) => {
    // TODO: Set analysis topic and navigate
    console.log('Starting analysis:', topic);
    setScreen('analysisChat');
  };

  return (
    <div className={`screen voice-chat-screen ${isActive ? 'active' : ''}`} id="analysis-screen">
      <div className="voice-header">
        <div className="voice-left-controls">
          <button className="voice-back-btn" onClick={() => setScreen('main')}>←</button>
        </div>
        <h1 className="voice-title">Анализ личности</h1>
        <div className="voice-avatar">
          <img src="/Robo.png" alt="SoulNear" />
        </div>
      </div>

      <div className="agent-description">
        <p>Выбери тему для глубокого анализа:</p>
      </div>

      <div className="analysis-cards">
        <div className="analysis-card" onClick={() => startAnalysis('relationships')}>
          <div className="analysis-icon">🫂</div>
          <h3>Отношения</h3>
          <p>Разбери свои отношения с людьми</p>
        </div>

        <div className="analysis-card" onClick={() => startAnalysis('money')}>
          <div className="analysis-icon">💸</div>
          <h3>Деньги</h3>
          <p>Пойми свои отношения с деньгами</p>
        </div>

        <div className="analysis-card" onClick={() => startAnalysis('confidence')}>
          <div className="analysis-icon">😎</div>
          <h3>Уверенность</h3>
          <p>Обрети уверенность в себе</p>
        </div>

        <div className="analysis-card" onClick={() => startAnalysis('fears')}>
          <div className="analysis-icon">🦾</div>
          <h3>Страхи</h3>
          <p>Выясни истинные страхи и научись справляться</p>
        </div>
      </div>
    </div>
  );
};
