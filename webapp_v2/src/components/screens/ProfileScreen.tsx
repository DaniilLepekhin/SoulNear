import { useEffect } from 'react';
import { useAppStore } from '../../stores/useAppStore';

interface ProfileScreenProps {
  isActive: boolean;
}

export const ProfileScreen = ({ isActive }: ProfileScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);

  useEffect(() => {
    loadTelegramAvatar();
  }, []);

  const loadTelegramAvatar = () => {
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user) {
      const user = window.Telegram.WebApp.initDataUnsafe.user;
      if (user.photo_url) {
        const img = document.getElementById('profile-avatar-img') as HTMLImageElement;
        const placeholder = document.getElementById('profile-avatar-placeholder');
        if (img && placeholder) {
          img.src = user.photo_url;
          img.style.display = 'block';
          placeholder.style.display = 'none';
        }
      }
    }
  };

  const showHelp = () => {
    // TODO: Implement help screen
    console.log('Show help');
  };

  const showSupport = () => {
    // TODO: Implement support screen
    console.log('Show support');
  };

  return (
    <div className={`screen profile-screen ${isActive ? 'active' : ''}`} id="profile-screen">
      <div className="profile-header">
        <h2 className="profile-title">Профиль</h2>
      </div>

      <div className="profile-content">
        <div className="profile-card">
          <div className="profile-avatar-container">
            <div className="profile-avatar" id="profile-avatar">
              <img id="profile-avatar-img" style={{display: 'none'}} alt="Avatar" />
              <svg id="profile-avatar-placeholder" width="60" height="60" viewBox="0 0 24 24" fill="none">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v1c0 .55.45 1 1 1h14c.55 0 1-.45 1-1v-1c0-2.66-5.33-4-8-4z" fill="#4A90E2"/>
              </svg>
            </div>
          </div>
          <div className="achievement-grid">
            <div className="achievement-slot">
              <div className="achievement-placeholder"></div>
            </div>
            <div className="achievement-slot">
              <div className="achievement-placeholder"></div>
            </div>
          </div>
        </div>

        <div className="profile-menu-block">
          <div className="profile-menu-item" onClick={showHelp}>
            <div className="menu-item-left">
              <div className="menu-item-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="#4A90E2" strokeWidth="2"/>
                  <path d="M12 16v-1m0-3c0-1 1-2 2-2.5C15 9 15 8 14 7c-1.5-1.5-4-.5-4 1.5" stroke="#4A90E2" strokeWidth="2" strokeLinecap="round"/>
                  <circle cx="12" cy="19" r="1" fill="#4A90E2"/>
                </svg>
              </div>
              <span className="menu-item-text">Помощь</span>
            </div>
            <div className="menu-arrow">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M9 6L15 12L9 18" stroke="#CBD5E0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </div>
          <div className="profile-menu-item" onClick={showSupport}>
            <div className="menu-item-left">
              <div className="menu-item-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z" fill="#4A90E2"/>
                </svg>
              </div>
              <span className="menu-item-text">Поддержка Soul Near</span>
            </div>
            <div className="menu-arrow">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M9 6L15 12L9 18" stroke="#CBD5E0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <div className="bottom-nav">
        <div className="nav-item" onClick={() => setScreen('main')}>
          <div className="nav-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" fill="currentColor"/>
            </svg>
          </div>
        </div>
        <div className="nav-item" onClick={() => setScreen('voiceChat')}>
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
        <div className="nav-item active" onClick={() => setScreen('profile')}>
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
