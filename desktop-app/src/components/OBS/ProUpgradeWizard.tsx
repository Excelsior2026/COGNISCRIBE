import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';

interface OBSInstallProgress {
  stage: string;
  progress: number;
  message: string;
}

interface ProUpgradeWizardProps {
  onComplete: () => void;
  onCancel: () => void;
}

type UpgradeStep = 'intro' | 'payment' | 'installing' | 'configuring' | 'launching' | 'complete' | 'error';

function ProUpgradeWizard({ onComplete, onCancel }: ProUpgradeWizardProps) {
  const [step, setStep] = useState<UpgradeStep>('intro');
  const [installProgress, setInstallProgress] = useState<OBSInstallProgress | null>(null);
  const [error, setError] = useState<string>('');
  const [isPaid, setIsPaid] = useState(false); // This will integrate with payment system

  // Listen for OBS installation progress
  useEffect(() => {
    const unlisten = listen<OBSInstallProgress>('obs-install-progress', (event) => {
      setInstallProgress(event.payload);

      // Update step based on progress stage
      if (event.payload.stage === 'downloading') {
        setStep('installing');
      } else if (event.payload.stage === 'downloaded') {
        setStep('installing');
      } else if (event.payload.stage === 'installed') {
        setStep('configuring');
      }
    });

    return () => {
      unlisten.then(f => f());
    };
  }, []);

  const handleStartUpgrade = () => {
    // In production, this would trigger payment flow first
    setStep('payment');
  };

  const handlePaymentComplete = () => {
    setIsPaid(true);
    startOBSInstallation();
  };

  const startOBSInstallation = async () => {
    try {
      setStep('installing');

      // Download and install OBS
      await invoke('obs_download_and_install');

      // Configure OBS
      setStep('configuring');
      await invoke('obs_configure');

      // Launch OBS
      setStep('launching');
      await invoke('obs_launch');

      // Wait a moment for OBS to start
      await new Promise(resolve => setTimeout(resolve, 3000));

      // Try to connect
      try {
        await invoke('obs_connect', {
          host: 'localhost',
          port: 4455,
          password: null,
        });
      } catch (err) {
        console.warn('Could not auto-connect to OBS, user can connect manually');
      }

      setStep('complete');
    } catch (err) {
      setStep('error');
      setError(err instanceof Error ? err.message : 'Installation failed');
    }
  };

  const handleSkipInstall = async () => {
    // User already has OBS, just configure and connect
    try {
      setStep('configuring');
      await invoke('obs_configure');

      setStep('launching');
      await invoke('obs_launch');

      await new Promise(resolve => setTimeout(resolve, 3000));

      try {
        await invoke('obs_connect', {
          host: 'localhost',
          port: 4455,
          password: null,
        });
      } catch (err) {
        console.warn('Could not auto-connect to OBS');
      }

      setStep('complete');
    } catch (err) {
      setStep('error');
      setError(err instanceof Error ? err.message : 'Configuration failed');
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-8 bg-white rounded-2xl shadow-xl">
      {/* Intro Step */}
      {step === 'intro' && (
        <div className="text-center">
          <div className="text-6xl mb-6">🎚️</div>
          <h2 className="text-3xl font-bold text-gray-800 mb-4">
            Upgrade to CliniScribe Pro
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            Get professional-quality audio recording with OBS Studio integration
          </p>

          <div className="bg-gradient-to-br from-purple-50 to-blue-50 border-2 border-purple-200 rounded-xl p-8 mb-8">
            <h3 className="text-xl font-semibold text-purple-900 mb-4">
              What's Included:
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
              <div className="flex items-start gap-3">
                <div className="text-2xl">🎙️</div>
                <div>
                  <h4 className="font-semibold text-gray-800">Pro Audio Recording</h4>
                  <p className="text-sm text-gray-600">Multi-track recording with professional filters</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="text-2xl">🔊</div>
                <div>
                  <h4 className="font-semibold text-gray-800">Noise Reduction</h4>
                  <p className="text-sm text-gray-600">AI-powered RNNoise suppression</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="text-2xl">⚙️</div>
                <div>
                  <h4 className="font-semibold text-gray-800">Audio Presets</h4>
                  <p className="text-sm text-gray-600">Optimized for lecture halls, clinical skills, online</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="text-2xl">🚀</div>
                <div>
                  <h4 className="font-semibold text-gray-800">Automatic Setup</h4>
                  <p className="text-sm text-gray-600">We'll install and configure OBS for you</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> This will automatically download and install OBS Studio (free, open-source software).
              The entire process takes about 2-3 minutes.
            </p>
          </div>

          <div className="flex gap-4 justify-center">
            <button
              onClick={handleStartUpgrade}
              className="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-lg font-semibold rounded-xl hover:from-purple-700 hover:to-blue-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              Upgrade to Pro - $XX.XX/month
            </button>
            <button
              onClick={onCancel}
              className="px-8 py-4 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition-colors"
            >
              Maybe Later
            </button>
          </div>

          <button
            onClick={handleSkipInstall}
            className="mt-4 text-sm text-blue-600 hover:text-blue-700 underline"
          >
            I already have OBS installed
          </button>
        </div>
      )}

      {/* Payment Step */}
      {step === 'payment' && (
        <div className="text-center">
          <div className="text-6xl mb-4">💳</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            Complete Your Purchase
          </h2>
          <p className="text-gray-600 mb-8">
            Enter your payment information to activate CliniScribe Pro
          </p>

          {/* Payment form will go here - integrate with Stripe/Paddle/etc */}
          <div className="bg-gray-100 border-2 border-dashed border-gray-300 rounded-xl p-12 mb-6">
            <p className="text-gray-500 mb-4">Payment Integration Placeholder</p>
            <p className="text-sm text-gray-400">
              Integrate with Stripe, Paddle, or other payment provider
            </p>
          </div>

          <div className="flex gap-4 justify-center">
            <button
              onClick={handlePaymentComplete}
              className="px-8 py-3 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition-colors"
            >
              [Demo] Complete Payment
            </button>
            <button
              onClick={onCancel}
              className="px-8 py-3 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Installing Step */}
      {step === 'installing' && (
        <div className="text-center">
          <div className="text-6xl mb-4 animate-bounce">📥</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            Installing OBS Studio
          </h2>
          <p className="text-gray-600 mb-8">
            {installProgress?.message || 'Downloading OBS Studio...'}
          </p>

          <div className="w-full bg-gray-200 rounded-full h-4 mb-4">
            <div
              className="bg-gradient-to-r from-purple-600 to-blue-600 h-4 rounded-full transition-all duration-300"
              style={{ width: `${installProgress?.progress || 0}%` }}
            ></div>
          </div>

          <p className="text-sm text-gray-500">
            {installProgress?.progress.toFixed(0)}% complete
          </p>

          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              Please wait while we download and install OBS Studio. This may take a few minutes depending on your internet connection.
            </p>
          </div>
        </div>
      )}

      {/* Configuring Step */}
      {step === 'configuring' && (
        <div className="text-center">
          <div className="text-6xl mb-4">⚙️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            Configuring OBS
          </h2>
          <p className="text-gray-600 mb-8">
            Setting up WebSocket, audio sources, and professional filters...
          </p>

          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mb-4"></div>

          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <p className="text-sm text-purple-800">
              Configuring optimal settings for lecture recording
            </p>
          </div>
        </div>
      )}

      {/* Launching Step */}
      {step === 'launching' && (
        <div className="text-center">
          <div className="text-6xl mb-4">🚀</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            Launching OBS Studio
          </h2>
          <p className="text-gray-600 mb-8">
            Starting OBS and connecting to CliniScribe...
          </p>

          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
        </div>
      )}

      {/* Complete Step */}
      {step === 'complete' && (
        <div className="text-center">
          <div className="text-6xl mb-4">✅</div>
          <h2 className="text-2xl font-bold text-green-700 mb-4">
            Welcome to CliniScribe Pro!
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            OBS Studio is installed and configured. You're ready to record with professional audio quality!
          </p>

          <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-8">
            <h3 className="font-semibold text-green-900 mb-3">Next Steps:</h3>
            <ol className="text-left space-y-2 text-sm text-green-800">
              <li>1. OBS Studio is now running in the background</li>
              <li>2. Select "Pro Recording" mode in CliniScribe</li>
              <li>3. Choose your microphone and audio preset</li>
              <li>4. Start recording with professional quality!</li>
            </ol>
          </div>

          <button
            onClick={onComplete}
            className="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-lg font-semibold rounded-xl hover:from-purple-700 hover:to-blue-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
          >
            Start Using Pro Features
          </button>
        </div>
      )}

      {/* Error Step */}
      {step === 'error' && (
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            Installation Error
          </h2>
          <p className="text-gray-600 mb-6">{error}</p>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6 text-left">
            <h3 className="font-semibold text-yellow-900 mb-3">Manual Installation:</h3>
            <ol className="space-y-2 text-sm text-yellow-800">
              <li>1. Visit <a href="https://obsproject.com" target="_blank" rel="noopener noreferrer" className="underline font-semibold">obsproject.com</a></li>
              <li>2. Download and install OBS Studio manually</li>
              <li>3. Return to CliniScribe and try connecting again</li>
            </ol>
          </div>

          <div className="flex gap-4 justify-center">
            <button
              onClick={() => setStep('intro')}
              className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={onCancel}
              className="px-6 py-3 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ProUpgradeWizard;
