// Global state
let currentScreen = 'splash-screen';
let previousScreen = null;
let isRecording = false;
let selectedMood = null;
let chatMessages = [];

// Analysis topics configuration
const analysisTopics = {
    relationships: {
        title: 'Анализ отношений',
        prompt: 'Сейчас мы наедине с твоими мыслями. Я задам тебе 10 вопросов, отвечай открыто и развернуто. По итогу тестирования, я помогу тебе лучше разобраться в твоих отношениях с людьми. 🫂\n\n<b>Пиши "Готов!"</b>',
        color: '#4A90E2'
    },
    money: {
        title: 'Анализ отношений с деньгами',
        prompt: 'Сейчас мы наедине с твоими мыслями. Я задам 10 вопросов, отвечай открыто и развернуто. В конце тестирования я помогу тебе лучше разобраться в твоих отношениях с деньгами. 💸\n\n<b>Пиши "Готов!"</b>',
        color: '#66BB6A'
    },
    confidence: {
        title: 'Анализ уверенности',
        prompt: 'Сейчас мы наедине с твоими мыслями. Я задам 10 вопросов, отвечай открыто и развернуто. В конце тестирования я помогу лучше понять себя и обрести уверенность. 😎\n\n<b>Пиши "Готов!"</b>',
        color: '#FFA726'
    },
    fears: {
        title: 'Анализ страхов',
        prompt: 'Сейчас мы наедине с твоими мыслями. Я задам 10 вопросов, отвечай открыто и развернуто. Вместе мы выясним твои истинные страхи и я научу справляться с тревожностью. 🦾\n\n<b>Пиши "Готов!"</b>',
        color: '#EF5350'
    }
};
let currentAnalysisTopic = null;

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
    // Load Telegram avatar on startup
    loadTelegramAvatar();

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

    // Analysis input handling
    const analysisInput = document.getElementById('analysisInput');
    if (analysisInput) {
        analysisInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendAnalysisMessage();
            }
        });
    }

    // Dreams input handling
    const dreamsInput = document.getElementById('dreamsInput');
    if (dreamsInput) {
        dreamsInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendDreamsMessage();
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
    console.log('showVoiceChat called - showing agent selection screen');
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
    loadTelegramAvatar();
}

function loadTelegramAvatar() {
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user) {
        const user = window.Telegram.WebApp.initDataUnsafe.user;
        if (user.photo_url) {
            const img = document.getElementById('profile-avatar-img');
            const placeholder = document.getElementById('profile-avatar-placeholder');
            if (img && placeholder) {
                img.src = user.photo_url;
                img.style.display = 'block';
                placeholder.style.display = 'none';
            }
        }
    }
}

function showHelp() {
    alert('Раздел помощи в разработке');
}

function showSupport() {
    alert('Поддержка Soul Near в разработке');
}

function showChat() {
    showScreen('chat-screen');
}

function showVoiceChat() {
    showScreen('voice-chat-screen');
}

function showChatHistory() {
    previousScreen = currentScreen;
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
async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (message) {
        addChatMessage(message, 'user');
        input.value = '';

        // Show typing indicator
        const typingIndicator = addChatMessage('Печатает...', 'assistant');
        typingIndicator.classList.add('typing-indicator');

        try {
            // Get user ID from Telegram
            let userId = 'anonymous';
            if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe) {
                const user = window.Telegram.WebApp.initDataUnsafe.user;
                if (user && user.id) {
                    userId = user.id;
                }
            }

            // Send to API
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    message: message,
                    assistant_type: currentAssistantType || 'helper'
                })
            });

            // Remove typing indicator
            typingIndicator.remove();

            if (response.ok) {
                const data = await response.json();
                addChatMessage(data.response, 'assistant');
            } else {
                addChatMessage('Извините, произошла ошибка. Попробуйте еще раз.', 'assistant');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            typingIndicator.remove();
            addChatMessage('Не удалось отправить сообщение. Проверьте подключение к интернету.', 'assistant');
        }
    }
}

function addChatMessage(message, type) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return null;

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

    return messageElement;

    // Add fade-in animation
    messageElement.classList.add('fade-in');
}

