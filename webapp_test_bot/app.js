// Global state
let currentScreen = 'splash-screen';
let isRecording = false;
let selectedMood = null;
let chatMessages = [];

// Initialize Telegram WebApp
if (window.Telegram && window.Telegram.WebApp) {
    window.Telegram.WebApp.ready();
    window.Telegram.WebApp.expand();
    window.Telegram.WebApp.setHeaderColor('#E3F2FD');
    window.Telegram.WebApp.setBackgroundColor('#E3F2FD');
}

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    drawMoodChart();
});

function initializeApp() {
    // Show splash screen for 3 seconds then go to onboarding
    setTimeout(() => {
        showScreen('onboarding-screen');
    }, 3000);
}

function setupEventListeners() {
    // Add touch feedback and animations
    document.querySelectorAll('button, .mood-btn, .option-card, .practice-card, .nav-item, .day-item, .history-item').forEach(element => {
        element.addEventListener('click', addRippleEffect);

        element.addEventListener('touchstart', function() {
            this.style.transform = this.style.transform.includes('scale') ?
                this.style.transform.replace(/scale\([^)]*\)/, 'scale(0.95)') :
                this.style.transform + ' scale(0.95)';
        });

        element.addEventListener('touchend', function() {
            setTimeout(() => {
                this.style.transform = this.style.transform.replace(/scale\([^)]*\)/, '');
            }, 150);
        });
    });

    // Chat input handling
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }

    // Voice recording button long press
    const voiceButtons = document.querySelectorAll('.voice-btn, .voice-record-btn');
    voiceButtons.forEach(btn => {
        let pressTimer;

        btn.addEventListener('touchstart', function(e) {
            e.preventDefault();
            pressTimer = setTimeout(() => {
                startVoiceRecording();
            }, 200);
        });

        btn.addEventListener('touchend', function(e) {
            e.preventDefault();
            clearTimeout(pressTimer);
            if (isRecording) {
                stopVoiceRecording();
            }
        });
    });
}

