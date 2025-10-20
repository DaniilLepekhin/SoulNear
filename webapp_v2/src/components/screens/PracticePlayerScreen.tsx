import { useAppStore } from '../../stores/useAppStore';

interface PracticePlayerScreenProps {
  isActive: boolean;
}

export const PracticePlayerScreen = ({ isActive }: PracticePlayerScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);

  return (
    <div className={`screen ${isActive ? 'active' : ''}`} id="practice-player-screen">
      <div className="player-header">
        <button className="back-btn" onClick={() => setScreen('practices')}>←</button>
        <h3>Дыхание</h3>
      </div>

      <div className="player-content">
        <div className="breathing-orb">
          <img src="/bubble.png" className="bubble-image" alt="Breathing orb" />
          <div className="breathing-text">Вдох</div>
        </div>

        <div className="player-timer">1:34</div>

        <div className="player-controls">
          <button className="player-pause-btn">▶</button>
        </div>
      </div>
    </div>
  );
};
