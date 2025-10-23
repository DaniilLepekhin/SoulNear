# План реализации Audio Player для SoulNear WebApp

## 📋 Обзор

На основе изучения проекта **You Better**, создаём полноценный audio player для воспроизведения медитаций, музыки и йога практик в SoulNear.

---

## 🎯 Ключевые особенности из You Better

### ✅ Что работает отлично:

1. **Native Web Audio API** - без HTML `<audio>` элемента
2. **3-уровневая синхронизация состояния** - защита от рассинхронизации
3. **Background воспроизведение** - аудио продолжает играть при закрытии UI
4. **Fullscreen плеер** - большой красивый плеер с волнами
5. **Mini-плеер** - компактный плеер внизу экрана
6. **Модальные окна через state** - без внешних библиотек

---

## 📁 Структура файлов

```
src/
├── components/
│   ├── audio/
│   │   ├── FullscreenPlayer.tsx     ← НОВЫЙ: Большой плеер
│   │   ├── MiniPlayer.tsx           ← НОВЫЙ: Мини плеер
│   │   └── AudioControls.tsx        ← НОВЫЙ: Переиспользуемые контролы
│   ├── screens/
│   │   ├── PracticesScreen.tsx      ← ОБНОВИТЬ: добавить клики
│   │   └── PracticePlayerScreen.tsx ← УДАЛИТЬ: заменим на FullscreenPlayer
├── stores/
│   └── useAppStore.ts               ← ОБНОВИТЬ: добавить audio state
├── types/
│   └── index.ts                     ← ОБНОВИТЬ: добавить типы
└── hooks/
    └── useAudioPlayer.ts            ← НОВЫЙ: Логика плеера
```

---

## 🔧 Шаг 1: Расширение Zustand Store

### Файл: `src/stores/useAppStore.ts`

```typescript
// Добавляем новые типы
interface Track {
  id: string;
  name: string;
  audio_url: string;
  duration?: string;
  category?: string;
}

interface AppState {
  // ... существующие поля ...

  // ========== НОВЫЕ ПОЛЯ ДЛЯ AUDIO ==========

  // Текущий трек
  activeTrack: Track | null;
  setActiveTrack: (track: Track | null) => void;

  // Воспроизведение
  isPlaying: boolean;
  setIsPlaying: (playing: boolean) => void;

  // Время
  currentTime: number;
  setCurrentTime: (time: number) => void;

  duration: number;
  setDuration: (duration: number) => void;

  // UI плеера
  showPlayer: boolean;
  setShowPlayer: (show: boolean) => void;

  // Audio объект (сохраняем для переиспользования)
  audioElement: HTMLAudioElement | null;
  setAudioElement: (audio: HTMLAudioElement | null) => void;
}
```

**Имплементация:**

```typescript
export const useAppStore = create<AppState>()((set) => ({
  // ... существующий код ...

  // Audio state
  activeTrack: null,
  setActiveTrack: (track) => set({ activeTrack: track }),

  isPlaying: false,
  setIsPlaying: (playing) => set({ isPlaying: playing }),

  currentTime: 0,
  setCurrentTime: (time) => set({ currentTime: time }),

  duration: 0,
  setDuration: (duration) => set({ duration: duration }),

  showPlayer: false,
  setShowPlayer: (show) => set({ showPlayer: show }),

  audioElement: null,
  setAudioElement: (audio) => set({ audioElement: audio }),
}));
```

---

## 🎵 Шаг 2: Создание Hook для Audio Logic

### Файл: `src/hooks/useAudioPlayer.ts`

