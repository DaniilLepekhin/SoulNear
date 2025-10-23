// ==========================================
// Mini Player Component
// ==========================================

import { useEffect, useState, useRef } from 'react';
import { useAudioPlayer } from '../../hooks/useAudioPlayer';
import './MiniPlayer.css';

export const MiniPlayer = () => {
  const {
    activeTrack,
    isPlaying,
    duration,
    togglePlayPause,
    stopAndClose,
    setShowPlayer,
    audioRef,
  } = useAudioPlayer();

  const [currentTime, setCurrentTime] = useState(0);
  const animationFrameRef = useRef<number>(0);

  // Update current time smoothly using requestAnimationFrame
  useEffect(() => {
    const updateTime = () => {
      if (audioRef.current) {
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
  }, [audioRef]);

  if (!activeTrack) return null;

  const formatTime = (seconds: number): string => {
    if (!seconds || !isFinite(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="mini-player" onClick={() => setShowPlayer(true)}>
      {/* Progress background */}
      <div
        className="mini-player-progress"
        style={{ width: `${progress}%` }}
      />

      {/* Content */}
      <div className="mini-player-content">
        {/* Track info */}
        <div className="mini-player-info">
          <div className="mini-player-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"
                fill="#2E6BEB"
              />
            </svg>
          </div>
          <div className="mini-player-text">
            <div className="mini-player-name">{activeTrack.name}</div>
            <div className="mini-player-time">
              {formatTime(currentTime)} / {formatTime(duration)}
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="mini-player-controls">
          <button
            className="mini-player-play-btn"
            onClick={(e) => {
              e.stopPropagation();
              togglePlayPause();
            }}
          >
            {isPlaying ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <rect x="6" y="4" width="4" height="16" fill="#2E6BEB" rx="1"/>
                <rect x="14" y="4" width="4" height="16" fill="#2E6BEB" rx="1"/>
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M8 5v14l11-7L8 5z" fill="#2E6BEB"/>
              </svg>
            )}
          </button>

          <button
            className="mini-player-close-btn"
            onClick={(e) => {
              e.stopPropagation();
              stopAndClose();
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path
                d="M18 6L6 18M6 6l12 12"
                stroke="#666"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};
