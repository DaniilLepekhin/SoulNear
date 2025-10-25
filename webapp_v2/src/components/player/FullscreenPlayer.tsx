// ==========================================
// Fullscreen Audio Player Component
// ==========================================

import { useEffect, useState, useRef } from 'react';
import { useAudioPlayer } from '../../hooks/useAudioPlayer';
import './FullscreenPlayer.css';

export const FullscreenPlayer = () => {
  const {
    activeTrack,
    isPlaying,
    duration,
    sleepTimer,
    togglePlayPause,
    seek,
    closePlayer,
    setSleepTimer,
    getSleepTimerRemaining,
    audioRef,
  } = useAudioPlayer();

  const [currentTime, setCurrentTime] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [dragTime, setDragTime] = useState(0);
  const [showTimerMenu, setShowTimerMenu] = useState(false);
  const [timerRemaining, setTimerRemaining] = useState<number | null>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number>(0);
  const timerIntervalRef = useRef<number>(0);

  const timerOptions = [1, 3, 5, 10, 15, 30, 60];

  // Update current time smoothly using requestAnimationFrame
  useEffect(() => {
    const updateTime = () => {
      if (!isDragging && audioRef.current) {
        setCurrentTime(audioRef.current.currentTime);
      }
      animationFrameRef.current = requestAnimationFrame(updateTime);
    };

    animationFrameRef.current = requestAnimationFrame(updateTime);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isDragging, audioRef]);

  // Handle Escape key
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closePlayer();
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [closePlayer]);

  // Update timer remaining every second
  useEffect(() => {
    if (!sleepTimer) {
      setTimerRemaining(null);
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = 0;
      }
      return;
    }

    const updateRemaining = () => {
      const remaining = getSleepTimerRemaining();
      setTimerRemaining(remaining);
    };

    updateRemaining();
    timerIntervalRef.current = setInterval(updateRemaining, 1000) as unknown as number;

    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = 0;
      }
    };
  }, [sleepTimer, getSleepTimerRemaining]);

  // Close timer menu when clicking outside
  useEffect(() => {
    if (!showTimerMenu) return;

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.player-timer-btn') && !target.closest('.timer-menu')) {
        setShowTimerMenu(false);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [showTimerMenu]);

  if (!activeTrack) return null;

  const formatTime = (seconds: number): string => {
    if (!seconds || !isFinite(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatTimerRemaining = (minutes: number | null): string => {
    if (minutes === null) return '';
    const mins = Math.floor(minutes);
    const secs = Math.floor((minutes - mins) * 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleTimerSelect = (minutes: number | null) => {
    setSleepTimer(minutes);
    setShowTimerMenu(false);
  };

  // Use dragging time if dragging, otherwise use current time
  const displayTime = isDragging ? dragTime : currentTime;
  const progress = duration > 0 ? (displayTime / duration) * 100 : 0;

  const calculateTimeFromMouse = (e: React.MouseEvent<HTMLDivElement> | MouseEvent): number => {
    if (!progressBarRef.current) return 0;

    const rect = progressBarRef.current.getBoundingClientRect();
    const x = (e as MouseEvent).clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    return percentage * duration;
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    const newTime = calculateTimeFromMouse(e);
    setDragTime(newTime);
    setIsDragging(true);
  };

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      const newTime = calculateTimeFromMouse(e as any);
      setDragTime(newTime);
    };

    const handleMouseUp = (e: MouseEvent) => {
      const newTime = calculateTimeFromMouse(e as any);
      setDragTime(newTime);
      console.log('Seeking to:', newTime);
      seek(newTime);
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, seek, duration]);

  return (
    <div className="fullscreen-player">
      {/* Background gradient */}
      <div className="player-background" />

      {/* Header */}
      <div className="player-header">
        <button
          className="player-back-btn"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            closePlayer();
          }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M15 18l-6-6 6-6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>

        <div className="player-header-spacer" />

        <button
          className={`player-timer-btn ${sleepTimer ? 'active' : ''}`}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setShowTimerMenu(!showTimerMenu);
          }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="13" r="9" stroke="currentColor" strokeWidth="2"/>
            <path d="M12 9v4l3 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <path d="M9 2h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          {timerRemaining !== null && (
            <span className="timer-remaining">{formatTimerRemaining(timerRemaining)}</span>
          )}
        </button>

        {/* Timer Menu */}
        {showTimerMenu && (
          <div className="timer-menu">
            {timerOptions.map((minutes) => (
              <button
                key={minutes}
                className={`timer-option ${sleepTimer === minutes ? 'active' : ''}`}
                onClick={() => handleTimerSelect(minutes)}
              >
                {minutes} мин
              </button>
            ))}
            <button
              className={`timer-option ${!sleepTimer ? 'active' : ''}`}
              onClick={() => handleTimerSelect(null)}
            >
              Выкл
            </button>
          </div>
        )}
      </div>

      {/* Main content */}
      <div className="player-main">
        {/* Animated visualization */}
        <div className="player-visualization">
          <div className={`breathing-orb ${isPlaying ? 'playing' : ''}`}>
            <img src="/bubble.png" className="bubble-image" alt="Visualization" />
          </div>
        </div>

        {/* Track info */}
        <div className="player-info">
          <h2 className="player-track-name">{activeTrack.name}</h2>
          {activeTrack.category && (
            <p className="player-track-category">{activeTrack.category}</p>
          )}
        </div>

        {/* Progress bar */}
        <div className="player-progress-section">
          <div
            ref={progressBarRef}
            className="player-progress-bar"
            onMouseDown={handleMouseDown}
          >
            <div
              className="player-progress-fill"
              style={{ width: `${progress}%` }}
            />
            <div
              className="player-progress-handle"
              style={{ left: `${progress}%` }}
            />
          </div>
          <div className="player-time">
            <span>{formatTime(displayTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Controls */}
        <div className="player-controls">
          <button className="player-control-btn" onClick={togglePlayPause}>
            {isPlaying ? (
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <rect x="6" y="4" width="4" height="16" fill="white" rx="1"/>
                <rect x="14" y="4" width="4" height="16" fill="white" rx="1"/>
              </svg>
            ) : (
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <path d="M8 5v14l11-7L8 5z" fill="white"/>
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