```typescript
import { useEffect, useCallback } from 'react';
import { useAppStore } from '../stores/useAppStore';

export const useAudioPlayer = () => {
  const {
    activeTrack,
    isPlaying,
    setIsPlaying,
    currentTime,
    setCurrentTime,
    duration,
    setDuration,
    audioElement,
    setAudioElement,
  } = useAppStore();

  // Создание и настройка audio объекта
  const initializeAudio = useCallback((url: string) => {
    // Останавливаем старый аудио
    if (audioElement) {
      audioElement.pause();
      audioElement.currentTime = 0;
    }

    const audio = new Audio(url);

    // ========== ОБРАБОТЧИКИ СОБЫТИЙ ==========

    // Play event
    audio.onplay = () => {
      console.log('▶️ Воспроизведение началось');
      if (!audio.paused) {
        setIsPlaying(true);
      }
    };

    // Pause event (с защитой от ложных пауз)
    audio.onpause = () => {
      // Игнорируем паузы в первые 500ms
      if (audio.currentTime < 0.5) return;

      // Игнорируем если трек еще играет
      if (audio.currentTime > 0 && !audio.ended) return;

      // Проверяем что это реальная пауза
      if (!audio.paused) return;

      console.log('⏸️ Пауза');
      setIsPlaying(false);
    };

    // Time update
    audio.ontimeupdate = () => {
      setCurrentTime(audio.currentTime);
    };

    // Metadata loaded (получаем длительность)
    audio.onloadedmetadata = () => {
      console.log('📊 Метаданные загружены:', audio.duration);
      setDuration(audio.duration);
    };

    // End event
    audio.onended = () => {
      console.log('⏹️ Трек завершён');
      setIsPlaying(false);
      setCurrentTime(0);
    };

    // Error event
    audio.onerror = (e) => {
      console.error('❌ Ошибка аудио:', e);
      console.error('Код ошибки:', audio.error?.code);
      console.error('Сообщение:', audio.error?.message);
      setIsPlaying(false);
    };

    // Сохраняем audio объект
    setAudioElement(audio);

    // Загружаем и начинаем воспроизведение
    audio.load();
    audio.play().catch((err) => {
      console.error('Не удалось начать воспроизведение:', err);
      setIsPlaying(false);
    });

    // ========== СИНХРОНИЗАЦИЯ СОСТОЯНИЯ ==========

    // Периодическая проверка состояния (уровень 2 защиты)
    setTimeout(() => {
      if (!audio.paused && isPlaying === false) {
        console.log('🔄 Синхронизация: исправляем isPlaying');
        setIsPlaying(true);
      } else if (audio.paused && isPlaying === true) {
        console.log('🔄 Синхронизация: останавливаем isPlaying');
        setIsPlaying(false);
      }
    }, 100);

    return audio;
  }, [audioElement, isPlaying, setIsPlaying, setCurrentTime, setDuration, setAudioElement]);

  // Toggle Play/Pause
  const togglePlayPause = useCallback(async () => {
    if (!activeTrack) return;

    if (isPlaying) {
      // PAUSE
      if (audioElement) {
        audioElement.pause();
        setIsPlaying(false);
      }
    } else {
      // PLAY
      if (audioElement && !audioElement.paused) {
        // Audio уже создан, просто играем
        audioElement.play().catch(err => {
          console.error('Ошибка воспроизведения:', err);
        });
      } else {
        // Создаём новый audio
        initializeAudio(activeTrack.audio_url);
      }
    }
  }, [isPlaying, activeTrack, audioElement, setIsPlaying, initializeAudio]);

  // Seek (перемотка)
  const seekTo = useCallback((time: number) => {
    if (audioElement) {
      audioElement.currentTime = time;
      setCurrentTime(time);
    }
  }, [audioElement, setCurrentTime]);

  // Полная остановка (для закрытия mini-плеера)
  const stopAudio = useCallback(() => {
    if (audioElement) {
      audioElement.pause();
      audioElement.currentTime = 0;
      setAudioElement(null);
    }
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
  }, [audioElement, setAudioElement, setIsPlaying, setCurrentTime, setDuration]);

  // Очистка при размонтировании
  useEffect(() => {
    return () => {
      if (audioElement) {
        audioElement.pause();
      }
    };
  }, [audioElement]);

  // Форматирование времени
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return {
    isPlaying,
    currentTime,
    duration,
    togglePlayPause,
    seekTo,
    stopAudio,
    formatTime,
  };
};
```

