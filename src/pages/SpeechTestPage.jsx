import React, { useState } from 'react';
import SpeechComponent from '../components/SpeechComponent'; // Adjust path if necessary

const SpeechTestPage = () => {
  const [testInputValue, setTestInputValue] = useState('');

  return (
    <div className="container mx-auto p-8 mt-8 border-t-2 border-dashed border-gray-400">
      <h2 className="text-2xl font-semibold mb-4 text-center">Speech Component Test Area</h2>
      <p className="text-center mb-6 text-gray-600">
        Use the microphone button below to test speech-to-text.
        The transcribed text will appear in the input field.
      </p>
      <div className="max-w-md mx-auto bg-white p-6 rounded-lg shadow-md">
        <div className="mb-4">
          <label htmlFor="speech-test-input" className="block text-sm font-medium text-gray-700 mb-1">
            Test Input Field:
          </label>
          <input
            type="text"
            id="speech-test-input"
            value={testInputValue}
            onChange={(e) => setTestInputValue(e.target.value)}
            placeholder="Transcription will appear here..."
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>
        <SpeechComponent targetInputSelector="#speech-test-input" />
      </div>
    </div>
  );
};

export default SpeechTestPage;
