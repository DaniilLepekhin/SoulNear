// ==========================================
// Audio Player Hook
// ==========================================

import { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '../stores/useAppStore';
import type { Track } from '../types';

export const useAudioPlayer = () => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const isSeekingRef = useRef(false);

  const {
    activeTrack,
    isPlaying,
    currentTime,
    duration,
    showPlayer,
    setActiveTrack,
    setIsPlaying,
    setCurrentTime,
    setDuration,
    setShowPlayer,
  } = useAppStore();

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

    audio.addEventListener('timeupdate', () => {
      // Don't update during seeking to prevent jumping
      if (!isSeekingRef.current) {
        setCurrentTime(audio.currentTime);
      }
    });

    audio.addEventListener('seeking', () => {
      isSeekingRef.current = true;
    });

    audio.addEventListener('seeked', () => {
      isSeekingRef.current = false;
      setCurrentTime(audio.currentTime);
    });

    audio.addEventListener('ended', () => {
      setIsPlaying(false);
      setCurrentTime(0);
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
  }, [activeTrack?.url, setDuration, setCurrentTime, setIsPlaying]);

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
      // Immediately update UI
      setCurrentTime(time);
      // Then seek audio
      audioRef.current.currentTime = time;
    }
  }, [setCurrentTime]);

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
    setCurrentTime(0);
    setDuration(0);
    setShowPlayer(false);
  }, [setActiveTrack, setIsPlaying, setCurrentTime, setDuration, setShowPlayer]);

  return {
    activeTrack,
    isPlaying,
    currentTime,
    duration,
    showPlayer,
    playTrack,
    togglePlayPause,
    seek,
    closePlayer,
    stopAndClose,
    setShowPlayer,
  };
};
