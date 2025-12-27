import { useState, useEffect } from 'react';
import { readBinaryFile } from '@tauri-apps/api/fs';
import { useNativeRecorder } from '../../hooks/useNativeRecorder';
import LoadingSpinner from '../LoadingSpinner';

interface RecordCardProps {
  onUploadStart: () => void;
  onResult: (data: any) => void;
  onError: (error: string) => void;
  isProcessing: boolean;
  isBackendReady: boolean;
  backendStatusMessage: string;
  onPreflightCheck: () => Promise<boolean>;
}

const SUBJECTS = [
  { value: '', label: 'General' },
  { value: 'anatomy', label: 'Anatomy' },
  { value: 'physiology', label: 'Physiology' },
  { value: 'pharmacology', label: 'Pharmacology' },
  { value: 'pathophysiology', label: 'Pathophysiology' },
  { value: 'clinical skills', label: 'Clinical Skills' },
  { value: 'nursing fundamentals', label: 'Nursing Fundamentals' },
  { value: 'biochemistry', label: 'Biochemistry' },
  { value: 'microbiology', label: 'Microbiology' },
];

const getSummaryLabel = (ratio: number): string => {
  if (ratio <= 0.05) return 'Very Brief';
  if (ratio <= 0.1) return 'Brief';
  if (ratio <= 0.15) return 'Balanced';
  if (ratio <= 0.2) return 'Detailed';
  return 'Comprehensive';
};

const getProcessingErrorMessage = (err: unknown, fallback: string) => {
  if (err instanceof Error) {
    const message = err.message || fallback;
    const normalized = message.toLowerCase();
    if (normalized.includes('load failed') || normalized.includes('failed to fetch')) {
      return 'Could not connect to the local processing service. Make sure it is running and try again.';
    }
    return message;
  }
  return fallback;
};