// Track current assistant type
let currentAssistantType = 'helper';

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

    // Find the button element (event.target might be SVG or other child element)
    let targetButton = event.target;
    while (targetButton && !targetButton.classList.contains('filter-btn')) {
        targetButton = targetButton.parentElement;
    }

    if (targetButton) {
        targetButton.classList.add('active');
    }

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
    // Уведомления отключены для лучшего UX
    console.log(`Notification (${type}):`, message);
    return; // Просто логируем, не показываем уведомление
}

// Функция для выбора элемента плана на день
function selectPlanItem(button) {
    // Убираем active класс у всех кнопок в этом контейнере
    const allButtons = button.parentElement.querySelectorAll('.plan-item');
    allButtons.forEach(btn => {
        btn.classList.remove('active');
        // Сбрасываем стили для неактивной кнопки
        btn.style.background = '#FFFFFF';
        btn.style.color = '#2E6BEB';
    });

    // Добавляем active класс к текущей кнопке
    button.classList.add('active');
    // Устанавливаем стили для активной кнопки
    button.style.background = '#2E6BEB';
    button.style.color = 'white';

    console.log('Selected plan item:', button.textContent);
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

// Error handling полностью отключен для лучшего UX
// window.addEventListener('error', function(e) {
//     console.error('JavaScript error:', e.error);
// });

// Export functions to global scope for direct access
window.showScreen = showScreen;
window.showMainScreen = showMainScreen;
window.showPractices = showPractices;
window.showProfile = showProfile;
window.showVoiceChat = showVoiceChat;
window.toggleVoiceRecording = toggleVoiceRecording;
window.filterPractices = filterPractices;
window.toggleFavorite = toggleFavorite;
// Preview video functions
function playVideo() {
    console.log('Playing video preview...');
    // Here you would implement video playback logic
}

function handlePriceClick() {
    console.log('Price button clicked');
    // Here you would implement price/payment logic
}

window.playMeditation = playMeditation;
window.playVideo = playVideo;
window.handlePriceClick = handlePriceClick;
window.selectPlanItem = selectPlanItem;
window.setMood = setMood;
window.goToHistory = goToHistory;
window.sendChatMessage = sendChatMessage;

// Export functions for potential module usage
window.SoulNearApp = {
    showScreen,
    selectMood,
    sendChatMessage,
    startVoiceRecording,
    stopVoiceRecording,
    playPractice,
    filterPractices,
    toggleFavorite,
    playMeditation,
    selectPlanItem,
    vibrate,
    showNotification
};
// twemoji parse on load - only for main screen badges
document.addEventListener("DOMContentLoaded", function(){
  if (window.twemoji) {
    // Только для значков в календаре на главном экране
    const calendarBadges = document.querySelectorAll('.day-badge');
    calendarBadges.forEach(badge => {
      window.twemoji.parse(badge, {folder: "svg", ext: ".svg"});
    });
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

// cache-bust 1759000003

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

// ========================================
// МЕДИТАЦИОННЫЙ ПЛЕЕР - ФУНКЦИОНАЛЬНОСТЬ
// ========================================

let meditationTimer = null;
let meditationSeconds = 0;
let isPlaying = false;
let breathingCycle = 'inhale'; // 'inhale' или 'exhale'
let breathingInterval = null;

// Запуск медитации
function playMeditation() {
    showScreen('practice-player-screen');
    startMeditation();
}

// Показать экран практик
function showPractices() {
    showScreen('practices-screen');
    updateNavigation('practices-screen');
    stopMeditation();
}

// Запуск медитации
function startMeditation() {
    meditationSeconds = 94; // 1:34 в секундах
    isPlaying = true;

    // Сначала обновляем UI
    updateMeditationTimer();
    updatePlayPauseButton();

    // Инициализируем обработчик кнопки если его еще нет
    initMeditationPlayer();

    // Запускаем анимацию
    startBreathingAnimation();

    // Запускаем таймер
    meditationTimer = setInterval(() => {
        if (meditationSeconds > 0) {
            meditationSeconds--;
            updateMeditationTimer();
        } else {
            stopMeditation();
        }
    }, 1000);

    console.log('Meditation started, isPlaying:', isPlaying);
}

// Остановка медитации
function stopMeditation() {
    isPlaying = false;

    if (meditationTimer) {
        clearInterval(meditationTimer);
        meditationTimer = null;
    }

    stopBreathingAnimation();
    updatePlayPauseButton();

    console.log('Meditation stopped');
}

// Переключение play/pause
function toggleMeditationPlayback() {
    console.log('Toggle clicked, current isPlaying:', isPlaying);
    if (isPlaying) {
        pauseMeditation();
    } else {
        resumeMeditation();
    }
}

function pauseMeditation() {
    console.log('Pausing meditation');
    isPlaying = false;

    if (meditationTimer) {
        clearInterval(meditationTimer);
        meditationTimer = null;
    }

    stopBreathingAnimation();
    updatePlayPauseButton();
    console.log('Meditation paused, isPlaying:', isPlaying);
}

function resumeMeditation() {
    console.log('Resuming meditation');
    isPlaying = true;
    startBreathingAnimation();
    updatePlayPauseButton();

    meditationTimer = setInterval(() => {
        if (meditationSeconds > 0) {
            meditationSeconds--;
            updateMeditationTimer();
        } else {
            stopMeditation();
        }
    }, 1000);
    console.log('Meditation resumed, isPlaying:', isPlaying);
}

// Обновление таймера
function updateMeditationTimer() {
    const minutes = Math.floor(meditationSeconds / 60);
    const seconds = meditationSeconds % 60;
    const timerText = `${minutes}:${seconds.toString().padStart(2, '0')}`;

    const timerElement = document.querySelector('.player-timer');
    if (timerElement) {
        timerElement.textContent = timerText;
    }
}

// Обновление кнопки play/pause
function updatePlayPauseButton() {
    const pauseBtn = document.querySelector('.player-pause-btn');
    if (pauseBtn) {
        if (isPlaying) {
            pauseBtn.innerHTML = '⏸';
            console.log('Button set to pause (⏸)');
        } else {
            pauseBtn.innerHTML = '▶';
            console.log('Button set to play (▶)');
        }
    } else {
        console.log('Pause button not found for update');
    }
}

// Анимация дыхания
function startBreathingAnimation() {
    const orbElement = document.querySelector('.breathing-orb');
    const textElement = document.querySelector('.breathing-text');

    console.log('Starting breathing animation, orb found:', !!orbElement, 'text found:', !!textElement);

    if (!orbElement || !textElement) {
        console.log('Missing elements for breathing animation');
        return;
    }

    // Очищаем предыдущий интервал если есть
    if (breathingInterval) {
        clearInterval(breathingInterval);
    }

    // Плавная анимация дыхания для шейдера
    function animateBreathing() {
        const cycleTime = 8000; // 8 секунд полный цикл
        const halfCycle = cycleTime / 2; // 4 секунды на фазу
        const startTime = Date.now();

        function updateBreathing() {
            if (!isPlaying) return;

            const elapsed = (Date.now() - startTime) % cycleTime;
            const phase = elapsed / halfCycle;

            if (phase < 1) {
                // Вдох (0 -> 1)
                breathingIntensity = 0.5 + 0.5 * Math.sin((phase * Math.PI) - Math.PI/2);
                if (textElement.textContent !== 'Вдох') {
                    textElement.textContent = 'Вдох';
                    console.log('Inhale phase');
                }
            } else {
                // Выдох (1 -> 0)
                const exhalePhase = phase - 1;
                breathingIntensity = 1.0 - 0.5 * Math.sin((exhalePhase * Math.PI) - Math.PI/2);
                if (textElement.textContent !== 'Выдох') {
                    textElement.textContent = 'Выдох';
                    console.log('Exhale phase');
                }
            }

            requestAnimationFrame(updateBreathing);
        }

        updateBreathing();
    }

    // Запускаем анимацию
    animateBreathing();
}

function stopBreathingAnimation() {
    if (breathingInterval) {
        clearInterval(breathingInterval);
        breathingInterval = null;
    }

    // Сбрасываем интенсивность дыхания для шейдера
    breathingIntensity = 1.0;

    const orbElement = document.querySelector('.breathing-orb');
    const textElement = document.querySelector('.breathing-text');

    if (orbElement) {
        orbElement.classList.remove('inhale', 'exhale');
    }

    if (textElement) {
        textElement.textContent = 'Вдох';
    }
}

// Инициализация медитационного плеера
function initMeditationPlayer() {
    // Удаляем старые обработчики чтобы избежать дублирования
    const pauseBtn = document.querySelector('.player-pause-btn');
    if (pauseBtn) {
        pauseBtn.removeEventListener('click', toggleMeditationPlayback);
        pauseBtn.addEventListener('click', toggleMeditationPlayback);
        console.log('Play/pause button event listener attached');
    } else {
        console.log('Play/pause button not found');
    }

    // Инициализируем таймер и состояние кнопки
    updateMeditationTimer();
    updatePlayPauseButton();

    console.log('Meditation player initialized, isPlaying:', isPlaying);
}

// Обновляем глобальные функции
window.playMeditation = playMeditation;
window.showPractices = showPractices;
window.toggleMeditationPlayback = toggleMeditationPlayback;

// Добавляем инициализацию плеера при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initVoiceChatEvents();
    initMeditationPlayer();
});

// ========================================
// WEBGL ШЕЙДЕР ДЛЯ ДЫХАТЕЛЬНОЙ ФОРМЫ
// ========================================

let shaderGL = null;
let shaderProgram = null;
let startTime = performance.now();
let breathingIntensity = 1.0;

function initShaderOrb() {
    const canvas = document.getElementById('shaderCanvas');
    if (!canvas) return;

    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (!gl) {
        console.log('WebGL not supported, using CSS fallback');
        return;
    }

    shaderGL = gl;

    const vertexShaderSource = `
        attribute vec4 position;
        void main() {
            gl_Position = position;
        }
    `;

    const fragmentShaderSource = `
        precision mediump float;
        uniform float iTime;
        uniform vec2 iResolution;
        uniform float breathingPhase;

        #define T iTime
        #define r(v,t) { float a = (t)*T; float c=cos(a), s=sin(a); v = vec2(v.x*c-v.y*s, v.x*s+v.y*c); }

        float hash(float n) {
            return fract(sin(n)*43758.5453);
        }

        float noise(vec3 x) {
            vec3 p = floor(x);
            vec3 f = fract(x);
            f = f*f*(3.0-2.0*f);
            float n = p.x + p.y*57.0 + 113.0*p.z;
            return mix(mix(mix(hash(n+0.0), hash(n+1.0), f.x),
                          mix(hash(n+57.0), hash(n+58.0), f.x), f.y),
                      mix(mix(hash(n+113.0), hash(n+114.0), f.x),
                          mix(hash(n+170.0), hash(n+171.0), f.x), f.y), f.z);
        }

        float fbm(vec3 p) {
            float f = 0.0;
            f += 0.5000*noise(p); p = p*2.02;
            f += 0.2500*noise(p); p = p*2.03;
            f += 0.1250*noise(p); p = p*2.01;
            f += 0.0625*noise(p);
            return f;
        }

        vec3 sfbm3(vec3 p) {
            return vec3(fbm(p), fbm(p-327.67), fbm(p+327.67))*2.0-1.0;
        }

        void main() {
            vec2 uv = (gl_FragCoord.xy - 0.5*iResolution.xy) / iResolution.y;
            vec3 p = vec3(uv, 0.0);

            // Дыхательная анимация
            float breathScale = 1.0 + 0.3 * breathingPhase;
            p /= breathScale;

            // Время для анимации
            float time = T * 0.5;

            // Создаем органическую форму
            vec3 pos = p + vec3(0.0, 0.0, time);
            pos += sfbm3(pos*2.0 + vec3(time*0.3, 0.0, 0.0)) * 0.2;

            float dist = length(pos) - 0.4;
            dist += fbm(pos*4.0 + vec3(time*0.8, 0.0, 0.0)) * 0.1;

            // Мягкие края
            float alpha = 1.0 - smoothstep(0.0, 0.2, dist);

            // Пастельные цвета из картинки
            vec3 color1 = vec3(0.97, 0.90, 1.0);  // #f7e6ff
            vec3 color2 = vec3(0.81, 0.91, 1.0);  // #cfe9ff
            vec3 color3 = vec3(0.98, 0.84, 0.95); // #f9d7f1
            vec3 color4 = vec3(0.84, 0.83, 1.0);  // #d7d4ff

            // Градиент на основе позиции и времени
            float colorMix = (sin(time + pos.x*3.0)*0.5 + 0.5);
            colorMix += (cos(time*1.3 + pos.y*2.0)*0.3);
            colorMix = fract(colorMix);

            vec3 finalColor;
            if (colorMix < 0.33) {
                finalColor = mix(color1, color2, colorMix*3.0);
            } else if (colorMix < 0.66) {
                finalColor = mix(color2, color3, (colorMix-0.33)*3.0);
            } else {
                finalColor = mix(color3, color4, (colorMix-0.66)*3.0);
            }

            // Добавляем переливы
            float iridescence = sin(time*2.0 + length(pos)*8.0)*0.3 + 0.7;
            finalColor *= iridescence;

            gl_FragColor = vec4(finalColor, alpha * 0.9);
        }
    `;

    function createShader(gl, type, source) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);

        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            console.error('Shader compile error:', gl.getShaderInfoLog(shader));
            gl.deleteShader(shader);
            return null;
        }
        return shader;
    }

    const vertexShader = createShader(gl, gl.VERTEX_SHADER, vertexShaderSource);
    const fragmentShader = createShader(gl, gl.FRAGMENT_SHADER, fragmentShaderSource);

    shaderProgram = gl.createProgram();
    gl.attachShader(shaderProgram, vertexShader);
    gl.attachShader(shaderProgram, fragmentShader);
    gl.linkProgram(shaderProgram);

    if (!gl.getProgramParameter(shaderProgram, gl.LINK_STATUS)) {
        console.error('Program link error:', gl.getProgramInfoLog(shaderProgram));
        return;
    }

    // Создаем полноэкранный quad
    const positions = new Float32Array([
        -1, -1,
         1, -1,
        -1,  1,
         1,  1
    ]);

    const positionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);

    const positionLocation = gl.getAttribLocation(shaderProgram, 'position');
    const timeLocation = gl.getUniformLocation(shaderProgram, 'iTime');
    const resolutionLocation = gl.getUniformLocation(shaderProgram, 'iResolution');
    const breathingLocation = gl.getUniformLocation(shaderProgram, 'breathingPhase');

    function render() {
        if (!shaderGL || !shaderProgram) return;

        const currentTime = (performance.now() - startTime) / 1000.0;

        gl.viewport(0, 0, canvas.width, canvas.height);
        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT);

        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

        gl.useProgram(shaderProgram);

        gl.enableVertexAttribArray(positionLocation);
        gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
        gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 0, 0);

        gl.uniform1f(timeLocation, currentTime);
        gl.uniform2f(resolutionLocation, canvas.width, canvas.height);
        gl.uniform1f(breathingLocation, breathingIntensity);

        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

        requestAnimationFrame(render);
    }

    render();
    console.log('Shader orb initialized successfully');
}

