import { useState, useRef, useEffect } from 'react';
import { telegram } from '../../services/telegram';

interface VoiceRecorderProps {
  onRecordingComplete: (audioBlob: Blob) => void;
  onCancel?: () => void;
  onStateChange?: (isActive: boolean) => void;
}

export const VoiceRecorder = ({ onRecordingComplete, onCancel, onStateChange }: VoiceRecorderProps) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasRecording, setHasRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioBlobRef = useRef<Blob | null>(null);
  const audioUrlRef = useRef<string | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm;codecs=opus' });
        audioBlobRef.current = audioBlob;

        // Create audio URL for playback
        if (audioUrlRef.current) {
          URL.revokeObjectURL(audioUrlRef.current);
        }
        audioUrlRef.current = URL.createObjectURL(audioBlob);

        stream.getTracks().forEach(track => track.stop());
        setIsRecording(false);
        setHasRecording(true);

        if (timerRef.current) {
          clearInterval(timerRef.current);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setHasRecording(false);
      setError(null);
      onStateChange?.(true);
      telegram.hapticSuccess();

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Не удалось получить доступ к микрофону');
      telegram.hapticError();
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      telegram.haptic('light');
    }
  };

  const playRecording = () => {
    if (audioUrlRef.current && audioBlobRef.current) {
      if (audioRef.current) {
        audioRef.current.pause();
      }

      const audio = new Audio(audioUrlRef.current);
      audioRef.current = audio;

      audio.onplay = () => setIsPlaying(true);
      audio.onended = () => setIsPlaying(false);
      audio.onpause = () => setIsPlaying(false);

      audio.play();
      telegram.haptic('light');
    }
  };

  const stopPlaying = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
      telegram.haptic('light');
    }
  };

  const sendRecording = () => {
    if (audioBlobRef.current) {
      onRecordingComplete(audioBlobRef.current);
      resetRecorder();
      onStateChange?.(false);
      telegram.hapticSuccess();
    }
  };

  const cancelRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      chunksRef.current = [];
    }

    resetRecorder();
    onStateChange?.(false);

    if (onCancel) {
      onCancel();
    }
    telegram.haptic('light');
  };

  const resetRecorder = () => {
    setIsRecording(false);
    setHasRecording(false);
    setIsPlaying(false);
    setRecordingTime(0);

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }

    audioBlobRef.current = null;
    chunksRef.current = [];

    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
  };

  const deleteRecording = () => {
    resetRecorder();
    onStateChange?.(false);
    telegram.haptic('light');
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (error) {
    return (
      <div className="voice-recorder-error">
        <p>{error}</p>
        <button onClick={() => setError(null)}>OK</button>
      </div>
    );
  }

  // Recording state
  if (isRecording) {
    return (
      <div className="voice-recorder-active">
        <button className="voice-cancel-btn" onClick={cancelRecording}>✕</button>

        <div className="voice-recording-indicator">
          <div className="voice-pulse"></div>
          <span className="voice-timer">{formatTime(recordingTime)}</span>
        </div>

        <button className="voice-stop-btn" onClick={stopRecording}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <rect x="6" y="6" width="12" height="12" fill="white" rx="2"/>
          </svg>
        </button>
      </div>
    );
  }

  // Preview state (after recording stopped)
  if (hasRecording) {
    return (
      <div className="voice-recorder-preview">
        <button className="voice-delete-btn" onClick={deleteRecording} title="Удалить">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" fill="#f44336"/>
          </svg>
        </button>

        <div className="voice-preview-info">
          <span className="voice-duration">{formatTime(recordingTime)}</span>
        </div>

        {!isPlaying ? (
          <button className="voice-play-btn" onClick={playRecording} title="Прослушать">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M8 5v14l11-7z" fill="#4A90E2"/>
            </svg>
          </button>
        ) : (
          <button className="voice-play-btn" onClick={stopPlaying} title="Остановить">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <rect x="6" y="4" width="4" height="16" fill="#4A90E2"/>
              <rect x="14" y="4" width="4" height="16" fill="#4A90E2"/>
            </svg>
          </button>
        )}

        <button className="voice-send-btn" onClick={sendRecording} title="Отправить">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" fill="white"/>
          </svg>
        </button>
      </div>
    );
  }

  // Initial state
  return (
    <button className="voice-record-start-btn" onClick={startRecording}>
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <path d="M12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14Z" fill="currentColor"/>
        <path d="M19 11C19 14.53 16.39 17.44 13 17.93V21H11V17.93C7.61 17.44 5 14.53 5 11H7C7 13.76 9.24 16 12 16C14.76 16 17 13.76 17 11H19Z" fill="currentColor"/>
      </svg>
    </button>
  );
};
