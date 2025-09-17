// Telegram WebApp API
let tg = window.Telegram.WebApp;

// Глобальные переменные
let currentUser = null;
let selectedMood = null;
let currentDate = new Date();
let userData = {
    moods: [],
    messages: [],
    practices: [],
    activities: []
};

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация Telegram WebApp
    tg.ready();
    tg.expand();
    
    // Получение данных пользователя
    currentUser = tg.initDataUnsafe?.user;
    
    // Настройка темы
    if (tg.colorScheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
    
    // Инициализация данных
    initializeUserData();
    updateDailyStats();
    generateCalendar();
    
    // Обработчики событий
    setupEventListeners();
    
    console.log('SoulNear WebApp инициализирован');
});

// Настройка обработчиков событий
function setupEventListeners() {
    // Обработчик ввода в чате
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // Обработчик изменения месяца в календаре
    window.changeMonth = changeMonth;
}

// Инициализация данных пользователя
function initializeUserData() {
    if (currentUser) {
        document.getElementById('user-name').textContent = currentUser.first_name || 'Пользователь';
        document.getElementById('user-id').textContent = `ID: ${currentUser.id}`;
    }
    
    // Загрузка сохраненных данных
    loadUserData();
}

// Загрузка данных пользователя
function loadUserData() {
    const savedData = localStorage.getItem('soulNearData');
    if (savedData) {
        userData = JSON.parse(savedData);
    }
    
    // Обновление статистики
    updateProfileStats();
    updateRecentActivities();
}

// Сохранение данных пользователя
function saveUserData() {
    localStorage.setItem('soulNearData', JSON.stringify(userData));
    
    // Отправка данных в бот
    sendDataToBot('data_sync', userData);
}

// Отправка данных в Telegram бот
function sendDataToBot(action, data) {
    const payload = {
        action: action,
        user_id: currentUser?.id || 'unknown',
        data: data,
        timestamp: new Date().toISOString()
    };
    
    tg.sendData(JSON.stringify(payload));
}

// Навигация между экранами
function showScreen(screenId) {
    // Скрыть все экраны
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    
    // Показать нужный экран
    const targetScreen = document.getElementById(screenId);
    if (targetScreen) {
        targetScreen.classList.add('active');
    }
}

// Показать главный экран
function showMainScreen() {
    showScreen('main-screen');
    updateDailyStats();
}

// Показать экран настроения
function openMoodTracker() {
    showScreen('mood-screen');
}

// Показать экран чата
function openChat() {
    showScreen('chat-screen');
}

// Показать экран дыхательных практик
function openBreathing() {
    showScreen('breathing-screen');
}

// Показать экран календаря
function openCalendar() {
    showScreen('calendar-screen');
    generateCalendar();
}

// Показать экран профиля
function showProfile() {
    showScreen('profile-screen');
    updateProfileStats();
}

// Выбор настроения
function selectMood(mood) {
    selectedMood = mood;
    
    // Убрать выделение с других кнопок
    document.querySelectorAll('.mood-option').forEach(btn => {
        btn.classList.remove('selected');
    });
    
    // Выделить выбранную кнопку
    document.querySelector(`[data-mood="${mood}"]`).classList.add('selected');
    
    // Активировать кнопку сохранения
    document.getElementById('save-mood-btn').disabled = false;
}

// Сохранение настроения
function saveMood() {
    if (!selectedMood) return;
    
    const note = document.getElementById('mood-note').value;
    const moodData = {
        mood: selectedMood,
        note: note,
        date: new Date().toISOString(),
        timestamp: Date.now()
    };
    
    // Добавить в данные пользователя
    userData.moods.push(moodData);
    
    // Обновить статистику
    updateDailyStats();
    updateProfileStats();
    
    // Сохранить данные
    saveUserData();
    
    // Отправить в бот
    sendDataToBot('set_mood', moodData);
    
    // Показать уведомление
    showNotification('Настроение сохранено! 😊');
    
    // Вернуться на главный экран
    setTimeout(() => {
        showMainScreen();
        resetMoodForm();
    }, 1500);
}

// Сброс формы настроения
function resetMoodForm() {
    selectedMood = null;
    document.getElementById('mood-note').value = '';
    document.querySelectorAll('.mood-option').forEach(btn => {
        btn.classList.remove('selected');
    });
    document.getElementById('save-mood-btn').disabled = true;
}

// Отправка сообщения в чат
function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Добавить сообщение пользователя
    addChatMessage(message, 'user');
    
    // Очистить поле ввода
    input.value = '';
    
    // Сохранить сообщение
    const messageData = {
        text: message,
        date: new Date().toISOString(),
        timestamp: Date.now()
    };
    
    userData.messages.push(messageData);
    saveUserData();
    
    // Отправить в бот
    sendDataToBot('send_message', messageData);
    
    // Показать индикатор загрузки
    showTypingIndicator();
    
    // Имитация ответа ИИ (в реальном приложении это будет ответ от бота)
    setTimeout(() => {
        hideTypingIndicator();
        const aiResponse = generateAIResponse(message);
        addChatMessage(aiResponse, 'ai');
    }, 2000);
}