---

## 🖼️ Шаг 3: Fullscreen Player Component

### Файл: `src/components/audio/FullscreenPlayer.tsx`

```typescript
import { useCallback } from 'react';
import { useAppStore } from '../../stores/useAppStore';
import { useAudioPlayer } from '../../hooks/useAudioPlayer';

export const FullscreenPlayer = () => {
  const activeTrack = useAppStore((state) => state.activeTrack);
  const setShowPlayer = useAppStore((state) => state.setShowPlayer);

  const {
    isPlaying,
    currentTime,
    duration,
    togglePlayPause,
    formatTime,
  } = useAudioPlayer();

  const closePlayer = useCallback(() => {
    setShowPlayer(false);
    // НЕ останавливаем аудио! Оно продолжит играть в фоне
  }, [setShowPlayer]);

  if (!activeTrack) return null;

  // Прогресс для волн
  const progress = duration > 0 ? currentTime / duration : 0;

  // Генерируем случайные высоты волн (можно вынести в useMemo)
  const waveHeights = Array.from({ length: 40 }, () =>
    Math.random() * 60 + 40
  );

  return (
    <div className="fixed inset-0 z-50 bg-gradient-to-br from-orange-300 via-pink-300 to-purple-400">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 p-4 flex items-center justify-between">
        <button
          onClick={closePlayer}
          className="w-12 h-12 rounded-full bg-black/30 backdrop-blur-sm flex items-center justify-center text-white text-2xl"
        >
          ←
        </button>
        <h2 className="text-white text-lg font-semibold">Медитация</h2>
        <div className="w-12" /> {/* Spacer */}
      </div>

      {/* Content */}
      <div className="flex flex-col items-center justify-center h-full px-6">
        {/* Орб (bubble) */}
        <div className="relative w-64 h-64 mb-8">
          <img
            src="/bubble.png"
            alt="Orb"
            className="w-full h-full object-contain animate-pulse"
          />
        </div>

        {/* Название трека */}
        <h3 className="text-white text-2xl font-bold mb-2 text-center">
          {activeTrack.name}
        </h3>

        {/* Время */}
        <div className="flex justify-between w-full max-w-sm text-white/80 text-sm mb-4">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>

        {/* Волны прогресса */}
        <div className="flex items-end justify-center gap-1 h-20 mb-8">
          {waveHeights.map((height, i) => {
            const isActive = i / 40 <= progress;
            return (
              <div
                key={i}
                style={{ height: `${height}%` }}
                className={`w-1 rounded-full transition-all duration-300 ${
                  isActive
                    ? 'bg-white opacity-100'
                    : 'bg-white opacity-30'
                }`}
              />
            );
          })}
        </div>

        {/* Кнопка Play/Pause */}
        <button
          onClick={togglePlayPause}
          className="w-20 h-20 rounded-full bg-white/90 backdrop-blur-sm flex items-center justify-center shadow-lg"
        >
          {isPlaying ? (
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <rect x="6" y="4" width="4" height="16" rx="1" fill="#4A90E2"/>
              <rect x="14" y="4" width="4" height="16" rx="1" fill="#4A90E2"/>
            </svg>
          ) : (
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <path d="M8 5V19L19 12L8 5Z" fill="#4A90E2"/>
            </svg>
          )}
        </button>
      </div>
    </div>
  );
};
```

---

## 📱 Шаг 4: Mini Player Component

### Файл: `src/components/audio/MiniPlayer.tsx`