function RecordCard({
  onUploadStart,
  onResult,
  onError,
  isProcessing,
  isBackendReady,
  backendStatusMessage,
  onPreflightCheck,
}: RecordCardProps) {
  const [recordingErrorMessage, setRecordingErrorMessage] = useState<string>('');
  const [subject, setSubject] = useState<string>('');
  const [quizSource, setQuizSource] = useState<'subject' | 'lecture'>('lecture');
  const [ratio, setRatio] = useState<number>(0.15);
  const [enhanceAudio, setEnhanceAudio] = useState(true);

  const {
    isRecording,
    isPaused,
    recordingTime,
    recordingPath,
    error: recordingError,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    clearRecording,
  } = useNativeRecorder();

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Start recording handler
  const handleStartRecording = async () => {
    try {
      clearRecording();
      setRecordingErrorMessage('');
      await startRecording();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start recording';
      setRecordingErrorMessage(message);
      onError(message);
    }
  };

  // Process recorded audio
  const handleProcess = async () => {
    if (!recordingPath) {
      onError('No recording available');
      return;
    }

    let backendReady = isBackendReady;
    try {
      backendReady = await onPreflightCheck();
    } catch (err) {
      const message = 'Unable to confirm local services. Please try again in a moment.';
      setRecordingErrorMessage(message);
      onError(message);
      return;
    }

    if (!backendReady) {
      const message = backendStatusMessage || 'Local services are still starting. Please try again in a moment.';
      setRecordingErrorMessage(message);
      onError(message);
      return;
    }

    onUploadStart();

    try {
      let fileData;
      try {
        fileData = await readBinaryFile(recordingPath);
      } catch (readErr) {
        throw new Error(
          'Failed to load the recording. Please ensure CogniScribe can access your recordings folder and try again.'
        );
      }

      const uint8 = new Uint8Array(fileData);
      if (uint8.length === 0) {
        throw new Error('Recording is empty. Please record audio before processing.');
      }
      const blob = new Blob([uint8], { type: 'audio/wav' });
      const fileName = recordingPath.split('/').pop() || 'recording.wav';
      const fileToProcess = new File([blob], fileName, { type: 'audio/wav' });

      // Send to processing pipeline
      const formData = new FormData();
      formData.append('file', fileToProcess);

      const response = await fetch(
        'http://localhost:8080/api/pipeline?' +
          new URLSearchParams({
            ratio: ratio.toString(),
            ...(subject && { subject }),
            enhance: enhanceAudio ? 'true' : 'false',
          }),
        {
          method: 'POST',
          body: formData,
        }
      );

      const result = await response.json().catch(() => null);
      if (!response.ok) {
        const message =
          (result && (result.error || result.message)) ||
          `Server returned ${response.status}: ${response.statusText}`;
        throw new Error(message);
      }

      if (!result) {
        throw new Error('Server returned an empty response.');
      }

      if (result.success) {
        onResult(result);
        clearRecording();
      } else {
        const message = result.error || 'Processing failed';
        setRecordingErrorMessage(message);
        onError(message);
      }
    } catch (err) {
      const message = getProcessingErrorMessage(err, 'Failed to process recording. Please try again.');
      setRecordingErrorMessage(message);
      onError(message);
    }
  };

  // Show recording error if any
  useEffect(() => {
    if (recordingError) {
      setRecordingErrorMessage(recordingError);
      onError(recordingError);
    }
  }, [recordingError, onError]);

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-2 flex items-center gap-2">
        🎙️ In Person Recording
      </h2>
      <p className="text-gray-600 mb-4">
        Record in-person lectures with in-app processing. No extra apps required.
      </p>

      <div
        className={`border-2 border-dashed rounded-xl p-12 text-center transition-all ${
          isRecording
            ? 'border-red-400 bg-red-50'
            : recordingPath
            ? 'border-green-400 bg-green-50'
            : 'border-gray-300 bg-gray-50'
        } ${isProcessing ? 'opacity-50 pointer-events-none' : ''}`}
      >
        {/* Recording Status */}
        {!isRecording && !recordingPath && (
          <div className="space-y-3">
            <div className="text-5xl">🎤</div>
            <div>
              <p className="text-lg font-semibold text-gray-800">Ready to record</p>
              <p className="text-sm text-gray-500 mt-1">
                Click the button below to start recording your lecture
              </p>
            </div>
          </div>
        )}

        {isRecording && (
          <div className="space-y-3">
            <div className="flex items-center justify-center gap-3">
              <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse"></div>
              <span className="text-2xl font-mono font-bold text-red-600">
                {formatTime(recordingTime)}
              </span>
            </div>
            <p className="text-sm text-gray-600">
              {isPaused ? '⏸️ Paused' : '🎙️ Recording...'}
            </p>
          </div>
        )}

        {recordingPath && !isRecording && (
          <div className="space-y-3">
            <div className="text-5xl">✅</div>
            <div>
              <p className="text-lg font-semibold text-green-700">Recording Complete!</p>
              <p className="text-sm text-gray-600 mt-1">
                Duration: {formatTime(recordingTime)} • Ready to process
              </p>
            </div>
          </div>
        )}

        {/* Recording Controls */}
        <div className="flex gap-3 justify-center mt-4">
          {!isRecording && !recordingPath && (
            <button
              onClick={handleStartRecording}
              disabled={isProcessing}
              className="bg-gradient-to-r from-red-500 to-red-600 text-white font-semibold py-3 px-8 rounded-xl hover:from-red-600 hover:to-red-700 transition-all shadow-md hover:shadow-lg transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ● Start Recording
            </button>
          )}

          {isRecording && (
            <>
              {!isPaused ? (
                <button
                  onClick={pauseRecording}
                  className="bg-yellow-500 text-white font-semibold py-2 px-6 rounded-lg hover:bg-yellow-600 transition-colors"
                >
                  ⏸️ Pause
                </button>
              ) : (
                <button
                  onClick={resumeRecording}
                  className="bg-green-500 text-white font-semibold py-2 px-6 rounded-lg hover:bg-green-600 transition-colors"
                >
                  ▶️ Resume
                </button>
              )}
              <button
                onClick={stopRecording}
                className="bg-red-600 text-white font-semibold py-2 px-6 rounded-lg hover:bg-red-700 transition-colors"
              >
                ⏹️ Stop
              </button>
            </>
          )}

          {recordingPath && !isRecording && (
            <button
              onClick={clearRecording}
              disabled={isProcessing}
              className="bg-gray-500 text-white font-semibold py-2 px-6 rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              🗑️ Discard
            </button>
          )}
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800">
        Educational use only. Do not upload live clinical data or PHI. Not for diagnosis, treatment, or clinical decision-making.
      </div>

      {!isBackendReady && (
        <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-xs text-blue-800">
          {backendStatusMessage || 'Local services are still starting. Please wait a moment.'}
        </div>
      )}

      {recordingErrorMessage && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          ⚠️ {recordingErrorMessage}
        </div>
      )}

      {/* Configuration (same as UploadCard) */}
      <div className="mt-8 space-y-6">
        {/* Subject Selection */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            📚 Subject (Optional)
          </label>
          <select
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            disabled={isProcessing || isRecording}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            {SUBJECTS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">Helps tailor the summary to your specific subject</p>
        </div>

        {/* Quiz Source */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            🎯 Quiz Question Source
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setQuizSource('subject')}
              disabled={isProcessing || isRecording}
              className={`px-4 py-3 rounded-lg border-2 transition-all text-left ${
                quizSource === 'subject'
                  ? 'border-blue-500 bg-blue-50 text-blue-900'
                  : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
              } ${isProcessing || isRecording ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <div className="font-semibold text-sm">📚 Subject-Based</div>
              <div className="text-xs mt-1 opacity-75">
                General {subject || 'medical'} knowledge
              </div>
            </button>
            <button
              type="button"
              onClick={() => setQuizSource('lecture')}
              disabled={isProcessing || isRecording}
              className={`px-4 py-3 rounded-lg border-2 transition-all text-left ${
                quizSource === 'lecture'
                  ? 'border-teal-500 bg-teal-50 text-teal-900'
                  : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
              } ${isProcessing || isRecording ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <div className="font-semibold text-sm">🎓 Lecture Content</div>
              <div className="text-xs mt-1 opacity-75">
                Specific to this recording
              </div>
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            {quizSource === 'subject'
              ? `Standardized questions testing ${subject || 'general'} knowledge`
              : 'Questions generated from your lecture notes (coming soon)'}
          </p>
        </div>

        {/* Summary Length */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            📝 Summary Length: {getSummaryLabel(ratio)}
          </label>
          <input
            type="range"
            min="0.05"
            max="0.30"
            step="0.05"
            value={ratio}
            onChange={(e) => setRatio(parseFloat(e.target.value))}
            disabled={isProcessing || isRecording}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:cursor-not-allowed"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Quick</span>
            <span>Balanced</span>
            <span>Thorough</span>
          </div>
        </div>

        {/* Enhancement Toggle */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            ✨ Studio Enhancement
          </label>
          <label className="flex items-center gap-3 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={enhanceAudio}
              onChange={(e) => setEnhanceAudio(e.target.checked)}
              disabled={isProcessing || isRecording}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <span>DeepFilterNet offline enhancement (auto-fallback)</span>
          </label>
          <p className="text-xs text-gray-500 mt-1">
            Improves clarity after recording; skips automatically if DeepFilterNet isn&apos;t available.
          </p>
        </div>
      </div>

      {/* Process Button */}
      <button
        onClick={handleProcess}
        disabled={!recordingPath || isProcessing || isRecording || !isBackendReady}
        className="w-full mt-8 bg-gradient-to-r from-blue-600 to-teal-600 text-white font-semibold py-4 px-6 rounded-xl hover:from-blue-700 hover:to-teal-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
      >
        {isProcessing ? (
          <span className="flex items-center justify-center gap-3">
            <LoadingSpinner />
            Processing your recording...
          </span>
        ) : (
          <span className="flex items-center justify-center gap-2">
            🚀 Process Recording & Generate Notes
          </span>
        )}
      </button>

      {isProcessing && (
        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600">This may take a few minutes depending on the recording length...</p>
          <div className="mt-3 flex justify-center gap-2">
            <span className="inline-block w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
            <span className="inline-block w-2 h-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
            <span className="inline-block w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
          </div>
        </div>
      )}
    </div>
  );
}

export default RecordCard;
