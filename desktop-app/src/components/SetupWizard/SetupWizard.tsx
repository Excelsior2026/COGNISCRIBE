import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';
import WelcomeStep from './WelcomeStep';
import ModelDownloadStep from './ModelDownloadStep';
import CompletionStep from './CompletionStep';
import OBSSetupWizard from '../OBS/OBSSetupWizard';

interface SetupWizardProps {
  onComplete: () => void;
}

type SetupStep = 'welcome' | 'download' | 'complete' | 'obs';

function SetupWizard({ onComplete }: SetupWizardProps) {
  const [currentStep, setCurrentStep] = useState<SetupStep>('welcome');
  const [downloadProgress, setDownloadProgress] = useState<any>(null);
  const [bundledModelsInstalled, setBundledModelsInstalled] = useState<boolean>(false);

  // Check for bundled models on mount
  useEffect(() => {
    const checkBundledModels = async () => {
      try {
        const hasBundledModels = await invoke<boolean>('check_bundled_models');
        setBundledModelsInstalled(hasBundledModels);

        if (hasBundledModels) {
          console.log('Bundled models detected - skipping download step');
        }
      } catch (err) {
        console.error('Failed to check for bundled models:', err);
        setBundledModelsInstalled(false);
      }
    };

    checkBundledModels();
  }, []);

  const handleNext = () => {
    if (currentStep === 'welcome') {
      // Skip download step if bundled models are installed
      if (bundledModelsInstalled) {
        setCurrentStep('complete');
      } else {
        setCurrentStep('download');
        startModelDownloads();
      }
    } else if (currentStep === 'download') {
      setCurrentStep('complete');
    } else if (currentStep === 'complete') {
      // After basic setup, offer OBS setup
      setCurrentStep('obs');
    } else if (currentStep === 'obs') {
      onComplete();
    }
  };

  const handleObsComplete = (_connected: boolean) => {
    onComplete();
  };

  const handleObsSkip = () => {
    onComplete();
  };

  const startModelDownloads = async () => {
    // Listen for download progress
    await listen('download-progress', (event: any) => {
      setDownloadProgress(event.payload);
    });

    try {
      // Download Whisper model
      await invoke('download_model', { modelType: 'whisper' });

      // Download Llama model
      await invoke('download_model', { modelType: 'llama' });

      // Both downloads complete
      setTimeout(() => {
        setCurrentStep('complete');
      }, 1000);
    } catch (err) {
      console.error('Model download failed:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-teal-50">
      {currentStep === 'welcome' && (
        <WelcomeStep
          onNext={handleNext}
          bundledModelsInstalled={bundledModelsInstalled}
        />
      )}
      {currentStep === 'download' && (
        <ModelDownloadStep
          progress={downloadProgress}
          onNext={handleNext}
        />
      )}
      {currentStep === 'complete' && <CompletionStep onNext={handleNext} />}
      {currentStep === 'obs' && (
        <div className="flex items-center justify-center min-h-screen p-8">
          <div className="max-w-3xl w-full">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-gray-800 mb-4">
                🎚️ CliniScribe Pro
              </h1>
              <p className="text-lg text-gray-600">
                Optional: Connect OBS Studio for professional audio recording
              </p>
            </div>
            <OBSSetupWizard
              onComplete={handleObsComplete}
              onSkip={handleObsSkip}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default SetupWizard;
