import { useAppStore } from '../../stores/useAppStore';

interface OnboardingScreenProps {
  isActive: boolean;
}

export const OnboardingScreen = ({ isActive }: OnboardingScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);

  const handleContinue = () => {
    setScreen('main');
  };

  return (
    <div className={`screen security-screen ${isActive ? 'active' : ''}`}>
      <div className="lock-container">
        <img src="/lock.png" alt="Security Lock" className="lock-image" />
      </div>
      <div className="security-title">
        <h2>Безопасность<br />наш приоритет</h2>
        <p>Все ваши диалоги с Soul Near защищены, приватны и не передаются третьим лицам.</p>
      </div>
      <button className="continue-btn" onClick={handleContinue}>
        Продолжить
      </button>
    </div>
  );
};
