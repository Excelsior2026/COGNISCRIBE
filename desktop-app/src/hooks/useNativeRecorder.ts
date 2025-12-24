import { useState, useRef, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/tauri';

interface NativeRecorderState {
  isRecording: boolean;
  isPaused: boolean;
  recordingTime: number;
  recordingPath: string | null;
  error: string | null;
}

interface NativeRecorderControls {
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<void>;
  pauseRecording: () => Promise<void>;
  resumeRecording: () => Promise<void>;
  clearRecording: () => void;
}

interface UseNativeRecorderReturn extends NativeRecorderState, NativeRecorderControls {}

export function useNativeRecorder(): UseNativeRecorderReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [recordingPath, setRecordingPath] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const timerRef = useRef<number | null>(null);

  const startTimer = useCallback(() => {
    timerRef.current = setInterval(() => {
      setRecordingTime((prev) => prev + 1);
    }, 1000);
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      setRecordingPath(null);
      await invoke('native_start_recording');
      setIsRecording(true);
      setIsPaused(false);
      setRecordingTime(0);
      startTimer();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start recording';
      setError(message);
      throw err;
    }
  }, [startTimer]);

  const stopRecording = useCallback(async () => {
    try {
      const path = await invoke<string>('native_stop_recording');
      setRecordingPath(path);
      setIsRecording(false);
      setIsPaused(false);
      stopTimer();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to stop recording';
      setError(message);
      throw err;
    }
  }, [stopTimer]);

  const pauseRecording = useCallback(async () => {
    try {
      await invoke('native_pause_recording');
      setIsPaused(true);
      stopTimer();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to pause recording';
      setError(message);
      throw err;
    }
  }, [stopTimer]);

  const resumeRecording = useCallback(async () => {
    try {
      await invoke('native_resume_recording');
      setIsPaused(false);
      startTimer();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to resume recording';
      setError(message);
      throw err;
    }
  }, [startTimer]);

  const clearRecording = useCallback(() => {
    setRecordingPath(null);
    setRecordingTime(0);
    setError(null);
  }, []);

  return {
    isRecording,
    isPaused,
    recordingTime,
    recordingPath,
    error,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    clearRecording,
  };
}
