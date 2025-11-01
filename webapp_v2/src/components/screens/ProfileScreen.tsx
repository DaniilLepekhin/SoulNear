import { useEffect, useState } from 'react';
import { useAppStore } from '../../stores/useAppStore';
import { api } from '../../services/api';

interface ProfileScreenProps {
  isActive: boolean;
}

interface UserSubscription {
  is_subscribed: boolean;
  subscription_end_date: string | null;
}

export const ProfileScreen = ({ isActive }: ProfileScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);
  const user = useAppStore((state) => state.user);
  const [subscription, setSubscription] = useState<UserSubscription | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTelegramAvatar();
    if (user) {
      loadSubscriptionInfo();
    }
  }, [user]);

  const loadTelegramAvatar = () => {
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user) {
      const telegramUser = window.Telegram.WebApp.initDataUnsafe.user;
      if (telegramUser.photo_url) {
        const img = document.getElementById('profile-avatar-img') as HTMLImageElement;
        const placeholder = document.getElementById('profile-avatar-placeholder');
        if (img && placeholder) {
          img.src = telegramUser.photo_url;
          img.style.display = 'block';
          placeholder.style.display = 'none';
        }
      }
    }
  };

  const loadSubscriptionInfo = async () => {
    if (!user) return;

    setLoading(true);
    const result = await api.getUserInfo(user.id);
    if (result.success && result.data) {
      setSubscription({
        is_subscribed: result.data.is_subscribed,
        subscription_end_date: result.data.subscription_end_date
      });
    }
    setLoading(false);
  };

  const showHelp = () => {
    if (window.Telegram && window.Telegram.WebApp) {
      window.open('https://telegra.ph/FAQ-dlya-bota-SOULnear-10-22', '_blank');
    }
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

          {/* Subscription Status */}
          {loading ? (
            <div className="subscription-status loading">
              <span>Загрузка...</span>
            </div>
          ) : subscription ? (
            <div className={`subscription-status ${subscription.is_subscribed ? 'active' : 'inactive'}`}>
              {subscription.is_subscribed ? (
                <>
                  <div className="subscription-badge">✓ Подписка активна</div>
                  <div className="subscription-date">до {subscription.subscription_end_date}</div>
                </>
              ) : (
                <>
                  <div className="subscription-badge">✗ Подписка не активна</div>
                  <div className="subscription-hint">Активируйте для полного доступа</div>
                </>
              )}
            </div>
          ) : null}

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
