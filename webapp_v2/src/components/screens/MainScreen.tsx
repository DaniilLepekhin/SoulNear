import { useEffect, useRef, useState } from 'react';
import { useAppStore } from '../../stores/useAppStore';
import { api } from '../../services/api';
import { telegram } from '../../services/telegram';

interface MainScreenProps {
  isActive: boolean;
}

interface MoodData {
  date: string;
  mood_value: number;
  emoji: string;
}

export const MainScreen = ({ isActive }: MainScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);
  const user = useAppStore((state) => state.user);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [greeting, setGreeting] = useState('');
  const [currentMonth, setCurrentMonth] = useState('');
  const [moodHistory, setMoodHistory] = useState<MoodData[]>([]);
  const [selectedMood, setSelectedMood] = useState<number | null>(null);
  const [calendarDays, setCalendarDays] = useState<any[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>(''); // Выбранная дата для установки настроения

  useEffect(() => {
    if (!isActive || !user) return;

    // Update month
    const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
    const now = new Date();
    setCurrentMonth(months[now.getMonth()]);

    // Update greeting
    const hour = now.getHours();
    let greetingText;
    if (hour < 6) greetingText = 'Доброй ночи';
    else if (hour < 12) greetingText = 'Доброе утро';
    else if (hour < 18) greetingText = 'Добрый день';
    else greetingText = 'Добрый вечер';

    const userName = user?.firstName || 'Пользователь';
    setGreeting(`${greetingText}, ${userName}!`);

    // Load mood history
    loadMoodHistory();
    generateCalendar();
  }, [isActive, user]);

  useEffect(() => {
    if (moodHistory.length > 0) {
      drawMoodChart();
    }
  }, [moodHistory]);

  const loadMoodHistory = async () => {
    if (!user) return;
    try {
      const response = await api.getMoodHistory(user.id, 30);
      if (response.success && response.data) {
        setMoodHistory(response.data as MoodData[]);
      }
    } catch (error) {
      console.error('Failed to load mood history:', error);
    }
  };

  const generateCalendar = () => {
    const now = new Date();
    const days = [];
    const todayStr = now.toISOString().split('T')[0];
    for (let i = 5; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      days.push({
        day: date.getDate(),
        date: dateStr,
        isToday: i === 0
      });
    }
    setCalendarDays(days);
    setSelectedDate(todayStr); // По умолчанию выбран сегодняшний день
  };

  const handleDayClick = (date: string) => {
    setSelectedDate(date);
    telegram.haptic('light');

    // Найти настроение для выбранного дня и показать его
    const dayMood = moodHistory.find(m => m.date === date);
    if (dayMood) {
      setSelectedMood(dayMood.mood_value);
    } else {
      setSelectedMood(null);
    }
  };

  const handleMoodSelect = async (moodValue: number, emoji: string) => {
    if (!user || !selectedDate) return;

    setSelectedMood(moodValue);
    telegram.haptic('light');

    try {
      await api.saveMood(user.id, selectedDate, moodValue, emoji);
      telegram.hapticSuccess();
      await loadMoodHistory();
    } catch (error) {
      console.error('Failed to save mood:', error);
      telegram.hapticError();
    }
  };

  const drawMoodChart = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.setTransform(1,0,0,1,0,0);
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const width = rect.width;
    const height = rect.height;

    ctx.clearRect(0, 0, width, height);

    // Grid - рисуем всегда
    ctx.strokeStyle = '#E3F2FD';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 10; i++) {
        const x = (width / 10) * i;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
    }
    for (let i = 0; i <= 5; i++) {
        const y = (height / 5) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }

    // Get last 7 days of mood data
    const last7Days = moodHistory.slice(-7);
    if (last7Days.length === 0) {
      // No data yet, show placeholder
      ctx.fillStyle = '#B0BEC5';
      ctx.font = '14px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText('Начните отмечать настроение', width / 2, height / 2);
      return;
    }

    const moodData = last7Days.map(m => ({
      time: m.date,
      value: m.mood_value / 5 // Normalize to 0-1
    }));

    // Smooth line
    const points = moodData.map((p, i) => ({
      x: moodData.length === 1 ? width / 2 : (width / (moodData.length - 1)) * i,
      y: height - (p.value * height)
    }));

    ctx.strokeStyle = '#1976D2';
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';

    // Рисуем линию только если точек больше одной
    if (points.length > 1) {
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);

      if (points.length === 2) {
        // Для двух точек - простая линия
        ctx.lineTo(points[1].x, points[1].y);
      } else {
        // Для трёх и более - плавная кривая через Bezier, которая проходит через точки
        for (let i = 0; i < points.length - 1; i++) {
          const p0 = points[i];
          const p1 = points[i + 1];

          // Вычисляем контрольные точки для плавной кривой
          const cp1x = p0.x + (p1.x - p0.x) / 3;
          const cp1y = p0.y + (p1.y - p0.y) / 3;
          const cp2x = p0.x + 2 * (p1.x - p0.x) / 3;
          const cp2y = p0.y + 2 * (p1.y - p0.y) / 3;

          ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p1.x, p1.y);
        }
      }

      ctx.stroke();
    }

    // Points
    points.forEach(point => {
      ctx.beginPath();
      ctx.fillStyle = '#FFFFFF';
      ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#1976D2';
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  };

  return (
    <div className={`screen main-screen ${isActive ? 'active' : ''}`}>
      <div className="main-container">
        {/* Calendar Section */}
        <div className="calendar-section">
          <div className="month-label">{currentMonth}</div>
          <div className="calendar-container">
            <div className="calendar-days">
              {calendarDays.map((day) => {
                const dayMood = moodHistory.find(m => m.date === day.date);
                const isSelected = day.date === selectedDate;
                return (
                  <div
                    key={day.date}
                    className={`calendar-day ${dayMood ? 'completed' : ''} ${day.isToday ? 'active' : ''} ${isSelected ? 'selected' : ''}`}
                    data-day={day.day}
                    onClick={() => handleDayClick(day.date)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="day-circle">
                      <span className="day-number">{day.day}</span>
                    </div>
                    <span className="day-badge">{dayMood ? dayMood.emoji : '➕'}</span>
                  </div>
                );
              })}
            </div>
            <div className="calendar-indicators">
              {calendarDays.map((day) => {
                const dayMood = moodHistory.find(m => m.date === day.date);
                return dayMood ? (
                  <div key={day.date} className={`day-indicator ${day.isToday ? 'active' : ''}`} data-day={day.day}></div>
                ) : (
                  <div key={day.date} className="day-indicator-placeholder" data-day={day.day}></div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Greeting Section */}
        <div className="greeting-section">
          <h2>{greeting}</h2>
          <p>Сегодня 24-й день вашего путешествия!</p>
        </div>

        {/* Mood Section with Chart */}
        <div className="mood-section">
          <div className="mood-header">
            <span>
              {selectedDate === new Date().toISOString().split('T')[0]
                ? 'Как ты себя чувствуешь сегодня?'
                : `Как ты себя чувствовал ${selectedDate.split('-')[2]} числа?`}
            </span>
            <div className="mood-profile-icon">
              <img src="/icons_people.png" alt="Profile Icon" width="24" height="24" />
            </div>
          </div>
          <div className="mood-selector">
            <div
              className={`mood-emoji ${selectedMood === 5 ? 'selected' : ''}`}
              onClick={() => handleMoodSelect(5, '😂')}
            >
              😂
            </div>
            <div
              className={`mood-emoji ${selectedMood === 4 ? 'selected' : ''}`}
              onClick={() => handleMoodSelect(4, '🤩')}
            >
              🤩
            </div>
            <div
              className={`mood-emoji ${selectedMood === 3 ? 'selected' : ''}`}
              onClick={() => handleMoodSelect(3, '😐')}
            >
              😐
            </div>
            <div
              className={`mood-emoji ${selectedMood === 2 ? 'selected' : ''}`}
              onClick={() => handleMoodSelect(2, '😔')}
            >
              😔
            </div>
            <div
              className={`mood-emoji ${selectedMood === 1 ? 'selected' : ''}`}
              onClick={() => handleMoodSelect(1, '🤯')}
            >
              🤯
            </div>
          </div>
          <div className="chart-container">
            <canvas ref={canvasRef} id="moodChart" width="320" height="180"></canvas>
          </div>
          <div className="chart-dates">
            {moodHistory.slice(-7).map((mood, idx) => (
              <span key={idx}>{new Date(mood.date).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Navigation */}
      <div className="bottom-nav">
        <div className="nav-item active" onClick={() => setScreen('main')}>
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
        <div className="nav-item" onClick={() => setScreen('profile')}>
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
