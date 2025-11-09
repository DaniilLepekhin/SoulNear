// ==========================================
// Video Player Hook
// ==========================================

import { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '../stores/useAppStore';
import type { Track } from '../types';

export const useVideoPlayer = () => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const playPromiseRef = useRef<Promise<void> | null>(null);

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

  // Get current time directly from video element
  const getCurrentTime = useCallback(() => {
    return videoRef.current?.currentTime || 0;
  }, []);

  // Initialize video element when track changes
  useEffect(() => {
    if (!videoRef.current) return;

    const video = videoRef.current;

    if (!activeTrack?.url) {
      video.src = '';
      return;
    }

    console.log('Loading video:', activeTrack.name);

    // Set video source
    video.src = activeTrack.url;

    // Setup event listeners
    const handleLoadedMetadata = () => {
      console.log('Video loaded, duration:', video.duration);
      setDuration(video.duration);
    };

    const handleEnded = () => {
      console.log('Video ended');
      setIsPlaying(false);
      video.currentTime = 0;
    };

    const handleError = (e: Event) => {
      console.error('Video playback error:', e);
      setIsPlaying(false);
    };

    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('ended', handleEnded);
    video.addEventListener('error', handleError);

    // Load video
    video.load();

    // Cleanup
    return () => {
      console.log('useEffect cleanup: removing video listeners');
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('ended', handleEnded);
      video.removeEventListener('error', handleError);
    };
  }, [activeTrack?.url, activeTrack?.name, setDuration, setIsPlaying]);

  // Play/pause based on isPlaying state
  useEffect(() => {
    if (!videoRef.current) return;

    const video = videoRef.current;

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
          playPromiseRef.current = video.play();
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
      video.pause();
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
    if (videoRef.current && isFinite(time)) {
      videoRef.current.currentTime = time;
    }
  }, []);

  const closePlayer = useCallback(() => {
    setShowPlayer(false);
    // Video continues playing in background (not typical for video, but keeping consistent with audio)
  }, [setShowPlayer]);

  const stopAndClose = useCallback(() => {
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
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
    videoRef,
  };
};
