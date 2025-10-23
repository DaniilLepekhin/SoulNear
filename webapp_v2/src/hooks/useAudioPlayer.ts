// ==========================================
// Audio Player Hook
// ==========================================

import { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '../stores/useAppStore';
import type { Track } from '../types';

export const useAudioPlayer = () => {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const {
    activeTrack,
    isPlaying,
    duration,
    showPlayer,
    setActiveTrack,
    setIsPlaying,
    setDuration,
    setShowPlayer,
  } = useAppStore();

  // Get current time directly from audio element
  const getCurrentTime = useCallback(() => {
    return audioRef.current?.currentTime || 0;
  }, []);

  // Initialize audio element when track changes
  useEffect(() => {
    if (!activeTrack?.url) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      return;
    }

    // Create new audio element
    const audio = new Audio(activeTrack.url);
    audioRef.current = audio;

    // Setup event listeners
    audio.addEventListener('loadedmetadata', () => {
      setDuration(audio.duration);
    });

    audio.addEventListener('ended', () => {
      setIsPlaying(false);
      audio.currentTime = 0;
    });

    audio.addEventListener('play', () => {
      setIsPlaying(true);
    });

    audio.addEventListener('pause', () => {
      setIsPlaying(false);
    });

    audio.addEventListener('error', (e) => {
      console.error('Audio playback error:', e);
      setIsPlaying(false);
    });

    // Load audio
    audio.load();

    // Cleanup
    return () => {
      audio.pause();
      audio.src = '';
    };
  }, [activeTrack?.url, setDuration, setIsPlaying]);

  // Play/pause based on isPlaying state
  useEffect(() => {
    if (!audioRef.current) return;

    if (isPlaying) {
      const playPromise = audioRef.current.play();
      if (playPromise !== undefined) {
        playPromise.catch((error) => {
          console.error('Playback failed:', error);
          setIsPlaying(false);
        });
      }
    } else {
      audioRef.current.pause();
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
    playTrack,
    togglePlayPause,
    seek,
    closePlayer,
    stopAndClose,
    setShowPlayer,
    getCurrentTime,
    audioRef,
  };
};
