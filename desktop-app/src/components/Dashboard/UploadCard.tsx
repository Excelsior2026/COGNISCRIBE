import { useState } from 'react';
import { open } from '@tauri-apps/api/dialog';
import LoadingSpinner from '../LoadingSpinner';
import { generateMockQuiz } from '../../utils/mockQuizGenerator';

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

interface UploadCardProps {
  onResult: (result: any) => void;
  onUploadStart: () => void;
  onError: () => void;
  isProcessing: boolean;
}

function UploadCard({ onResult, onUploadStart, onError, isProcessing }: UploadCardProps) {
  const [filePath, setFilePath] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [subject, setSubject] = useState('');
  const [ratio, setRatio] = useState(0.15);
  const [quizSource, setQuizSource] = useState<'subject' | 'lecture'>('subject');
  const [error, setError] = useState('');

  const handleFileSelect = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [
          {
            name: 'Audio',
            extensions: ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac', 'wma', 'webm', 'mkv', 'mp4'],
          },
        ],
      });

      if (selected && typeof selected === 'string') {
        setFilePath(selected);
        setFileName(selected.split('/').pop() || selected);
        setError('');
      }
    } catch (err) {
      setError(`Failed to select file: ${err}`);
    }
  };

  const handleSubmit = async () => {
    if (!filePath) {
      setError('Please select a file first');
      return;
    }

    onUploadStart();
    setError('');

    try {
      // For desktop, we'll use the Tauri fs API to read the file
      // and send it to the backend
      const response = await fetch('http://localhost:8080/api/pipeline?' + new URLSearchParams({
        ratio: ratio.toString(),
        ...(subject && { subject }),
      }), {
        method: 'POST',
        body: await createFilePayload(filePath),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      // Generate quiz questions based on user's choice
      let quizQuestions;
      let quizMetadata;

      if (quizSource === 'lecture') {
        // Future: LLM-generated questions from lecture content
        // For now, use subject-based questions with a note
        quizQuestions = generateMockQuiz(subject || 'general', 5);
        quizMetadata = {
          source: 'lecture',
          note: 'Content-based questions (simulated - will use actual lecture content when backend is ready)'
        };
      } else {
        // Subject-based questions from question bank
        quizQuestions = generateMockQuiz(subject || 'general', 5);
        quizMetadata = {
          source: 'subject',
          note: `Questions based on ${subject || 'general'} subject knowledge`
        };
      }

      // Add quiz to the result
      const resultWithQuiz = {
        ...result,
        quiz: quizQuestions,
        quizMetadata
      };

      onResult(resultWithQuiz);
    } catch (err: any) {
      setError(err.message || 'Failed to process audio. Please try again.');
      onError();
    }
  };

  const createFilePayload = async (path: string): Promise<FormData> => {
    // Read file using Tauri's fs API
    const { readBinaryFile } = await import('@tauri-apps/api/fs');
    let contents;
    try {
      contents = await readBinaryFile(path);
    } catch (readErr) {
      throw new Error(
        'Failed to load the selected file. Please move it to your home folder and try again.'
      );
    }

    const extension = (fileName || path).split('.').pop()?.toLowerCase() || '';
    const mimeType = (() => {
      switch (extension) {
        case 'wav':
          return 'audio/wav';
        case 'mp3':
          return 'audio/mpeg';
        case 'm4a':
          return 'audio/mp4';
        case 'flac':
          return 'audio/flac';
        case 'ogg':
          return 'audio/ogg';
        case 'aac':
          return 'audio/aac';
        case 'wma':
          return 'audio/x-ms-wma';
        case 'webm':
          return 'audio/webm';
        case 'mkv':
          return 'audio/x-matroska';
        case 'mp4':
          return 'audio/mp4';
        default:
          return 'application/octet-stream';
      }
    })();

    const blob = new Blob([new Uint8Array(contents)], { type: mimeType });
    const formData = new FormData();
    formData.append('file', blob, fileName || 'audio.mp3');

    return formData;
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
      {/* Upload Area */}
      <div
        onClick={!isProcessing ? handleFileSelect : undefined}
        className={`
          border-3 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all
          ${filePath
            ? 'border-green-400 bg-green-50'
            : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'
          }
          ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        {filePath ? (
          <div className="space-y-3">
            <div className="text-5xl">🎵</div>
            <div>
              <p className="text-lg font-semibold text-gray-800">{fileName}</p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (!isProcessing) {
                  setFilePath(null);
                  setFileName(null);
                }
              }}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium disabled:opacity-50"
              disabled={isProcessing}
            >
              Change file
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="text-5xl">🎙️</div>
            <div>
              <p className="text-lg font-semibold text-gray-800">Click to select lecture audio</p>
              <p className="text-sm text-gray-500 mt-1">or drag and drop (coming soon)</p>
            </div>
            <p className="text-xs text-gray-400">MP3, WAV, M4A, FLAC, OGG, AAC, WMA, WEBM, MKV, MP4 (up to 1GB)</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          ⚠️ {error}
        </div>
      )}

      {/* Settings */}
      <div className="mt-8 space-y-6">
        {/* Subject Selector */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            📚 Subject (Optional)
          </label>
          <select
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            disabled={isProcessing}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            {SUBJECTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">Helps tailor the summary to your specific subject</p>
        </div>

        {/* Quiz Source Selector */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            🎯 Quiz Question Source
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setQuizSource('subject')}
              disabled={isProcessing}
              className={`px-4 py-3 rounded-lg border-2 transition-all text-left ${
                quizSource === 'subject'
                  ? 'border-blue-500 bg-blue-50 text-blue-900'
                  : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
              } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <div className="font-semibold text-sm">📚 Subject-Based</div>
              <div className="text-xs mt-1 opacity-75">
                General {subject || 'medical'} knowledge
              </div>
            </button>
            <button
              type="button"
              onClick={() => setQuizSource('lecture')}
              disabled={isProcessing}
              className={`px-4 py-3 rounded-lg border-2 transition-all text-left ${
                quizSource === 'lecture'
                  ? 'border-teal-500 bg-teal-50 text-teal-900'
                  : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
              } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
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

        {/* Summary Length Slider */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            📝 Summary Length:{' '}
            {ratio === 0.05
              ? 'Very Brief'
              : ratio === 0.1
              ? 'Brief'
              : ratio === 0.15
              ? 'Balanced'
              : ratio === 0.2
              ? 'Detailed'
              : 'Comprehensive'}
          </label>
          <input
            type="range"
            min="0.05"
            max="0.30"
            step="0.05"
            value={ratio}
            onChange={(e) => setRatio(parseFloat(e.target.value))}
            disabled={isProcessing}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:cursor-not-allowed"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Quick</span>
            <span>Balanced</span>
            <span>Thorough</span>
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={!filePath || isProcessing}
        className="w-full mt-8 bg-gradient-to-r from-blue-600 to-teal-600 text-white font-semibold py-4 px-6 rounded-xl hover:from-blue-700 hover:to-teal-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
      >
        {isProcessing ? (
          <span className="flex items-center justify-center gap-3">
            <LoadingSpinner />
            Processing your lecture...
          </span>
        ) : (
          <span className="flex items-center justify-center gap-2">
            ✨ Generate Study Notes
          </span>
        )}
      </button>

      {isProcessing && (
        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600">This may take a few minutes depending on the audio length...</p>
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

export default UploadCard;