// Запускаем шейдер при запуске медитации
const originalStartMeditation = startMeditation;
startMeditation = function() {
    originalStartMeditation();
    setTimeout(initShaderOrb, 100); // Небольшая задержка для загрузки DOM
};

// ========================================
// ИСТОРИЯ ЧАТОВ - УПРАВЛЕНИЕ СЕССИЯМИ
// ========================================

// Хранилище чатов
let chatSessions = [
    { id: 1, title: 'Как справляться со стрессом', date: new Date(), messages: [] },
    { id: 2, title: 'Проблемы на работе', date: new Date(), messages: [] },
    { id: 3, title: 'Поссорились с парнем', date: new Date(Date.now() - 86400000), messages: [] }
];

let currentChatId = null;

// Создать новый чат
function createNewChat() {
    const newChat = {
        id: Date.now(),
        title: 'Новый диалог',
        date: new Date(),
        messages: []
    };
    chatSessions.unshift(newChat);
    currentChatId = newChat.id;

    // Очищаем сообщения в voice-messages
    const voiceMessages = document.querySelector('.voice-messages');
    if (voiceMessages) {
        voiceMessages.innerHTML = '';
    }

    // Очищаем сообщения в chat-messages
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.innerHTML = '';
    }

    // Переходим в экран чата
    showScreen('voice-chat-screen');
    console.log('Created new chat:', newChat.id);
}