```typescript
import { useAppStore } from '../../stores/useAppStore';
import { useAudioPlayer } from '../../hooks/useAudioPlayer';

export const MiniPlayer = () => {
  const activeTrack = useAppStore((state) => state.activeTrack);
  const setActiveTrack = useAppStore((state) => state.setActiveTrack);
  const setShowPlayer = useAppStore((state) => state.setShowPlayer);

  const {
    isPlaying,
    currentTime,
    duration,
    togglePlayPause,
    stopAudio,
    formatTime,
  } = useAudioPlayer();

  if (!activeTrack) return null;

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  const handleClose = (e: React.MouseEvent) => {
    e.stopPropagation();

    // Полностью останавливаем аудио
    stopAudio();
    setActiveTrack(null);
  };

  const handleOpen = () => {
    setShowPlayer(true);
  };

  return (
    <div
      className="fixed bottom-20 left-4 right-4 z-20"
      onClick={handleOpen}
    >
      <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-lg p-4 flex items-center gap-3">
        {/* Play/Pause button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            togglePlayPause();
          }}
          className="w-12 h-12 rounded-full bg-blue-500 flex items-center justify-center shrink-0"
        >
          {isPlaying ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <rect x="6" y="4" width="4" height="16" rx="1" fill="white"/>
              <rect x="14" y="4" width="4" height="16" rx="1" fill="white"/>
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M8 5V19L19 12L8 5Z" fill="white"/>
            </svg>
          )}
        </button>

        {/* Track info */}
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-gray-900 truncate">
            {activeTrack.name}
          </h4>
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <span>{formatTime(currentTime)}</span>
            <span>/</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 rounded-b-2xl overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Close button */}
        <button
          onClick={handleClose}
          className="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center shrink-0 text-white text-lg"
        >
          ✕
        </button>
      </div>
    </div>
  );
};
```

---

## 🔗 Шаг 5: Интеграция в App.tsx

### Файл: `src/App.tsx`

```typescript
import { FullscreenPlayer } from './components/audio/FullscreenPlayer';
import { MiniPlayer } from './components/audio/MiniPlayer';
import { useAppStore } from './stores/useAppStore';

function App() {
  const currentScreen = useAppStore((state) => state.currentScreen);
  const showPlayer = useAppStore((state) => state.showPlayer);
  const activeTrack = useAppStore((state) => state.activeTrack);

  return (
    <div className="App">
      {/* Все существующие экраны */}
      {/* ... */}

      {/* ========== НОВЫЕ КОМПОНЕНТЫ ========== */}

      {/* Fullscreen плеер (модальное окно) */}
      {showPlayer && activeTrack && <FullscreenPlayer />}

      {/* Mini-плеер (когда fullscreen закрыт, но трек активен) */}
      {!showPlayer && activeTrack && <MiniPlayer />}
    </div>
  );
}
```

---

## 🎯 Шаг 6: Обновление PracticesScreen

### Файл: `src/components/screens/PracticesScreen.tsx`

Обновляем обработчики кликов:

```typescript
import { useAppStore } from '../../stores/useAppStore';

export const PracticesScreen = ({ isActive }: PracticesScreenProps) => {
  const setActiveTrack = useAppStore((state) => state.setActiveTrack);
  const setShowPlayer = useAppStore((state) => state.setShowPlayer);

  // Обработчик для медитаций
  const handlePlayMeditation = (item: any) => {
    console.log('🎵 Воспроизведение медитации:', item.name);

    // Устанавливаем активный трек
    setActiveTrack({
      id: item.media_id || item.id,
      name: item.name,
      audio_url: item.url || item.file_url || '', // Зависит от структуры данных
      category: 'meditation',
    });

    // Открываем fullscreen плеер
    setShowPlayer(true);
  };

  // Обработчик для музыки
  const handlePlayMusic = (track: any) => {
    console.log('🎵 Воспроизведение музыки:', track.name);

    setActiveTrack({
      id: track.media_id || track.id,
      name: track.name,
      audio_url: track.url || track.file_url || '',
      duration: track.duration,
      category: 'music',
    });

    setShowPlayer(true);
  };

  return (
    <div className="screen practices-screen">
      {/* ... существующий код ... */}

      {/* Медитации */}
      {practicesData?.practices.map((category: any, idx: number) => (
        <div key={idx}>
          {category.items.map((item: any, itemIdx: number) => (
            <div key={itemIdx} className="meditation-card">
              {/* ... существующий UI ... */}

              {/* Обновляем кнопку Play */}
              <button
                className="meditation-play-btn"
                onClick={() => handlePlayMeditation(item)}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M8 5V19L19 12L8 5Z" fill="white"/>
                </svg>
              </button>
            </div>
          ))}
        </div>
      ))}

      {/* Музыка */}
      {practicesData?.music.map((track: any, idx: number) => (
        <div key={idx} className="meditation-card">
          {/* ... существующий UI ... */}

          {/* Обновляем кнопку Play */}
          <button
            className="meditation-play-btn"
            onClick={() => handlePlayMusic(track)}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M8 5V19L19 12L8 5Z" fill="white"/>
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
};
```

