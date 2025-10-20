// ==========================================
// Telegram WebApp Service
// ==========================================

import WebApp from '@twa-dev/sdk';

class TelegramService {
  private tg = WebApp;

  constructor() {
    this.init();
  }

  private init() {
    // Initialize Telegram WebApp
    this.tg.ready();
    this.tg.expand();

    // Set theme colors
    this.tg.setHeaderColor('#E3F2FD');
    this.tg.setBackgroundColor('#E3F2FD');
  }

  getUser() {
    const user = this.tg.initDataUnsafe?.user;
    if (!user) return null;

    return {
      id: user.id,
      firstName: user.first_name,
      lastName: user.last_name,
      username: user.username,
      photoUrl: user.photo_url,
      languageCode: user.language_code,
    };
  }

  getUserId(): number {
    return this.tg.initDataUnsafe?.user?.id || 0;
  }

  // Haptic feedback
  haptic(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft' = 'medium') {
    this.tg.HapticFeedback.impactOccurred(style);
  }

  hapticSuccess() {
    this.tg.HapticFeedback.notificationOccurred('success');
  }

  hapticError() {
    this.tg.HapticFeedback.notificationOccurred('error');
  }

  // Main Button
  showMainButton(text: string, onClick: () => void) {
    this.tg.MainButton.setText(text);
    this.tg.MainButton.onClick(onClick);
    this.tg.MainButton.show();
  }

  hideMainButton() {
    this.tg.MainButton.hide();
  }

  // Back Button
  showBackButton(onClick: () => void) {
    this.tg.BackButton.onClick(onClick);
    this.tg.BackButton.show();
  }

  hideBackButton() {
    this.tg.BackButton.hide();
  }

  // Close app
  close() {
    this.tg.close();
  }

  // Alerts
  showAlert(message: string): Promise<void> {
    return new Promise((resolve) => {
      this.tg.showAlert(message, () => resolve());
    });
  }

  showConfirm(message: string): Promise<boolean> {
    return new Promise((resolve) => {
      this.tg.showConfirm(message, (confirmed) => resolve(confirmed));
    });
  }

  // Get theme params
  getThemeParams() {
    return this.tg.themeParams;
  }

  // Check if running in Telegram
  isInTelegram(): boolean {
    return !!this.tg.initData;
  }
}

export const telegram = new TelegramService();
