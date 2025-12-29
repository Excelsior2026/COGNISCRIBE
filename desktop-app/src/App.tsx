import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';
import SetupWizard from './components/SetupWizard/SetupWizard';
import Dashboard from './components/Dashboard/Dashboard';
import './styles/index.css';

interface ServiceStatus {
  ollama_running: boolean;
  api_running: boolean;
  whisper_loaded: boolean;
  deepfilter_available: boolean;
  deepfilter_binary: string | null;
  deepfilter_model: string | null;
}

interface BackendHealthResponse {
  status?: string;
  whisper?: {
    loaded?: boolean;
    error?: string;
  };
  ollama?: {
    available?: boolean;
    error?: string;
  };
}

function App() {
  const [isFirstRun, setIsFirstRun] = useState<boolean | null>(null);
  const [servicesStarted, setServicesStarted] = useState(false);
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkFirstRun();
    setupEventListeners();
  }, []);

  const checkFirstRun = async () => {
    try {
      const firstRun = await invoke<boolean>('is_first_run');
      setIsFirstRun(firstRun);

      if (!firstRun) {
        // Not first run, start services automatically
        await startServices();
      }
    } catch (err) {
      setError(`Failed to check setup status: ${err}`);
    }
  };

  const setupEventListeners = async () => {
    // Listen for service status updates
    await listen('service-status', (event: any) => {
      setServiceStatus(event.payload);
    });
  };

  const startServices = async () => {
    try {
      setError(null);
      await invoke('start_services');
      setServicesStarted(true);

      // Poll for service status
      const status = await invoke<ServiceStatus>('get_service_status');
      setServiceStatus(status);
    } catch (err) {
      setError(`Failed to start services: ${err}`);
    }
  };

  const handleSetupComplete = async () => {
    try {
      await invoke('complete_setup');
      setIsFirstRun(false);
      await startServices();
    } catch (err) {
      setError(`Setup completion failed: ${err}`);
    }
  };

  // Loading state
  if (isFirstRun === null) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-teal-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">Loading CogniScribe...</p>
        </div>
      </div>
    );
  }

  // First run - show setup wizard
  if (isFirstRun) {
    return <SetupWizard onComplete={handleSetupComplete} />;
  }

  // Services not started yet
  if (!servicesStarted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-teal-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">Starting backend services...</p>
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg max-w-md">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Main application
  return (
    <Dashboard
      serviceStatus={serviceStatus}
      onRefreshStatus={async () => {
        const status = await invoke<ServiceStatus>('get_service_status');
        setServiceStatus(status);
        return status;
      }}
      onCheckBackendHealth={async () => {
        try {
          const health = await invoke<BackendHealthResponse>('check_backend_health');
          if (health?.status === 'healthy') {
            return { healthy: true };
          }

          const issues: string[] = [];
          if (health?.whisper?.loaded === false) {
            issues.push('Transcription model still loading');
          }
          if (health?.ollama?.available === false) {
            issues.push('AI summarization service unavailable');
          }
          if (health?.whisper?.error) {
            issues.push(`Whisper: ${health.whisper.error}`);
          }
          if (health?.ollama?.error) {
            issues.push(`Ollama: ${health.ollama.error}`);
          }

          const message = issues.length
            ? issues.join('. ')
            : 'Local processing service is not responding.';

          return { healthy: false, message };
        } catch (err) {
          return {
            healthy: false,
            message: 'Local processing service is not responding. Try restarting CogniScribe.',
          };
        }
      }}
    />
  );
}

export default App;