---

## 🎨 Шаг 7: Стили (Tailwind CSS)

Все компоненты используют Tailwind утилиты. Убедитесь что в `tailwind.config.js` есть:

```javascript
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      backdropBlur: {
        'md': '12px',
        'lg': '24px',
      },
      animation: {
        'pulse': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}
```

---

## ✅ Шаг 8: Тестирование

### Сценарии для проверки:

1. **Play медитации**
   - Клик на кнопку Play → открывается fullscreen плеер
   - Аудио начинает воспроизводиться
   - Волны анимируются в такт прогрессу

2. **Закрытие fullscreen плеера**
   - Клик на кнопку "Назад" → fullscreen закрывается
   - Mini-плеер появляется внизу
   - Аудио продолжает играть

3. **Открытие fullscreen из mini**
   - Клик на mini-плеер → fullscreen открывается снова
   - Прогресс сохранён

4. **Полная остановка**
   - Клик на X mini-плеера → аудио останавливается
   - Mini-плеер исчезает

5. **Смена трека**
   - Воспроизведение трека 1
   - Клик на трек 2 → трек 1 останавливается, трек 2 начинается

6. **Синхронизация состояния**
   - isPlaying всегда соответствует реальному состоянию audio

---

## 📊 Таблица состояний

| showPlayer | activeTrack | Что видит пользователь |
|-----------|-------------|------------------------|
| `true` | `exists` | Fullscreen плеер ✅ |
| `false` | `exists` | Mini-плеер ✅ |
| `false` | `null` | Ничего ✅ |
| `true` | `null` | Невозможное состояние ❌ |

---

## 🚀 Развёртывание

1. **Локальная разработка:**
   ```bash
   cd webapp_v2
   npm run dev
   ```

2. **Сборка:**
   ```bash
   npm run build
   ```

3. **Деплой на сервер:**
   ```bash
   scp -P 61943 -r dist/* root@37.221.127.100:/home/soulnear_webapp/
   ```

---

## 🔮 Будущие улучшения

- [ ] Добавить playlist (очередь треков)
- [ ] Добавить shuffle и repeat
- [ ] Добавить управление громкостью
- [ ] Добавить скорость воспроизведения (0.5x, 1x, 1.5x, 2x)
- [ ] Добавить визуализацию с WebGL (как в You Better)
- [ ] Добавить избранное (favorites)
- [ ] Сохранять позицию в localStorage
- [ ] Добавить уведомления при переключении треков

---

## 📚 Источники

- Проект **You Better**: `/Users/daniillepekhin/My Python/You better/`
- Документация:
  - `/You better/AUDIO_PLAYER_IMPLEMENTATION.md`
  - `/You better/MODALS_AND_NAVIGATION.md`
  - `/You better/TECHNICAL_ANALYSIS.md`

---

**Автор:** Claude Code
**Дата:** 23 октября 2025
**Проект:** SoulNear WebApp v2