// Добавление сообщения в чат
function addChatMessage(text, sender) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatar = sender === 'ai' ? '🤖' : '👤';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${text}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Показать индикатор печати
function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message ai-message typing-indicator';
    typingDiv.id = 'typing-indicator';
    
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Скрыть индикатор печати
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Генерация ответа ИИ (заглушка)
function generateAIResponse(userMessage) {
    const responses = [
        "Интересно! Расскажи больше об этом.",
        "Понимаю тебя. Как ты себя чувствуешь сейчас?",
        "Это важная тема. Что ты думаешь об этом?",
        "Спасибо, что поделился. Я здесь, чтобы помочь.",
        "Как это влияет на твою жизнь?",
        "Ты молодец, что говоришь об этом открыто.",
        "Давай разберем это вместе.",
        "Что бы ты хотел изменить в этой ситуации?"
    ];
    
    return responses[Math.floor(Math.random() * responses.length)];
}

// Начало дыхательной практики
function startBreathing(type) {
    const practiceData = {
        type: type,
        startTime: new Date().toISOString(),
        timestamp: Date.now()
    };
    
    // Сохранить практику
    userData.practices.push(practiceData);
    saveUserData();
    
    // Отправить в бот
    sendDataToBot('breathing_started', practiceData);
    
    // Показать уведомление
    showNotification('Дыхательная практика началась! 🫁');
    
    // Имитация завершения практики через 30 секунд
    setTimeout(() => {
        completeBreathingPractice(type);
    }, 30000);
}

// Завершение дыхательной практики
function completeBreathingPractice(type) {
    const practiceData = {
        type: type,
        duration: 30,
        completed: true,
        endTime: new Date().toISOString(),
        timestamp: Date.now()
    };
    
    // Обновить последнюю практику
    const lastPractice = userData.practices[userData.practices.length - 1];
    if (lastPractice) {
        Object.assign(lastPractice, practiceData);
    }
    
    // Сохранить данные
    saveUserData();
    
    // Отправить в бот
    sendDataToBot('breathing_completed', practiceData);
    
    // Обновить статистику
    updateDailyStats();
    updateProfileStats();
    
    // Показать уведомление
    showNotification('Практика завершена! Отличная работа! 🎯');
}

// Генерация календаря
function generateCalendar() {
    const calendarGrid = document.getElementById('calendar-grid');
    if (!calendarGrid) return;
    
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    // Обновить заголовок
    document.getElementById('current-month').textContent = 
        currentDate.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' });
    
    // Получить первый день месяца и количество дней
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    // Создать сетку календаря
    let calendarHTML = '<div class="calendar-weekdays">';
    const weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
    weekdays.forEach(day => {
        calendarHTML += `<div class="weekday">${day}</div>`;
    });
    calendarHTML += '</div><div class="calendar-days">';
    
    // Пустые ячейки для начала месяца
    for (let i = 0; i < startingDayOfWeek; i++) {
        calendarHTML += '<div class="calendar-day empty"></div>';
    }
    
    // Дни месяца
    for (let day = 1; day <= daysInMonth; day++) {
        const isToday = day === new Date().getDate() && month === new Date().getMonth();
        const hasMood = hasMoodForDay(day, month, year);
        const hasPractice = hasPracticeForDay(day, month, year);
        
        let dayClass = 'calendar-day';
        if (isToday) dayClass += ' today';
        if (hasMood) dayClass += ' has-mood';
        if (hasPractice) dayClass += ' has-practice';
        
        calendarHTML += `<div class="${dayClass}" onclick="selectDay(${day})">${day}</div>`;
    }
    
    calendarHTML += '</div>';
    calendarGrid.innerHTML = calendarHTML;
}

// Проверка наличия настроения для дня
function hasMoodForDay(day, month, year) {
    return userData.moods.some(mood => {
        const moodDate = new Date(mood.date);
        return moodDate.getDate() === day && 
               moodDate.getMonth() === month && 
               moodDate.getFullYear() === year;
    });
}

// Проверка наличия практики для дня
function hasPracticeForDay(day, month, year) {
    return userData.practices.some(practice => {
        const practiceDate = new Date(practice.startTime);
        return practiceDate.getDate() === day && 
               practiceDate.getMonth() === month && 
               practiceDate.getFullYear() === year;
    });
}

// Выбор дня в календаре
function selectDay(day) {
    // Здесь можно добавить функциональность просмотра событий дня
    showNotification(`Выбран ${day} ${currentDate.toLocaleDateString('ru-RU', { month: 'long' })}`);
}

// Изменение месяца в календаре
function changeMonth(direction) {
    currentDate.setMonth(currentDate.getMonth() + direction);
    generateCalendar();
}

