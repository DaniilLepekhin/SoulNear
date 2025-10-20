import { useAppStore } from '../../stores/useAppStore';
import { telegram } from '../../services/telegram';

interface DreamsScreenProps {
  isActive: boolean;
}

export const DreamsScreen = ({ isActive }: DreamsScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);

  return (
    <div className={`screen dreams-screen ${isActive ? 'active' : ''}`}>
      <div className="dreams-header">
        <div className="dreams-icon">🌙</div>
        <h2>Толкование снов</h2>
        <p>Расскажите свой сон и узнайте его значение</p>
      </div>

      <div className="dreams-modes">
        <div className="mode-card" onClick={() => { telegram.haptic('light'); setScreen('dreamsChat'); }}>
          <div className="mode-icon">💬</div>
          <h3>Текстовый формат</h3>
          <p>Опишите свой сон текстом</p>
        </div>

        <div className="mode-card" onClick={() => { telegram.haptic('light'); setScreen('dreamsVoice'); }}>
          <div className="mode-icon">🎤</div>
          <h3>Голосовой формат</h3>
          <p>Расскажите сон голосом</p>
        </div>
      </div>

      <div className="dreams-tips">
        <h4>💡 Советы для лучшего толкования:</h4>
        <ul>
          <li>Опишите все детали, которые помните</li>
          <li>Укажите эмоции, которые испытывали во сне</li>
          <li>Отметьте яркие символы и образы</li>
          <li>Расскажите о контексте вашей жизни</li>
        </ul>
      </div>
    </div>
  );
};
