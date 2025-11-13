// ==========================================
// Fullscreen Video Player Component
// ==========================================

import { useEffect, useState, useRef } from 'react';
import { useVideoPlayer } from '../../hooks/useVideoPlayer';
import './VideoPlayer.css';

export const VideoPlayer = () => {
  const {
    activeTrack,
    isPlaying,
    duration,
    togglePlayPause,
    seek,
    closePlayer,
    videoRef,
  } = useVideoPlayer();

  const [currentTime, setCurrentTime] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [dragTime, setDragTime] = useState(0);
  const [showControls, setShowControls] = useState(true);
  const progressBarRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number>(0);
  const controlsTimeoutRef = useRef<number>(0);

  // Update current time smoothly using requestAnimationFrame
  useEffect(() => {
    const updateTime = () => {
      if (!isDragging && videoRef.current) {
        setCurrentTime(videoRef.current.currentTime);
      }
      animationFrameRef.current = requestAnimationFrame(updateTime);
    };

    animationFrameRef.current = requestAnimationFrame(updateTime);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isDragging, videoRef]);

  // Handle Escape key
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closePlayer();
      }
      if (e.key === ' ') {
        e.preventDefault();
        togglePlayPause();
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [closePlayer, togglePlayPause]);

  // Auto-hide controls after 3 seconds of inactivity
  useEffect(() => {
    if (!isPlaying) {
      setShowControls(true);
      return;
    }

    const hideControls = () => {
      setShowControls(false);
    };

    const resetTimeout = () => {
      setShowControls(true);
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
      controlsTimeoutRef.current = setTimeout(hideControls, 3000) as unknown as number;
    };

    const handleMouseMove = () => resetTimeout();
    const handleTouchStart = () => resetTimeout();

    resetTimeout();
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('touchstart', handleTouchStart);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('touchstart', handleTouchStart);
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
    };
  }, [isPlaying]);

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
    <div className="video-player-fullscreen">
      <div className="video-container">
        {/* Video element */}
        <video
          ref={videoRef}
          className="video-element"
          playsInline
          onClick={togglePlayPause}
        />

        {/* Controls overlay */}
        <div className={`video-controls-overlay ${showControls ? 'visible' : ''}`}>
        {/* Header */}
        <div className="video-header">
          <button
            className="video-back-btn"
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

          <div className="video-title">
            <h2>{activeTrack.name}</h2>
            {activeTrack.category && <p>{activeTrack.category}</p>}
          </div>
        </div>

        {/* Center play button */}
        <div className="video-center-controls">
          <button
            className="video-play-btn-center"
            onClick={togglePlayPause}
            style={{ opacity: isPlaying ? 0 : 1 }}
          >
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="11" stroke="white" strokeWidth="2" opacity="0.8"/>
              <path d="M10 8v8l6-4-6-4z" fill="white"/>
            </svg>
          </button>
        </div>

        {/* Bottom controls */}
        <div className="video-bottom-controls">
          {/* Progress bar */}
          <div
            ref={progressBarRef}
            className="video-progress-bar"
            onMouseDown={handleMouseDown}
          >
            <div
              className="video-progress-fill"
              style={{ width: `${progress}%` }}
            />
            <div
              className="video-progress-handle"
              style={{ left: `${progress}%` }}
            />
          </div>

          {/* Time and controls */}
          <div className="video-controls-row">
            <button className="video-control-btn" onClick={togglePlayPause}>
              {isPlaying ? (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <rect x="6" y="4" width="4" height="16" fill="white" rx="1"/>
                  <rect x="14" y="4" width="4" height="16" fill="white" rx="1"/>
                </svg>
              ) : (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M8 5v14l11-7L8 5z" fill="white"/>
                </svg>
              )}
            </button>

            <div className="video-time">
              <span>{formatTime(displayTime)}</span>
              <span className="video-time-separator"> / </span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
};