// Открыть существующий чат
function openChat(chatId) {
    currentChatId = chatId;
    const chat = chatSessions.find(c => c.id === chatId);
    
    if (chat) {
        console.log('Opening chat:', chat.title);
        // Загружаем сообщения чата
        loadChatMessages(chat);
        // Переходим в экран чата
        showScreen('voice-chat-screen');
    }
}

// Загрузить сообщения чата
function loadChatMessages(chat) {
    const chatContent = document.querySelector('.chat-content');
    if (!chatContent) return;
    
    // Очищаем текущие сообщения
    chatContent.innerHTML = '';
    
    // Загружаем сообщения из истории
    chat.messages.forEach(msg => {
        addChatMessage(msg.text, msg.type);
    });
    
    console.log(`Loaded ${chat.messages.length} messages for chat ${chat.id}`);
}

// Запуск голосового ввода
function startVoiceInput() {
    console.log('Starting voice input from history screen');
    createNewChat();
    // Здесь можно сразу активировать микрофон
}

// Обновить историю чатов в интерфейсе
function updateChatHistory() {
    const historyContent = document.querySelector('.history-content');
    if (!historyContent) return;
    
    // Группируем чаты по датам
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    const todayChats = chatSessions.filter(chat => {
        const chatDate = new Date(chat.date);
        chatDate.setHours(0, 0, 0, 0);
        return chatDate.getTime() === today.getTime();
    });
    
    const yesterdayChats = chatSessions.filter(chat => {
        const chatDate = new Date(chat.date);
        chatDate.setHours(0, 0, 0, 0);
        return chatDate.getTime() === yesterday.getTime();
    });
    
    const olderChats = chatSessions.filter(chat => {
        const chatDate = new Date(chat.date);
        chatDate.setHours(0, 0, 0, 0);
        return chatDate.getTime() < yesterday.getTime();
    });
    
    // Очищаем контент
    historyContent.innerHTML = '';
    
    // Добавляем группу "Сегодня"
    if (todayChats.length > 0) {
        const todayGroup = document.createElement('div');
        todayGroup.className = 'history-group';
        todayGroup.innerHTML = '<h4 class="history-date">Сегодня</h4>';
        
        todayChats.forEach(chat => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.textContent = chat.title;
            item.onclick = () => openChat(chat.id);
            todayGroup.appendChild(item);
        });
        
        historyContent.appendChild(todayGroup);
    }
    
    // Добавляем группу "Вчера"
    if (yesterdayChats.length > 0) {
        const yesterdayGroup = document.createElement('div');
        yesterdayGroup.className = 'history-group';
        yesterdayGroup.innerHTML = '<h4 class="history-date">Вчера</h4>';
        
        yesterdayChats.forEach(chat => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.textContent = chat.title;
            item.onclick = () => openChat(chat.id);
            yesterdayGroup.appendChild(item);
        });
        
        historyContent.appendChild(yesterdayGroup);
    }
    
    // Добавляем группу "Раньше"
    if (olderChats.length > 0) {
        const olderGroup = document.createElement('div');
        olderGroup.className = 'history-group';
        olderGroup.innerHTML = '<h4 class="history-date">Раньше</h4>';
        
        olderChats.forEach(chat => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.textContent = chat.title;
            item.onclick = () => openChat(chat.id);
            olderGroup.appendChild(item);
        });
        
        historyContent.appendChild(olderGroup);
    }
    
    console.log('Chat history updated');
}

