import React, { useState } from 'react';
import SpeechComponent from '../components/SpeechComponent';
import { Mic, Volume2, TestTube } from 'lucide-react';
import { useTranslation } from 'react-i18next'; // Import useTranslation

const SpeechTestPage = () => {
  const { t } = useTranslation(); // Initialize useTranslation
  const [testInputValue, setTestInputValue] = useState('');
  const [speechResult, setSpeechResult] = useState(null);
  const [speechError, setSpeechError] = useState(null);

  const handleSpeechEnd = (transcription, errorKey) => { // Renamed error to errorKey
    if (transcription) {
      setTestInputValue(transcription);
      setSpeechResult(transcription);
      setSpeechError(null);
    } else if (errorKey) { // Check for errorKey
      // Translate the errorKey to a user-friendly message
      // Fallback to the key itself if no translation is found
      setSpeechError(t(`speech.errors.${errorKey}`, errorKey)); 
      setSpeechResult(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 py-8 px-4">
      <div className="container mx-auto max-w-4xl">
        {/* Header Section */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full mb-4">
            <TestTube className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">{t('speechTestPage.title', 'Speech Recognition Test')}</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            {t('speechTestPage.subtitle', 'Test the speech-to-text functionality by clicking the microphone button below. Your spoken words will be transcribed and displayed in real-time.')}
          </p>
        </div>

        {/* Main Test Area */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
          <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-6">
            <h2 className="text-2xl font-semibold text-white flex items-center">
              <Mic className="w-6 h-6 mr-3" />
              {t('speechTestPage.testAreaTitle', 'Voice Input Test Area')}
            </h2>
          </div>
          
          <div className="p-8">
            {/* Input Field */}
            <div className="mb-6">
              <label htmlFor="speech-test-input" className="flex items-center text-lg font-medium text-gray-700 mb-3">
                <Volume2 className="w-5 h-5 mr-2 text-indigo-500" />
                {t('speechTestPage.transcriptionOutputLabel', 'Transcription Output:')}
              </label>
              <textarea
                id="speech-test-input"
                value={testInputValue}
                onChange={(e) => setTestInputValue(e.target.value)}
                placeholder={t('speechTestPage.transcriptionPlaceholder', 'Your spoken words will appear here...')}
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 text-lg resize-none"
                rows="4"
              />
            </div>

            {/* Speech Component */}
            <div className="flex justify-center mb-6">
              <SpeechComponent onRecordingEnd={handleSpeechEnd} />
            </div>

            {/* Success/Error Messages */}
            {speechResult && (
              <div className="bg-green-50 border-l-4 border-green-400 p-4 mb-4 rounded-r-lg">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-green-700 font-medium">{t('speechTestPage.successMessage', 'Speech successfully transcribed!')}</p>
                  </div>
                </div>
              </div>
            )}

            {speechError && (
              <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4 rounded-r-lg">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-700 font-medium">{t('speechTestPage.errorMessage', 'Error:')} {speechError}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Instructions */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-blue-800 mb-3">{t('speechTestPage.instructionsTitle', 'How to Test:')}</h3>
              <ol className="list-decimal list-inside space-y-2 text-blue-700">
                <li>{t('speechTestPage.instruction1', 'Click the microphone button to start recording')}</li>
                <li>{t('speechTestPage.instruction2', 'Speak clearly into your device\'s microphone')}</li>
                <li>{t('speechTestPage.instruction3', 'Click the stop button when finished')}</li>
                <li>{t('speechTestPage.instruction4', 'Your speech will be transcribed and displayed above')}</li>
              </ol>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-8 grid md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-lg p-6 text-center">
            <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Mic className="w-6 h-6 text-indigo-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">{t('speechTestPage.feature1Title', 'Real-time Transcription')}</h3>
            <p className="text-gray-600">{t('speechTestPage.feature1Desc', 'Instant speech-to-text conversion with high accuracy')}</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 text-center">
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Volume2 className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">{t('speechTestPage.feature2Title', 'Multi-language Support')}</h3>
            <p className="text-gray-600">{t('speechTestPage.feature2Desc', 'Supports multiple languages for global accessibility')}</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 text-center">
            <div className="w-12 h-12 bg-cyan-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <TestTube className="w-6 h-6 text-cyan-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">{t('speechTestPage.feature3Title', 'Easy Testing')}</h3>
            <p className="text-gray-600">{t('speechTestPage.feature3Desc', 'Simple interface for testing speech recognition')}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpeechTestPage;
