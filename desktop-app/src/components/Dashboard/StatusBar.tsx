import { useState } from 'react';

interface ServiceStatus {
  ollama_running: boolean;
  api_running: boolean;
  whisper_loaded: boolean;
  deepfilter_available: boolean;
  deepfilter_binary: string | null;
  deepfilter_model: string | null;
}

interface StatusBarProps {
  status: ServiceStatus | null;
  onRefresh: () => void | Promise<unknown>;
}

function StatusBar({ status, onRefresh }: StatusBarProps) {
  const [showDetails, setShowDetails] = useState(false);

  if (!status) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-lg">
        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
        <span className="text-xs text-gray-600">Loading...</span>
      </div>
    );
  }

  const allHealthy = status.ollama_running && status.api_running && status.whisper_loaded;
  const deepfilterDescription = status.deepfilter_available
    ? `Model: ${status.deepfilter_model || 'Bundled'}`
    : 'Studio enhancement unavailable';

  return (
    <div className="relative">
      <button
        onClick={() => setShowDetails(!showDetails)}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors ${
          allHealthy
            ? 'bg-green-100 hover:bg-green-200'
            : 'bg-yellow-100 hover:bg-yellow-200'
        }`}
      >
        <div className={`w-2 h-2 rounded-full ${allHealthy ? 'bg-green-500' : 'bg-yellow-500'} animate-pulse`}></div>
        <span className={`text-xs font-medium ${allHealthy ? 'text-green-800' : 'text-yellow-800'}`}>
          {allHealthy ? 'All Systems Healthy' : 'Services Starting...'}
        </span>
      </button>

      {/* Dropdown Details */}
      {showDetails && (
        <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-800">Service Status</h3>
              <button
                onClick={onRefresh}
                className="text-blue-600 hover:text-blue-700 text-xs"
              >
                Refresh
              </button>
            </div>

            <div className="space-y-2">
              <StatusItem
                label="Ollama"
                status={status.ollama_running}
                description="AI summarization service"
              />
              <StatusItem
                label="Python API"
                status={status.api_running}
                description="Backend processing"
              />
              <StatusItem
                label="Whisper Model"
                status={status.whisper_loaded}
                description="Transcription engine"
              />
              <StatusItem
                label="DeepFilterNet"
                status={status.deepfilter_available}
                description={deepfilterDescription}
              />
            </div>
          </div>

          {/* Close overlay */}
          <div
            className="fixed inset-0 -z-10"
            onClick={() => setShowDetails(false)}
          ></div>
        </div>
      )}
    </div>
  );
}

function StatusItem({ label, status, description }: { label: string; status: boolean; description: string }) {
  return (
    <div className="flex items-start gap-2">
      <div className={`w-2 h-2 rounded-full mt-1.5 ${status ? 'bg-green-500' : 'bg-red-500'}`}></div>
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-800">{label}</span>
          <span className={`text-xs ${status ? 'text-green-600' : 'text-red-600'}`}>
            {status ? 'Running' : 'Stopped'}
          </span>
        </div>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
    </div>
  );
}

export default StatusBar;
