// ==========================================
// Bottom Navigation Component
// ==========================================

import { useAppStore } from '../stores/useAppStore';
import { telegram } from '../services/telegram';
import type { Screen } from '../types';

export const BottomNavigation = () => {
  const currentScreen = useAppStore((state) => state.currentScreen);
  const setScreen = useAppStore((state) => state.setScreen);

  const navItems: { screen: Screen; icon: string; label: string }[] = [
    { screen: 'main', icon: '🏠', label: 'Главная' },
    { screen: 'practices', icon: '🧘', label: 'Практики' },
    { screen: 'analysis', icon: '📊', label: 'Анализ' },
    { screen: 'profile', icon: '👤', label: 'Профиль' },
  ];

  const handleNavClick = (screen: Screen) => {
    telegram.haptic('light');
    setScreen(screen);
  };

  // Only show navigation on main screens
  const showNav = ['main', 'practices', 'analysis', 'profile'].includes(currentScreen);

  if (!showNav) return null;

  return (
    <div className="bottom-navigation">
      {navItems.map((item) => (
        <div
          key={item.screen}
          className={`nav-item ${currentScreen === item.screen ? 'active' : ''}`}
          onClick={() => handleNavClick(item.screen)}
        >
          <div className="nav-icon">{item.icon}</div>
          <div className="nav-label">{item.label}</div>
        </div>
      ))}
    </div>
  );
};
