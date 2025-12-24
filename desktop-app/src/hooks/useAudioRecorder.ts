import { useState, useRef, useCallback } from 'react';

interface AudioRecorderState {
  isRecording: boolean;
  isPaused: boolean;
  recordingTime: number;
  audioBlob: Blob | null;
  mimeType: string;
  error: string | null;
}

interface AudioRecorderControls {
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  pauseRecording: () => void;
  resumeRecording: () => void;
  clearRecording: () => void;
}

interface UseAudioRecorderReturn extends AudioRecorderState, AudioRecorderControls {
  audioChunks: Blob[];
}

export function useAudioRecorder(
  onChunk?: (chunk: Blob, timestamp: number) => void,
  chunkIntervalMs: number = 5000
): UseAudioRecorderReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [mimeType, setMimeType] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const chunkTimerRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const pickMimeType = (): string => {
    if (typeof MediaRecorder === 'undefined') {
      return '';
    }

    const candidates = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/ogg',
      'audio/mpeg',
    ];

    for (const candidate of candidates) {
      if (MediaRecorder.isTypeSupported(candidate)) {
        return candidate;
      }
    }

    return '';
  };

  const getMediaErrorMessage = (err: unknown): string => {
    if (err instanceof DOMException) {
      switch (err.name) {
        case 'NotAllowedError':
        case 'PermissionDeniedError':
          return 'Microphone access denied. Enable it in System Settings > Privacy & Security > Microphone.';
        case 'NotFoundError':
        case 'DevicesNotFoundError':
          return 'No microphone detected. Connect a microphone and try again.';
        case 'NotReadableError':
        case 'TrackStartError':
          return 'Microphone is in use by another app. Close it and try again.';
        default:
          return err.message || 'Failed to access microphone.';
      }
    }
    if (err instanceof Error) {
      return err.message || 'Failed to access microphone.';
    }
    return 'Failed to access microphone.';
  };

  // Start recording timer
  const startTimer = useCallback(() => {
    timerRef.current = setInterval(() => {
      setRecordingTime((prev) => prev + 1);
    }, 1000);
  }, []);

  // Stop recording timer
  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  // Start chunk timer for live preview
  const startChunkTimer = useCallback(() => {
    if (!onChunk || chunkIntervalMs <= 0) return;

    chunkTimerRef.current = setInterval(() => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        // Request data from MediaRecorder (triggers ondataavailable)
        mediaRecorderRef.current.requestData();
      }
    }, chunkIntervalMs);
  }, [onChunk, chunkIntervalMs]);

  // Stop chunk timer
  const stopChunkTimer = useCallback(() => {
    if (chunkTimerRef.current) {
      clearInterval(chunkTimerRef.current);
      chunkTimerRef.current = null;
    }
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setError(null);

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;

      // Create MediaRecorder with appropriate MIME type
      const selectedMimeType = pickMimeType();

      const mediaRecorder = selectedMimeType
        ? new MediaRecorder(stream, {
            mimeType: selectedMimeType,
            audioBitsPerSecond: 128000,
          })
        : new MediaRecorder(stream, {
            audioBitsPerSecond: 128000,
          });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      setMimeType(mediaRecorder.mimeType || selectedMimeType);

      // Handle data available (for both chunks and final recording)
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);

          // If this is a chunk (not the final stop), call onChunk
          if (mediaRecorder.state === 'recording' && onChunk) {
            onChunk(event.data, recordingTime);
          }
        }
      };

      // Handle recording stop
      mediaRecorder.onstop = () => {
        const chunkMimeType = chunksRef.current.find((chunk) => chunk.type)?.type || '';
        const finalMimeType = mediaRecorder.mimeType || chunkMimeType || selectedMimeType || '';
        const blob = finalMimeType
          ? new Blob(chunksRef.current, { type: finalMimeType })
          : new Blob(chunksRef.current);
        setAudioBlob(blob);
        setMimeType(finalMimeType);
        setIsRecording(false);
        stopTimer();
        stopChunkTimer();

        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
      };

      // Handle errors
      mediaRecorder.onerror = (event: Event) => {
        const errorEvent = event as ErrorEvent;
        console.error('MediaRecorder error:', errorEvent.error);
        setError(`Recording error: ${errorEvent.error?.message || 'Unknown error'}`);
        setIsRecording(false);
        stopTimer();
        stopChunkTimer();
      };

      // Start recording
      mediaRecorder.start();
      setIsRecording(true);
      setIsPaused(false);
      setRecordingTime(0);
      setAudioBlob(null);

      startTimer();
      startChunkTimer();
    } catch (err) {
      const errorMessage = getMediaErrorMessage(err);
      setError(errorMessage);
      console.error('Error starting recording:', err);
    }
  }, [onChunk, startTimer, stopTimer, startChunkTimer, stopChunkTimer, recordingTime]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      stopTimer();
      stopChunkTimer();
    }
  }, [stopTimer, stopChunkTimer]);

  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      startTimer();
      startChunkTimer();
    }
  }, [startTimer, startChunkTimer]);

  const clearRecording = useCallback(() => {
    setAudioBlob(null);
    setRecordingTime(0);
    setError(null);
    setMimeType('');
    chunksRef.current = [];
  }, []);

  return {
    isRecording,
    isPaused,
    recordingTime,
    audioBlob,
    mimeType,
    error,
    audioChunks: chunksRef.current,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    clearRecording,
  };
}