// Сохранить сообщение в текущий чат
function saveChatMessage(text, type) {
    if (!currentChatId) {
        // Если нет текущего чата, создаём новый
        createNewChat();
    }
    
    const chat = chatSessions.find(c => c.id === currentChatId);
    if (chat) {
        chat.messages.push({ text, type, timestamp: new Date() });
        
        // Обновляем название чата на основе первого сообщения пользователя
        if (chat.title === 'Новый диалог' && type === 'user' && chat.messages.length === 1) {
            chat.title = text.substring(0, 50);
            updateChatHistory();
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    updateChatHistory();
});

// Экспортируем функции в глобальную область
window.createNewChat = createNewChat;
window.openChat = openChat;
window.startVoiceInput = startVoiceInput;

// Вернуться из истории на предыдущий экран
function goBackFromHistory() {
    if (previousScreen && previousScreen !== 'chat-history-screen') {
        showScreen(previousScreen);
    } else {
        showScreen('voice-chat-screen');
    }
    previousScreen = null;
}

window.goBackFromHistory = goBackFromHistory;

// ===== ANALYSIS SCREENS =====

function showAnalysis() {
    showScreen('analysis-screen');
}

function startAnalysis(topic) {
    currentAnalysisTopic = topic;
    const topicData = analysisTopics[topic];

    // Set assistant type based on topic
    currentAssistantType = topic; // 'relationships', 'money', 'confidence', 'fears'

    // Update title for both screens
    const chatTitleEl = document.getElementById('analysisTopicTitle');
    if (chatTitleEl) {
        chatTitleEl.textContent = topicData.title;
    }
    const voiceTitleEl = document.getElementById('analysisVoiceTitle');
    if (voiceTitleEl) {
        voiceTitleEl.textContent = topicData.title;
    }

    // Clear previous messages
    const messagesContainer = document.getElementById('analysisChatMessages');
    if (messagesContainer) {
        messagesContainer.innerHTML = '';
    }
    const voiceMessagesContainer = document.getElementById('analysisVoiceMessages');
    if (voiceMessagesContainer) {
        voiceMessagesContainer.innerHTML = '';
    }

    // Show voice screen first (like Soul Near GPT)
    showScreen('analysis-voice-screen');
}

async function sendAnalysisMessage() {
    const input = document.getElementById('analysisInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message using addChatMessage with custom container
    const messagesContainer = document.getElementById('analysisChatMessages');
    addMessageToContainer(messagesContainer, message, 'user');

    // Clear input
    input.value = '';

    // Add typing indicator
    const typingIndicator = addMessageToContainer(messagesContainer, 'Печатает...', 'assistant');
    typingIndicator.classList.add('typing-indicator');

    try {
        // Get user ID
        let userId = 'anonymous';
        if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe) {
            const user = window.Telegram.WebApp.initDataUnsafe.user;
            if (user && user.id) {
                userId = user.id;
            }
        }

        // Send to API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                message: message,
                assistant_type: currentAssistantType
            })
        });

        // Remove typing indicator
        typingIndicator.remove();

        if (response.ok) {
            const data = await response.json();
            addMessageToContainer(messagesContainer, data.response, 'assistant');
        } else {
            addMessageToContainer(messagesContainer, 'Извините, произошла ошибка. Попробуйте еще раз.', 'assistant');
        }
    } catch (error) {
        console.error('Error sending analysis message:', error);
        typingIndicator.remove();
        addMessageToContainer(messagesContainer, 'Не удалось отправить сообщение. Проверьте подключение к интернету.', 'assistant');
    }
}

