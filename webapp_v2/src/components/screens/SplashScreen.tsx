import { useEffect } from 'react';
import { useAppStore } from '../../stores/useAppStore';

interface SplashScreenProps {
  isActive: boolean;
}

export const SplashScreen = ({ isActive }: SplashScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);

  useEffect(() => {
    if (isActive) {
      const timer = setTimeout(() => {
        setScreen('onboarding');
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isActive, setScreen]);

  return (
    <div className={`screen splash-screen ${isActive ? 'active' : ''}`}>
      <img src="/robot.png" alt="SoulNear Robot" className="robot-image" />
      <div className="splash-title">
        <h1>SoulNear</h1>
        <p>Твой путь к совершенству</p>
      </div>
      <div className="splash-footer">
        <p>© 2025 SoulNear</p>
      </div>
    </div>
  );
};
