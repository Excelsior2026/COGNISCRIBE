import { useState } from 'react';
import UploadCard from './UploadCard';
import RecordCard from './RecordCard';
import ResultsPanel from './ResultsPanel';
import StatusBar from './StatusBar';
import SettingsModal from '../Settings/SettingsModal';

interface ServiceStatus {
  ollama_running: boolean;
  api_running: boolean;
  whisper_loaded: boolean;
}

interface DashboardProps {
  serviceStatus: ServiceStatus | null;
  onRefreshStatus: () => void;
}

function Dashboard({ serviceStatus, onRefreshStatus }: DashboardProps) {
  const [data, setData] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const handleUploadStart = () => {
    setIsProcessing(true);
    setData(null);
  };

  const handleResult = (result: any) => {
    setData(result);
    setIsProcessing(false);
  };

  const handleError = () => {
    setIsProcessing(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-teal-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">
              <span className="text-blue-600">Cogni</span>
              <span className="text-teal-600">Scribe</span>
            </h1>
            <span className="text-sm text-gray-500">Desktop</span>
          </div>

          <div className="flex items-center gap-4">
            {/* Status Indicator */}
            <StatusBar status={serviceStatus} onRefresh={onRefreshStatus} />

            {/* Settings Button */}
            <button
              onClick={() => setShowSettings(true)}
              className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
              title="Settings"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8 max-w-6xl">
        {/* Hero Section */}
        <div className="text-center mb-8">
          <p className="text-xl text-gray-600 mb-4">
            Transform your lecture recordings into structured study notes
          </p>
          <div className="flex justify-center gap-4">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              🎙️ Audio Transcription
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-teal-100 text-teal-800">
              📝 Structured Notes
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
              ⚡ Fast Processing
            </span>
          </div>
        </div>

        {/* Input Cards - Upload or Record */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <UploadCard
            onResult={handleResult}
            onUploadStart={handleUploadStart}
            onError={handleError}
            isProcessing={isProcessing}
          />
          <RecordCard
            onResult={handleResult}
            onUploadStart={handleUploadStart}
            onError={handleError}
            isProcessing={isProcessing}
          />
        </div>

        {/* Results Panel */}
        {data && <ResultsPanel data={data} />}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-500">
          <p>Made with ❤️ for medical students • All processing happens locally on your computer</p>
        </div>
      </footer>

      {/* Settings Modal */}
      {showSettings && (
        <SettingsModal onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}

export default Dashboard;
