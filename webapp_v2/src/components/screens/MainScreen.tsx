import { useEffect, useRef, useState } from 'react';
import { useAppStore } from '../../stores/useAppStore';

interface MainScreenProps {
  isActive: boolean;
}

export const MainScreen = ({ isActive }: MainScreenProps) => {
  const setScreen = useAppStore((state) => state.setScreen);
  const user = useAppStore((state) => state.user);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [greeting, setGreeting] = useState('');
  const [currentMonth, setCurrentMonth] = useState('');

  useEffect(() => {
    if (!isActive) return;
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
    
    const userName = user?.firstName || 'Аня';
    setGreeting(`${greetingText}, ${userName}!`);

    // Draw mood chart
    drawMoodChart();
  }, [isActive, user]);

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

    const moodData = [
        { time: 21.04, value: 0.3 },
        { time: 22.04, value: 0.5 },
        { time: 23.04, value: 0.4 },
        { time: 24.04, value: 0.6 },
        { time: 25.04, value: 0.8 },
        { time: 26.04, value: 0.7 },
        { time: 27.04, value: 0.9 },
        { time: 28.04, value: 0.8 },
        { time: 29.04, value: 0.6 },
        { time: 30.04, value: 0.7 }
    ];

    // Grid
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

    // Smooth line
    const points = moodData.map((p, i) => ({ 
      x: (width / (moodData.length - 1)) * i, 
      y: height - (p.value * height) 
    }));
    
    ctx.strokeStyle = '#1976D2';
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';

    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    
    for (let i = 1; i < points.length - 1; i++) {
      const xc = (points[i].x + points[i + 1].x) / 2;
      const yc = (points[i].y + points[i + 1].y) / 2;
      ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
    }
    
    ctx.quadraticCurveTo(points[points.length - 2].x, points[points.length - 2].y, 
                         points[points.length - 1].x, points[points.length - 1].y);
    ctx.stroke();

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
              <div className="calendar-day completed" data-day="4">
                <div className="day-circle">
                  <span className="day-number">4</span>
                </div>
                <span className="day-badge">😊</span>
              </div>
              <div className="calendar-day completed" data-day="5">
                <div className="day-circle">
                  <span className="day-number">5</span>
                </div>
                <span className="day-badge">😐</span>
              </div>
              <div className="calendar-day active" data-day="6">
                <div className="day-circle">
                  <span className="day-number">6</span>
                </div>
                <span className="day-badge">➕</span>
              </div>
              <div className="calendar-day" data-day="7">
                <div className="day-circle">
                  <span className="day-number">7</span>
                </div>
                <span className="day-badge">➕</span>
              </div>
              <div className="calendar-day" data-day="8">
                <div className="day-circle">
                  <span className="day-number">8</span>
                </div>
                <span className="day-badge">➕</span>
              </div>
              <div className="calendar-day" data-day="9">
                <div className="day-circle">
                  <span className="day-number">9</span>
                </div>
                <span className="day-badge">➕</span>
              </div>
            </div>
            <div className="calendar-indicators">
              <div className="day-indicator" data-day="4"></div>
              <div className="day-indicator" data-day="5"></div>
              <div className="day-indicator active" data-day="6"></div>
              <div className="day-indicator-placeholder" data-day="7"></div>
              <div className="day-indicator-placeholder" data-day="8"></div>
              <div className="day-indicator-placeholder" data-day="9"></div>
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
            <span>Как ты себя чувствуешь сегодня?</span>
            <div className="mood-profile-icon">
              <img src="/icons_people.png" alt="Profile Icon" width="24" height="24" />
            </div>
          </div>
          <div className="mood-selector">
            <div className="mood-emoji">😂</div>
            <div className="mood-emoji">🤩</div>
            <div className="mood-emoji">😐</div>
            <div className="mood-emoji">😔</div>
            <div className="mood-emoji">🤯</div>
          </div>
          <div className="chart-container">
            <canvas ref={canvasRef} id="moodChart" width="320" height="180"></canvas>
          </div>
          <div className="chart-dates">
            <span>24.04</span>
            <span>25.04</span>
            <span>26.04</span>
            <span>27.04</span>
            <span>28.04</span>
            <span>29.04</span>
            <span>30.04</span>
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
