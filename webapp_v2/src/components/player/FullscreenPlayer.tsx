// ==========================================
// Fullscreen Audio Player Component
// ==========================================

import { useEffect, useState } from 'react';
import { useAudioPlayer } from '../../hooks/useAudioPlayer';
import './FullscreenPlayer.css';

export const FullscreenPlayer = () => {
  const {
    activeTrack,
    isPlaying,
    currentTime,
    duration,
    togglePlayPause,
    seek,
    closePlayer,
  } = useAudioPlayer();

  const [isDragging, setIsDragging] = useState(false);
  const [dragTime, setDragTime] = useState(0);

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

  if (!activeTrack) return null;

  const formatTime = (seconds: number): string => {
    if (!seconds || !isFinite(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Use dragging time if dragging, otherwise use current time
  const displayTime = isDragging ? dragTime : currentTime;
  const progress = duration > 0 ? (displayTime / duration) * 100 : 0;

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    setIsDragging(true);
    updateTimeFromMouse(e);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (isDragging) {
      updateTimeFromMouse(e as any);
    }
  };

  const handleMouseUp = (e: MouseEvent) => {
    if (isDragging) {
      updateTimeFromMouse(e as any);
      seek(dragTime);
      setIsDragging(false);
    }
  };

  const updateTimeFromMouse = (e: React.MouseEvent<HTMLDivElement> | MouseEvent) => {
    const target = e.currentTarget || document.querySelector('.player-progress-bar');
    if (!target) return;

    const rect = (target as HTMLElement).getBoundingClientRect();
    const x = (e as MouseEvent).clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    const newTime = percentage * duration;
    setDragTime(newTime);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragTime, duration]);

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
          <div className="player-progress-bar" onMouseDown={handleMouseDown}>
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
