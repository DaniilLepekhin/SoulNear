// ==========================================
// Audio Player Hook
// ==========================================

import { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '../stores/useAppStore';
import type { Track } from '../types';

export const useAudioPlayer = () => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const playPromiseRef = useRef<Promise<void> | null>(null);

  const {
    activeTrack,
    isPlaying,
    duration,
    showPlayer,
    sleepTimer,
    sleepTimerStartTime,
    setActiveTrack,
    setIsPlaying,
    setDuration,
    setShowPlayer,
    setSleepTimer,
  } = useAppStore();

  // Get current time directly from audio element
  const getCurrentTime = useCallback(() => {
    return audioRef.current?.currentTime || 0;
  }, []);

  // Get remaining sleep timer time in minutes
  const getSleepTimerRemaining = useCallback(() => {
    if (!sleepTimer || !sleepTimerStartTime) return null;

    const elapsed = Date.now() - sleepTimerStartTime;
    const elapsedMinutes = elapsed / 1000 / 60;
    const remaining = sleepTimer - elapsedMinutes;

    return Math.max(0, remaining);
  }, [sleepTimer, sleepTimerStartTime]);

  // Initialize audio element when track changes
  useEffect(() => {
    // Cleanup old audio element
    if (audioRef.current) {
      console.log('Cleaning up old audio element');

      // Cancel any pending play promise
      if (playPromiseRef.current) {
        playPromiseRef.current.catch(() => {});
        playPromiseRef.current = null;
      }

      audioRef.current.pause();
      audioRef.current.src = '';
      audioRef.current.load(); // Force release
      audioRef.current = null;
    }

    if (!activeTrack?.url) {
      return;
    }

    console.log('Creating new audio element for:', activeTrack.name);

    // Create new audio element
    const audio = new Audio(activeTrack.url);
    audioRef.current = audio;

    // Setup event listeners
    const handleLoadedMetadata = () => {
      console.log('Audio loaded, duration:', audio.duration);
      setDuration(audio.duration);
    };

    const handleEnded = () => {
      console.log('Audio ended');
      setIsPlaying(false);
      audio.currentTime = 0;
    };

    const handleError = (e: ErrorEvent) => {
      console.error('Audio playback error:', e);
      setIsPlaying(false);
    };

    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError as any);

    // Load audio
    audio.load();

    // Cleanup
    return () => {
      console.log('useEffect cleanup: removing audio element');
      audio.pause();
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError as any);
      audio.src = '';
      audio.load();
    };
  }, [activeTrack?.url, setDuration, setIsPlaying]); // Removed activeTrack?.name - only URL matters for audio element

  // Sleep timer - check every second
  useEffect(() => {
    if (!sleepTimer || !sleepTimerStartTime || !isPlaying) return;

    const checkTimer = setInterval(() => {
      const elapsed = Date.now() - sleepTimerStartTime;
      const elapsedMinutes = elapsed / 1000 / 60;

      if (elapsedMinutes >= sleepTimer) {
        console.log('Sleep timer expired, stopping playback');
        setIsPlaying(false);
        setSleepTimer(null);
      }
    }, 1000);

    return () => clearInterval(checkTimer);
  }, [sleepTimer, sleepTimerStartTime, isPlaying, setIsPlaying, setSleepTimer]);

  // Play/pause based on isPlaying state
  useEffect(() => {
    if (!audioRef.current) return;

    const audio = audioRef.current;

    if (isPlaying) {
      // Wait for any previous play promise to complete
      const startPlayback = async () => {
        try {
          // If there's a pending play promise, wait for it
          if (playPromiseRef.current) {
            await playPromiseRef.current.catch(() => {
              // Ignore errors from previous play attempt
            });
          }

          // Start new playback
          playPromiseRef.current = audio.play();
          await playPromiseRef.current;
          playPromiseRef.current = null;
        } catch (error: any) {
          playPromiseRef.current = null;
          if (error?.name !== 'AbortError') {
            console.error('Playback failed:', error);
            setIsPlaying(false);
          }
        }
      };

      startPlayback();
    } else {
      // Cancel any pending play
      if (playPromiseRef.current) {
        playPromiseRef.current.catch(() => {
          // Ignore abort errors
        });
        playPromiseRef.current = null;
      }
      audio.pause();
    }
  }, [isPlaying, setIsPlaying]);

  const playTrack = useCallback((track: Track) => {
    setActiveTrack(track);
    setShowPlayer(true);
    setIsPlaying(true);
  }, [setActiveTrack, setShowPlayer, setIsPlaying]);

  const togglePlayPause = useCallback(() => {
    setIsPlaying(!isPlaying);
  }, [isPlaying, setIsPlaying]);

  const seek = useCallback((time: number) => {
    if (audioRef.current && isFinite(time)) {
      audioRef.current.currentTime = time;
    }
  }, []);

  const closePlayer = useCallback(() => {
    setShowPlayer(false);
    // Audio continues playing in background (mini-player)
  }, [setShowPlayer]);

  const stopAndClose = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setActiveTrack(null);
    setIsPlaying(false);
    setDuration(0);
    setShowPlayer(false);
  }, [setActiveTrack, setIsPlaying, setDuration, setShowPlayer]);

  return {
    activeTrack,
    isPlaying,
    duration,
    showPlayer,
    sleepTimer,
    playTrack,
    togglePlayPause,
    seek,
    closePlayer,
    stopAndClose,
    setShowPlayer,
    setSleepTimer,
    getCurrentTime,
    getSleepTimerRemaining,
    audioRef,
  };
};
