interface DownloadProgress {
  model_name: string;
  status: string;
  percent: number;
  downloaded_bytes: number;
  total_bytes: number;
  message: string;
}

interface ModelDownloadStepProps {
  progress: DownloadProgress | null;
  error?: string;
  onRetry?: () => void;
  onNext: () => void;
}

function ModelDownloadStep({ progress, error, onRetry, onNext }: ModelDownloadStepProps) {
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 GB';
    const gb = bytes / 1_000_000_000;
    return `${gb.toFixed(2)} GB`;
  };

  const isComplete = progress?.status === 'complete';

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <div className="max-w-2xl w-full">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-3xl font-bold text-gray-800 mb-2 text-center">
            Downloading AI Models
          </h2>
          <p className="text-gray-600 mb-8 text-center">
            This will only happen once. Grab a coffee! ☕
          </p>

          {/* Download Progress */}
          {progress && (
            <div className="space-y-6">
              <div className="p-6 bg-gradient-to-r from-blue-50 to-teal-50 rounded-xl">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-800 text-lg">
                      {progress.model_name}
                    </h3>
                    <p className="text-sm text-gray-600">{progress.message}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-blue-600">
                      {progress.percent.toFixed(0)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatBytes(progress.downloaded_bytes)} / {formatBytes(progress.total_bytes)}
                    </div>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full h-4 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-teal-500 transition-all duration-500 ease-out"
                    style={{ width: `${progress.percent}%` }}
                  ></div>
                </div>

                {/* Status Icon */}
                <div className="mt-4 flex items-center justify-center">
                  {progress.status === 'downloading' && (
                    <div className="flex gap-2">
                      <span className="inline-block w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                      <span className="inline-block w-2 h-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                      <span className="inline-block w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                    </div>
                  )}
                  {progress.status === 'complete' && (
                    <div className="flex items-center gap-2 text-green-600">
                      <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                      </svg>
                      <span className="font-semibold">Complete!</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Info Box */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>💡 Tip:</strong> These models are stored locally on your computer and will be reused for all future sessions. No re-download needed!
                </p>
              </div>
            </div>
          )}

          {!progress && !error && (
            <div className="text-center py-12">
              <div className="animate-spin h-16 w-16 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
              <p className="text-gray-600">Preparing download...</p>
            </div>
          )}

          {error && (
            <div className="text-center py-8">
              <div className="text-5xl mb-3">⚠️</div>
              <p className="text-red-700 font-semibold mb-2">Download failed</p>
              <p className="text-sm text-gray-600 mb-6">{error}</p>
              <button
                onClick={onRetry}
                className="bg-blue-600 text-white font-semibold py-3 px-8 rounded-xl hover:bg-blue-700 transition-colors"
              >
                Retry Download
              </button>
            </div>
          )}

          {/* Continue Button (only show when complete) */}
          {isComplete && (
            <div className="mt-8 text-center">
              <button
                onClick={onNext}
                className="bg-gradient-to-r from-blue-600 to-teal-600 text-white font-semibold py-4 px-12 rounded-xl hover:from-blue-700 hover:to-teal-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                Continue →
              </button>
            </div>
          )}
        </div>

        {/* Background Tasks Info */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            You can minimize this window. We'll notify you when it's done.
          </p>
        </div>
      </div>
    </div>
  );
}

export default ModelDownloadStep;