// Обновление статистики дня
function updateDailyStats() {
    const today = new Date().toDateString();
    
    // Настроение сегодня
    const todayMood = userData.moods.find(mood => 
        new Date(mood.date).toDateString() === today
    );
    
    if (todayMood) {
        const moodEmojis = {
            excellent: '😍',
            good: '😊',
            okay: '😐',
            bad: '😔',
            terrible: '😢'
        };
        document.getElementById('mood-today').textContent = moodEmojis[todayMood.mood] || '😊';
    } else {
        document.getElementById('mood-today').textContent = '😊';
    }
    
    // Сообщения сегодня
    const todayMessages = userData.messages.filter(msg => 
        new Date(msg.date).toDateString() === today
    );
    document.getElementById('messages-today').textContent = todayMessages.length;
    
    // Практики сегодня
    const todayPractices = userData.practices.filter(practice => 
        new Date(practice.startTime).toDateString() === today
    );
    document.getElementById('practices-today').textContent = todayPractices.length;
}

// Обновление статистики профиля
function updateProfileStats() {
    // Дней с нами
    const firstMood = userData.moods[0];
    const daysWithUs = firstMood ? 
        Math.floor((Date.now() - new Date(firstMood.date).getTime()) / (1000 * 60 * 60 * 24)) : 0;
    document.getElementById('total-days').textContent = daysWithUs;
    
    // Всего записей настроения
    document.getElementById('total-moods').textContent = userData.moods.length;
    
    // Всего практик
    document.getElementById('total-practices').textContent = userData.practices.length;
}

// Обновление недавних активностей
function updateRecentActivities() {
    const activityList = document.getElementById('activity-list');
    if (!activityList) return;
    
    // Объединить все активности
    const allActivities = [
        ...userData.moods.map(mood => ({
            type: 'mood',
            text: `Настроение: ${mood.mood}`,
            time: mood.timestamp
        })),
        ...userData.messages.map(msg => ({
            type: 'message',
            text: `Сообщение отправлено`,
            time: msg.timestamp
        })),
        ...userData.practices.map(practice => ({
            type: 'practice',
            text: `Практика: ${practice.type}`,
            time: practice.timestamp
        }))
    ];
    
    // Сортировать по времени
    allActivities.sort((a, b) => b.time - a.time);
    
    // Показать последние 5 активностей
    const recentActivities = allActivities.slice(0, 5);
    
    let activitiesHTML = '';
    recentActivities.forEach(activity => {
        const icon = {
            mood: '😊',
            message: '💬',
            practice: '🫁'
        }[activity.type] || '🎯';
        
        const timeAgo = getTimeAgo(activity.time);
        
        activitiesHTML += `
            <div class="activity-item">
                <div class="activity-icon">${icon}</div>
                <div class="activity-text">
                    <div class="activity-title">${activity.text}</div>
                    <div class="activity-time">${timeAgo}</div>
                </div>
            </div>
        `;
    });
    
    if (activitiesHTML === '') {
        activitiesHTML = `
            <div class="activity-item">
                <div class="activity-icon">🎯</div>
                <div class="activity-text">
                    <div class="activity-title">Добро пожаловать!</div>
                    <div class="activity-time">Только что</div>
                </div>
            </div>
        `;
    }
    
    activityList.innerHTML = activitiesHTML;
}

// Получение времени "назад"
function getTimeAgo(timestamp) {
    const now = Date.now();
    const diff = now - timestamp;
    
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (minutes < 1) return 'только что';
    if (minutes < 60) return `${minutes} мин назад`;
    if (hours < 24) return `${hours} ч назад`;
    return `${days} дн назад`;
}

// Показать уведомление
function showNotification(message) {
    // Создать элемент уведомления
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    
    // Добавить стили
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(255, 107, 107, 0.9);
        color: white;
        padding: 12px 20px;
        border-radius: 25px;
        font-size: 14px;
        font-weight: 500;
        z-index: 1000;
        backdrop-filter: blur(10px);
        animation: slideDown 0.3s ease;
    `;
    
    // Добавить анимацию
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideDown {
            from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
            to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
    
    // Добавить в DOM
    document.body.appendChild(notification);
    
    // Удалить через 3 секунды
    setTimeout(() => {
        notification.remove();
        style.remove();
    }, 3000);
}

// Экспорт данных
function exportData() {
    const dataStr = JSON.stringify(userData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `soulNear_data_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    showNotification('Данные экспортированы! 📤');
}

// Показать настройки
function showSettings() {
    showNotification('Настройки в разработке ⚙️');
}

// Обработка данных от Telegram WebApp
tg.onEvent('mainButtonClicked', function() {
    // Обработка нажатия главной кнопки
    console.log('Main button clicked');
});

tg.onEvent('backButtonClicked', function() {
    // Обработка нажатия кнопки "Назад"
    showMainScreen();
});

// Показать кнопку "Назад" когда нужно
function showBackButton() {
    tg.BackButton.show();
}

// Скрыть кнопку "Назад"
function hideBackButton() {
    tg.BackButton.hide();
}

// Инициализация завершена
console.log('SoulNear WebApp готов к работе!');


