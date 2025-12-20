import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';

interface OBSInfo {
  installed: boolean;
  version: string | null;
  path: string | null;
  websocket_enabled: boolean;
  websocket_port: number;
  is_running: boolean;
}

interface OBSConnectionStatus {
  connected: boolean;
  obs_version: string | null;
  websocket_version: string | null;
  available_features: string[];
}

interface OBSSetupWizardProps {
  onComplete: (connected: boolean) => void;
  onSkip: () => void;
}

function OBSSetupWizard({ onComplete, onSkip }: OBSSetupWizardProps) {
  const [step, setStep] = useState<'detecting' | 'not-found' | 'not-running' | 'connecting' | 'connected' | 'error'>('detecting');
  const [obsInfo, setObsInfo] = useState<OBSInfo | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<OBSConnectionStatus | null>(null);
  const [error, setError] = useState<string>('');
  const [password, setPassword] = useState('');

  // Detect OBS on mount
  useEffect(() => {
    detectOBS();
  }, []);

  const detectOBS = async () => {
    try {
      setStep('detecting');
      const info = await invoke<OBSInfo>('obs_detect');
      setObsInfo(info);

      if (!info.installed) {
        setStep('not-found');
      } else if (!info.is_running) {
        setStep('not-running');
      } else if (info.websocket_enabled) {
        // Try to connect automatically
        connectToOBS('localhost', info.websocket_port, null);
      } else {
        setStep('error');
        setError('OBS is running but WebSocket is not enabled');
      }
    } catch (err) {
      setStep('error');
      setError(err instanceof Error ? err.message : 'Failed to detect OBS');
    }
  };

  const connectToOBS = async (host: string, port: number, pwd: string | null) => {
    try {
      setStep('connecting');
      const status = await invoke<OBSConnectionStatus>('obs_connect', {
        host,
        port,
        password: pwd,
      });

      setConnectionStatus(status);
      setStep('connected');
      setTimeout(() => onComplete(true), 1500);
    } catch (err) {
      setStep('error');
      setError(err instanceof Error ? err.message : 'Failed to connect to OBS');
    }
  };

  const handleConnect = () => {
    if (obsInfo) {
      connectToOBS('localhost', obsInfo.websocket_port, password || null);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-8 bg-white rounded-2xl shadow-xl">
      {/* Detecting */}
      {step === 'detecting' && (
        <div className="text-center">
          <div className="text-6xl mb-4 animate-bounce">🔍</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Detecting OBS Studio...
          </h2>
          <p className="text-gray-600">
            Checking for OBS installation and configuration
          </p>
          <div className="mt-4">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </div>
      )}

      {/* OBS Not Found */}
      {step === 'not-found' && (
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            OBS Studio Not Found
          </h2>
          <p className="text-gray-600 mb-6">
            CliniScribe Pro requires OBS Studio for professional audio recording.
          </p>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6 text-left">
            <h3 className="font-semibold text-blue-900 mb-3">📥 How to Install OBS:</h3>
            <ol className="space-y-2 text-sm text-blue-800">
              <li>1. Visit <a href="https://obsproject.com" target="_blank" rel="noopener noreferrer" className="underline font-semibold">obsproject.com</a></li>
              <li>2. Download OBS Studio (100% Free)</li>
              <li>3. Install and launch OBS</li>
              <li>4. Come back to CliniScribe and click "Retry"</li>
            </ol>
          </div>

          <div className="flex gap-3 justify-center">
            <button
              onClick={detectOBS}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
            >
              🔄 Retry Detection
            </button>
            <button
              onClick={onSkip}
              className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Use Basic Recording
            </button>
          </div>
        </div>
      )}

      {/* OBS Not Running */}
      {step === 'not-running' && (
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            OBS Studio Not Running
          </h2>
          <p className="text-gray-600 mb-6">
            OBS is installed at:<br />
            <code className="text-sm bg-gray-100 px-2 py-1 rounded">{obsInfo?.path}</code>
          </p>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6 text-left">
            <h3 className="font-semibold text-yellow-900 mb-3">🚀 Launch OBS:</h3>
            <ol className="space-y-2 text-sm text-yellow-800">
              <li>1. Open OBS Studio from your Applications</li>
              <li>2. Wait for it to fully load</li>
              <li>3. Come back to CliniScribe and click "Retry"</li>
            </ol>
          </div>

          <div className="flex gap-3 justify-center">
            <button
              onClick={detectOBS}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
            >
              🔄 Retry Detection
            </button>
            <button
              onClick={onSkip}
              className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Use Basic Recording
            </button>
          </div>
        </div>
      )}

      {/* Connecting */}
      {step === 'connecting' && (
        <div className="text-center">
          <div className="text-6xl mb-4">🔌</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Connecting to OBS...
          </h2>
          <p className="text-gray-600">
            Establishing WebSocket connection
          </p>
          <div className="mt-4">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </div>
      )}

      {/* Connected */}
      {step === 'connected' && connectionStatus && (
        <div className="text-center">
          <div className="text-6xl mb-4">✅</div>
          <h2 className="text-2xl font-bold text-green-700 mb-4">
            Connected to OBS Studio!
          </h2>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-green-800">
              <strong>OBS Version:</strong> {connectionStatus.obs_version}<br />
              <strong>WebSocket:</strong> {connectionStatus.websocket_version}<br />
              <strong>Features:</strong> {connectionStatus.available_features.join(', ')}
            </p>
          </div>
          <p className="text-gray-600">
            CliniScribe Pro is now ready with professional audio!
          </p>
        </div>
      )}

      {/* Error */}
      {step === 'error' && (
        <div className="text-center">
          <div className="text-6xl mb-4">🔧</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            Setup Required
          </h2>
          <p className="text-gray-600 mb-6">{error}</p>

          {obsInfo?.installed && obsInfo?.is_running && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-6 mb-6 text-left">
              <h3 className="font-semibold text-purple-900 mb-3">⚙️ Enable OBS WebSocket:</h3>
              <ol className="space-y-2 text-sm text-purple-800">
                <li>1. In OBS, click <strong>Tools</strong> → <strong>WebSocket Server Settings</strong></li>
                <li>2. Check <strong>"Enable WebSocket server"</strong></li>
                <li>3. (Optional) Set a password below</li>
                <li>4. Click <strong>OK</strong> in OBS</li>
                <li>5. Click "Connect" below</li>
              </ol>
            </div>
          )}

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              WebSocket Password (if set)
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Leave empty if no password"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex gap-3 justify-center">
            <button
              onClick={handleConnect}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
            >
              🔌 Connect
            </button>
            <button
              onClick={detectOBS}
              className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              🔄 Retry Detection
            </button>
            <button
              onClick={onSkip}
              className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Use Basic Recording
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default OBSSetupWizard;