function addRippleEffect(e) {
    const button = e.currentTarget;
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;

    ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
        z-index: 100;
    `;

    button.style.position = 'relative';
    button.style.overflow = 'hidden';
    button.appendChild(ripple);

    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// Add ripple animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple-animation {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Screen navigation with smooth transitions
function showScreen(screenId) {
    const currentScreenEl = document.querySelector('.screen.active');
    const targetScreenEl = document.getElementById(screenId);

    if (!targetScreenEl) return;

    // Hide current screen
    if (currentScreenEl) {
        currentScreenEl.classList.remove('active');
    }

    // Show target screen with animation
    setTimeout(() => {
        targetScreenEl.classList.add('active');
        currentScreen = screenId;

        // Update navigation state
        updateNavigation(screenId);

        // Trigger screen-specific initializations
        onScreenShow(screenId);
    }, 100);
}

function updateNavigation(screenId) {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });

    // Map screens to navigation items
    const navMapping = {
        'main-screen': 0,
        'daily-plan-screen': 0,
        'voice-chat-screen': 1,
        'practices-screen': 2,
        'practice-player-screen': 2,
        'profile-screen': 3
    };

    const navIndex = navMapping[screenId];
    if (navIndex !== undefined) {
        const navItems = document.querySelectorAll('.nav-item');
        if (navItems[navIndex]) {
            navItems[navIndex].classList.add('active');
        }
    }
}

function onScreenShow(screenId) {
    switch(screenId) {
        case 'main-screen':
            drawMoodChart();
            break;
        case 'practice-player-screen':
            startBreathingAnimation();
            break;
        case 'voice-assistant-screen':
            startOrbAnimation();
            break;
    }
}

// Update navigation active states
function updateNavigation(activeScreen) {
    // Remove active class from all nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });

    // Add active class to current nav item based on screen
    let activeNavSelector = '';
    switch(activeScreen) {
        case 'main-screen':
            activeNavSelector = '.nav-item[onclick="showMainScreen()"]';
            break;
        case 'voice-chat-screen':
            activeNavSelector = '.nav-item[onclick="showVoiceChat()"]';
            break;
        case 'practices-screen':
            activeNavSelector = '.nav-item[onclick="showPractices()"]';
            break;
        case 'profile-screen':
            activeNavSelector = '.nav-item[onclick="showProfile()"]';
            break;
    }

    if (activeNavSelector) {
        document.querySelectorAll(activeNavSelector).forEach(item => {
            item.classList.add('active');
        });
    }
}

// Main navigation functions
function showMainScreen() {
    showScreen('main-screen');
    updateNavigation('main-screen');
}

function showVoiceChat() {
    showScreen('voice-chat-screen');
    updateNavigation('voice-chat-screen');
}


function showPractices() {
    showScreen('practices-screen');
    updateNavigation('practices-screen');
}

function showProfile() {
    showScreen('profile-screen');
    updateNavigation('profile-screen');
}

function showChat() {
    showScreen('chat-screen');
}

function showVoiceChat() {
    showScreen('voice-chat-screen');
}

function showChatHistory() {
    showScreen('chat-history-screen');
}

function showDailyPlan() {
    showScreen('daily-plan-screen');
}

function showDreamAnalysis() {
    showScreen('chat-screen');
    setTimeout(() => {
        addChatMessage("Расскажите мне о своем сне, и я помогу его проанализировать", 'assistant');
    }, 500);
}

function showPersonalityAnalysis() {
    showScreen('chat-screen');
    setTimeout(() => {
        addChatMessage("Давайте проведем анализ личности. Ответьте на несколько вопросов о себе", 'assistant');
    }, 500);
}

// Mood selection
function selectMood(mood) {
    selectedMood = mood;

    // Update mood buttons visual feedback
    document.querySelectorAll('.mood-btn').forEach(btn => {
        btn.classList.remove('selected');
    });

    // Find and highlight selected mood button
    const selectedBtn = document.querySelector(`[data-mood="${mood}"]`);
    if (selectedBtn) {
        selectedBtn.classList.add('selected');
    }

    // Send mood data to Telegram WebApp
    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.sendData(JSON.stringify({
            action: 'mood_selected',
            mood: mood,
            timestamp: new Date().toISOString()
        }));
    }

    showMoodFeedback(mood);
}

function showMoodFeedback(mood) {
    const feedback = document.createElement('div');
    feedback.textContent = `Настроение ${mood} сохранено!`;
    feedback.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(21, 101, 192, 0.9);
        color: white;
        padding: 15px 30px;
        border-radius: 25px;
        z-index: 1000;
        animation: fadeInOut 2s ease-in-out;
        backdrop-filter: blur(10px);
    `;

    document.body.appendChild(feedback);

    setTimeout(() => {
        feedback.remove();
    }, 2000);
}

// Calendar functionality
function selectDay(dayNumber) {
    // Update active day
    document.querySelectorAll('.day-item').forEach(day => {
        day.classList.remove('active');
    });

    event.target.closest('.day-item').classList.add('active');

    // Show daily plan for selected day
    setTimeout(() => {
        showDailyPlan();
    }, 300);
}

// Chat functionality
function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (message) {
        addChatMessage(message, 'user');
        input.value = '';

        // Send message data to Telegram WebApp
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.sendData(JSON.stringify({
                action: 'chat_message',
                message: message,
                timestamp: new Date().toISOString()
            }));
        }

        // Simulate assistant response
        setTimeout(() => {
            simulateAssistantResponse(message);
        }, 1000);
    }
}

