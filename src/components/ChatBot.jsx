import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import SpeechComponent from './SpeechComponent';
import { Send, MessageSquare, AlertTriangle } from 'lucide-react';

const ChatBot = () => {
  const { t } = useTranslation();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isVoiceInputActive, setIsVoiceInputActive] = useState(false);
  const [speechErrorKey, setSpeechErrorKey] = useState(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const chatBotApiUrl = import.meta.env.VITE_CHATBOT_API_URL;

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleInputChange = (e) => {
    setInput(e.target.value);
    if (speechErrorKey) setSpeechErrorKey(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() && !isVoiceInputActive) {
      setError(t('chatbot.please_enter_message'));
      return;
    }
    
    const userMessage = input.trim() || (isVoiceInputActive ? t('chatbot.voice_input_active_placeholder') : "Audio input");
    if (!userMessage && !isVoiceInputActive) return;

    const newMessages = [...messages, { text: userMessage, sender: 'user' }];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);
    setError(null);
    setSpeechErrorKey(null);
    setIsVoiceInputActive(false);

    try {
      const response = await axios.post(chatBotApiUrl, {
        message: userMessage,
      });
      
      const botMessage = response.data.reply || response.data.message || "Sorry, I didn't understand that.";
      setMessages([...newMessages, { text: botMessage, sender: 'bot' }]);
    } catch (err) {
      console.error("Error sending message to chatbot API:", err);
      const errMsg = err.response?.data?.error || t('chatbot.unexpected_error');
      setMessages([...newMessages, { text: errMsg, sender: 'bot', isError: true }]);
      setError(errMsg);
    } finally {
      setIsLoading(false);
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }
  };

  const handleSpeechRecognitionEnd = (transcribedText, errorKey) => {
    setIsVoiceInputActive(false);
    if (errorKey) {
      console.error("Speech recognition error:", errorKey);
      setSpeechErrorKey(errorKey);
      setInput('');
    } else if (transcribedText) {
      setInput(transcribedText);
      setSpeechErrorKey(null);
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] max-w-3xl mx-auto bg-white shadow-xl rounded-lg overflow-hidden">
      <header className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 sm:p-6 flex items-center">
        <MessageSquare size={28} className="mr-3" />
        <h1 className="text-xl sm:text-2xl font-semibold">{t('chatbot.newTitle')}</h1>
      </header>

      {/* Display Speech Error */}
      {speechErrorKey && (
        <div className="p-3 bg-red-100 border-l-4 border-red-500 text-red-700">
          <div className="flex items-center">
            <AlertTriangle size={20} className="mr-2" />
            <p>{t(speechErrorKey, { defaultValue: "Voice input error" })}</p>
          </div>
        </div>
      )}
      
      {/* Display General Error */}
      {error && !speechErrorKey && ( // Only show general error if no specific speech error
        <div className="p-3 bg-red-100 border-l-4 border-red-500 text-red-700">
           <div className="flex items-center">
            <AlertTriangle size={20} className="mr-2" />
            <p>{error}</p>
          </div>
        </div>
      )}

      <div className="flex-grow p-4 sm:p-6 space-y-4 overflow-y-auto bg-gray-50">
        {messages.map((msg, index) => (
          <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-xl shadow ${
                msg.sender === 'user'
                  ? 'bg-blue-500 text-white rounded-br-none'
                  : msg.isError
                  ? 'bg-red-400 text-white rounded-bl-none'
                  : 'bg-gray-200 text-gray-800 rounded-bl-none'
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} /> {/* For auto-scrolling */}
      </div>

      <form onSubmit={handleSubmit} className="p-3 sm:p-4 border-t border-gray-200 bg-white flex items-center space-x-2">
        <SpeechComponent 
          onRecordingEnd={handleSpeechRecognitionEnd}
        />
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={handleInputChange}
          placeholder={isVoiceInputActive ? t('chatbot.voice_input_active_placeholder') : t('chatbot.input_placeholder')}
          className="flex-grow p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-shadow disabled:bg-gray-100"
          disabled={isLoading || isVoiceInputActive}
        />
        <button
          type="submit"
          disabled={isLoading || (!input.trim() && !isVoiceInputActive)}
          className="p-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
          aria-label={t('chatbot.send_button_aria_label')}
        >
          {isLoading ? (
            <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          ) : (
            <Send size={20} />
          )}
        </button>
      </form>
    </div>
  );
};

export default ChatBot;