// Helper function to add messages to any container
function addMessageToContainer(container, message, type) {
    if (!container) return null;

    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}`;

    const contentElement = document.createElement('div');
    contentElement.className = 'message-content';

    if (type === 'assistant' && message.includes('\n')) {
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
    container.appendChild(messageElement);
    container.scrollTop = container.scrollHeight;

    return messageElement;
}

function switchToAnalysisVoice() {
    showScreen('analysis-voice-screen');
}

function toggleAnalysisVoiceRecording() {
    isRecording = !isRecording;
    const btn = document.querySelector('#analysis-voice-screen .voice-mic-btn');

    if (isRecording) {
        btn.style.background = '#EF5350';
        // TODO: Start recording
    } else {
        btn.style.background = '#4A90E2';
        // TODO: Stop recording and send
    }
}

// ===== DREAMS SCREENS =====
function showDreams() {
    showScreen('dreams-screen');
}

function startDreamsChat() {
    showScreen('dreams-chat-screen');
}

function startDreamsVoice() {
    showScreen('dreams-voice-screen');
}

async function sendDreamsMessage() {
    const input = document.getElementById('dreamsInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message
    const messagesContainer = document.getElementById('dreamsChatMessages');
    addMessageToContainer(messagesContainer, message, 'user');

    // Clear input
    input.value = '';

    // Add typing indicator
    const typingIndicator = addMessageToContainer(messagesContainer, 'Печатает...', 'assistant');
    typingIndicator.classList.add('typing-indicator');

    try {
        // Get user ID
        let userId = 'anonymous';
        if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe) {
            const user = window.Telegram.WebApp.initDataUnsafe.user;
            if (user && user.id) {
                userId = user.id;
            }
        }

        // Send to API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                message: message,
                assistant_type: 'sleeper'
            })
        });

        // Remove typing indicator
        typingIndicator.remove();

        if (response.ok) {
            const data = await response.json();
            addMessageToContainer(messagesContainer, data.response, 'assistant');
        } else {
            addMessageToContainer(messagesContainer, 'Извините, произошла ошибка. Попробуйте еще раз.', 'assistant');
        }
    } catch (error) {
        console.error('Error sending dreams message:', error);
        typingIndicator.remove();
        addMessageToContainer(messagesContainer, 'Не удалось отправить сообщение. Проверьте подключение к интернету.', 'assistant');
    }
}

// Remove old mock code
function startDreamsChat() {
    showScreen('dreams-chat-screen');
    // Clear previous messages
    const messagesContainer = document.getElementById('dreamsChatMessages');
    if (messagesContainer) {
        messagesContainer.innerHTML = '';
    }
}

function startDreamsVoice() {
    showScreen('dreams-voice-screen');
}

// Skip old mock simulation below
if (false) {
    setTimeout(() => {
        const aiMsg = document.createElement('div');
        aiMsg.className = 'dreams-message assistant';
        aiMsg.innerHTML = `<div class="message-content">Это очень интересный сон. Позволь разобрать его символику...</div>`;
        messagesContainer.appendChild(aiMsg);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 1000);
}

function switchToDreamsVoice() {
    showScreen('dreams-voice-screen');
}

function toggleDreamsVoiceRecording() {
    isRecording = !isRecording;
    const btn = document.querySelector('#dreams-voice-screen .voice-mic-btn');

    if (isRecording) {
        btn.style.background = '#EF5350';
        // TODO: Start recording
    } else {
        btn.style.background = '#7E57C2';
        // TODO: Stop recording and send
    }
}

// ===== AGENT SELECTION =====
function selectAgent(agentType) {
    switch(agentType) {
        case 'general':
            // Обычный чат - показываем голосовой экран
            currentAssistantType = 'helper';
            showScreen('general-voice-screen');
            break;
        case 'analysis':
            // Анализ личности - показываем экран выбора категории
            showScreen('analysis-screen');
            break;
        case 'dreams':
            // Сны - сразу показываем голосовой экран
            currentAssistantType = 'sleeper';
            showScreen('dreams-voice-screen');
            break;
    }
}

function toggleGeneralVoiceRecording() {
    isRecording = !isRecording;
    const btn = document.querySelector('#general-voice-screen .voice-mic-btn');

    if (isRecording) {
        btn.style.background = '#EF5350';
        // TODO: Start recording
    } else {
        btn.style.background = '#4A90E2';
        // TODO: Stop recording and send
    }
}

// Export new functions to window
window.selectAgent = selectAgent;
window.toggleGeneralVoiceRecording = toggleGeneralVoiceRecording;

window.showAnalysis = showAnalysis;
window.startAnalysis = startAnalysis;
window.sendAnalysisMessage = sendAnalysisMessage;
window.switchToAnalysisVoice = switchToAnalysisVoice;
window.toggleAnalysisVoiceRecording = toggleAnalysisVoiceRecording;

window.showDreams = showDreams;
window.startDreamsChat = startDreamsChat;
window.startDreamsVoice = startDreamsVoice;
window.sendDreamsMessage = sendDreamsMessage;
window.switchToDreamsVoice = switchToDreamsVoice;
window.toggleDreamsVoiceRecording = toggleDreamsVoiceRecording;