function addChatMessage(message, type) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;

    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}`;

    const contentElement = document.createElement('div');
    contentElement.className = 'message-content';

    if (type === 'assistant' && message.includes('\n')) {
        // Handle multi-line messages
        const paragraphs = message.split('\n').filter(p => p.trim());
        paragraphs.forEach(paragraph => {
            const p = document.createElement('p');
            p.textContent = paragraph;
            contentElement.appendChild(p);
        });
    } else {
        const p = document.createElement('p');
        p.textContent = message;
        contentElement.appendChild(p);
    }

    messageElement.appendChild(contentElement);
    messagesContainer.appendChild(messageElement);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Add fade-in animation
    messageElement.classList.add('fade-in');
}

function simulateAssistantResponse(userMessage) {
    const responses = [
        "Понимаю твои чувства. Расскажи больше о том, что тебя беспокоит.",
        "Это важный шаг - обратиться за поддержкой. Как ты себя чувствуешь прямо сейчас?",
        "Давай разберем эту ситуацию вместе. Что для тебя сейчас самое важное?",
        "Твои эмоции абсолютно нормальны. Хочешь поговорить о том, что привело к этому состоянию?",
        "Я здесь, чтобы тебя поддержать. Что бы ты хотел изменить в своей жизни?"
    ];

    const randomResponse = responses[Math.floor(Math.random() * responses.length)];
    addChatMessage(randomResponse, 'assistant');
}

// Voice functionality
function startVoiceRecording() {
    if (isRecording) return;

    isRecording = true;

    // Update UI
    const voiceButtons = document.querySelectorAll('.voice-btn, .voice-record-btn');
    voiceButtons.forEach(btn => {
        btn.classList.add('recording');
    });

    // Show recording animation
    showRecordingAnimation();

    // Haptic feedback
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
    }

    console.log('Voice recording started...');
}

function stopVoiceRecording() {
    if (!isRecording) return;

    isRecording = false;

    // Update UI
    const voiceButtons = document.querySelectorAll('.voice-btn, .voice-record-btn');
    voiceButtons.forEach(btn => {
        btn.classList.remove('recording');
    });

    // Hide recording animation
    hideRecordingAnimation();

    // Send voice data to Telegram WebApp
    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.sendData(JSON.stringify({
            action: 'voice_message',
            duration: Math.floor(Math.random() * 10) + 1, // Simulate duration
            timestamp: new Date().toISOString()
        }));
    }

    // Simulate voice message processing
    setTimeout(() => {
        if (currentScreen === 'chat-screen') {
            addChatMessage("🎤 Голосовое сообщение", 'user');
            setTimeout(() => {
                simulateAssistantResponse("voice");
            }, 500);
        }
    }, 1000);

    console.log('Voice recording stopped...');
}

function showRecordingAnimation() {
    const recordingElements = document.querySelectorAll('.orb-gradient, .voice-orb, .assistant-orb .orb-gradient');
    recordingElements.forEach(element => {
        element.classList.add('recording');
    });

    const waveElements = document.querySelectorAll('.recording-bar, .wave-bar');
    waveElements.forEach(element => {
        element.style.animationPlayState = 'running';
    });
}

function hideRecordingAnimation() {
    const recordingElements = document.querySelectorAll('.orb-gradient, .voice-orb, .assistant-orb .orb-gradient');
    recordingElements.forEach(element => {
        element.classList.remove('recording');
    });
}

// Practice functionality
function playPractice(practiceId) {
    // Send practice data to Telegram WebApp
    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.sendData(JSON.stringify({
            action: 'practice_started',
            practice_id: practiceId || 'breathing',
            timestamp: new Date().toISOString()
        }));
    }

    showScreen('practice-player-screen');
}

function startBreathingAnimation() {
    const breathingText = document.querySelector('.breathing-text');
    if (breathingText) {
        let isInhale = true;
        const breathingInterval = setInterval(() => {
            if (currentScreen !== 'practice-player-screen') {
                clearInterval(breathingInterval);
                return;
            }

            breathingText.textContent = isInhale ? 'Вдох' : 'Выдох';
            isInhale = !isInhale;
        }, 2000);
    }
}

function startOrbAnimation() {
    const orbs = document.querySelectorAll('.assistant-orb .orb-gradient');
    orbs.forEach(orb => {
        orb.classList.add('animated');
    });
}

// Mood chart drawing
function drawMoodChart() {
    const canvas = document.getElementById('moodChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const width = rect.width;
    const height = rect.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Sample mood data
    const moodData = [
        { time: '21.04', value: 0.3 },
        { time: '22.04', value: 0.5 },
        { time: '23.04', value: 0.4 },
        { time: '24.04', value: 0.6 },
        { time: '25.04', value: 0.8 },
        { time: '26.04', value: 0.7 },
        { time: '27.04', value: 0.9 },
        { time: '28.04', value: 0.8 },
        { time: '29.04', value: 0.6 },
        { time: '30.04', value: 0.7 }
    ];

    // Draw grid
    ctx.strokeStyle = '#E3F2FD';
    ctx.lineWidth = 1;

    // Vertical lines
    for (let i = 0; i <= 10; i++) {
        const x = (width / 10) * i;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
            /* AXIS LABELS */
            ctx.fillStyle = "#1565C0";
            ctx.font = "12px system-ui, -apple-system, Segoe UI, Roboto, Arial";
            ctx.textAlign = "center";
            ctx.textBaseline = "bottom";
            for (let i = 0; i < moodData.length; i++) {
                const x = (width / (moodData.length - 1)) * i;
                const label = moodData[i].time;
                ctx.fillText(label, x, height - 4);
            }
    }

    // Horizontal lines
    for (let i = 0; i <= 5; i++) {
        const y = (height / 5) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }

    // Draw mood line with smoothing
    const points = moodData.map((p, i) => ({ x: (width / (moodData.length - 1)) * i, y: height - (p.value * height) }));

    ctx.strokeStyle = "#1976D2";
    ctx.lineWidth = 2;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    ctx.beginPath();

    if (points.length) {
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length - 1; i++) {
            const xc = (points[i].x + points[i + 1].x) / 2;
            const yc = (points[i].y + points[i + 1].y) / 2;
            ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
        }
        const last = points[points.length - 1];
        ctx.quadraticCurveTo(points[points.length - 1].x, points[points.length - 1].y, last.x, last.y);
        ctx.stroke();
    }

    // No data points - just clean line
}

// Practice filters
function filterPractices(filter) {
    // Update filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    event.target.classList.add('active');

    // Send filter data to Telegram WebApp
    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.sendData(JSON.stringify({
            action: 'practice_filter',
            filter: filter,
            timestamp: new Date().toISOString()
        }));
    }

    console.log('Filter selected:', filter);
}

// Utility functions
function vibrate(pattern = [100]) {
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
    } else if ('vibrate' in navigator) {
        navigator.vibrate(pattern);
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: ${type === 'error' ? '#FF1744' : '#1565C0'};
        color: white;
        padding: 15px 30px;
        border-radius: 25px;
        z-index: 1000;
        animation: slideDown 0.3s ease-out;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideUp 0.3s ease-out';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Performance optimization
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Resize handler with debouncing
const handleResize = debounce(() => {
    drawMoodChart();
}, 250);

window.addEventListener('resize', handleResize);

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    showNotification('Произошла ошибка. Попробуйте обновить страницу.', 'error');
});

// Export functions for potential module usage
window.SoulNearApp = {
    showScreen,
    selectMood,
    sendChatMessage,
    startVoiceRecording,
    stopVoiceRecording,
    playPractice,
    filterPractices,
    vibrate,
    showNotification
};
// twemoji parse on load
document.addEventListener("DOMContentLoaded", function(){
  if (window.twemoji) {
    window.twemoji.parse(document.body, {folder: "svg", ext: ".svg"});
  }
});

// UI 2025-09-18: override drawMoodChart with smoothing
function drawMoodChart() {
    const canvas = document.getElementById("moodChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.setTransform(1,0,0,1,0,0);
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const width = rect.width;
    const height = rect.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Sample mood data
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
    ctx.strokeStyle = "#E3F2FD";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 10; i++) {
        const x = (width / 10) * i;
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
    }
    for (let i = 0; i <= 5; i++) {
        const y = (height / 5) * i;
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
    }

    // Smooth line
    const points = moodData.map((p, i) => ({ x: (width / (moodData.length - 1)) * i, y: height - (p.value * height) }));
    ctx.strokeStyle = "#1976D2";
    ctx.lineWidth = 2;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    ctx.beginPath();
    if (points.length) {
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length - 1; i++) {
            const xc = (points[i].x + points[i + 1].x) / 2;
            const yc = (points[i].y + points[i + 1].y) / 2;
            ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
        }
        const last = points[points.length - 1];
        ctx.quadraticCurveTo(points[points.length - 1].x, points[points.length - 1].y, last.x, last.y);
    }
    ctx.stroke();
}

// cache-bust 1758206594

// ========================================
// ГОЛОСОВОЙ ЧАТ - НОВАЯ ЛОГИКА ПО ТЗ
// ========================================

// Переключение записи голоса
function toggleVoiceRecording() {
    if (isRecording) {
        stopVoiceRecording();
    } else {
        startVoiceRecording();
    }
}

// Обновленная функция записи голоса
function startVoiceRecording() {
    if (isRecording) return;

    isRecording = true;

    // Обновляем UI для новой кнопки микрофона
    const micBtn = document.querySelector('.voice-mic-btn');
    if (micBtn) {
        micBtn.classList.add('recording');
    }

    // Показываем пользовательское сообщение
    showUserVoiceMessage();

    // Haptic feedback
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
    }

    console.log('Voice recording started...');
}

// Обновленная функция остановки записи
function stopVoiceRecording() {
    if (!isRecording) return;

    isRecording = false;

    // Убираем анимацию записи
    const micBtn = document.querySelector('.voice-mic-btn');
    if (micBtn) {
        micBtn.classList.remove('recording');
    }

    // Отправляем данные в Telegram WebApp
    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.sendData(JSON.stringify({
            type: 'voice_message',
            action: 'send',
            timestamp: Date.now()
        }));
    }

    console.log('Voice recording stopped.');
}

// Показать сообщение пользователя
function showUserVoiceMessage() {
    const messagesContainer = document.querySelector('.voice-messages');
    const userMessage = document.querySelector('.user-message');

    if (messagesContainer && userMessage) {
        userMessage.style.display = 'flex';
        // Прокрутка к новому сообщению
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Переключение Play/Pause для голосовых сообщений
function toggleVoicePlayback(button) {
    const isPlaying = button.innerHTML.includes('rect');

    if (isPlaying) {
        // Остановить воспроизведение - показать иконку Play
        button.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M8 5V19L19 12L8 5Z" fill="currentColor"/>
            </svg>
        `;
        stopWaveAnimation(button);
    } else {
        // Начать воспроизведение - показать иконку Pause
        button.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <rect x="6" y="4" width="4" height="16" fill="currentColor"/>
                <rect x="14" y="4" width="4" height="16" fill="currentColor"/>
            </svg>
        `;
        startWaveAnimation(button);

        // Автоматически остановить через 3 секунды (имитация)
        setTimeout(() => {
            if (button.innerHTML.includes('rect')) {
                button.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                        <path d="M8 5V19L19 12L8 5Z" fill="currentColor"/>
                    </svg>
                `;
                stopWaveAnimation(button);
            }
        }, 3000);
    }

    // Haptic feedback
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
    }
}

// Анимация волн
function startWaveAnimation(button) {
    const waveform = button.nextElementSibling;
    if (waveform) {
        const waveBars = waveform.querySelectorAll('.wave-bar');
        waveBars.forEach((bar, index) => {
            bar.style.animationDelay = `${index * 0.1}s`;
            bar.style.animationPlayState = 'running';
        });
    }
}

function stopWaveAnimation(button) {
    const waveform = button.nextElementSibling;
    if (waveform) {
        const waveBars = waveform.querySelectorAll('.wave-bar');
        waveBars.forEach(bar => {
            bar.style.animationPlayState = 'paused';
        });
    }
}

// Инициализация событий для голосового чата
function initVoiceChatEvents() {
    // Добавляем обработчики для кнопок play/pause
    document.querySelectorAll('.voice-play-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            toggleVoicePlayback(this);
        });
    });

    // Обработчик для кнопки клавиатуры (переход к текстовому чату)
    const keyboardBtn = document.querySelector('.voice-keyboard-btn');
    if (keyboardBtn) {
        keyboardBtn.addEventListener('click', function() {
            showScreen('chat-screen');
        });
    }
}

// Добавляем инициализацию при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initVoiceChatEvents();
});
