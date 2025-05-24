import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom'; // Added import
import SpeechComponent from './SpeechComponent';
import { Send, MessageSquare, AlertTriangle } from 'lucide-react';

const ChatBot = () => {
  const { t, i18n } = useTranslation(); // Destructure i18n here
  const navigate = useNavigate(); // Added initialization
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isVoiceInputActive, setIsVoiceInputActive] = useState(false);
  const [speechErrorKey, setSpeechErrorKey] = useState(null);
  const [conversationHistory, setConversationHistory] = useState([]); // Add state for conversation history

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const chatBotApiUrl = import.meta.env.VITE_CHATBOT_API_URL;

  const initialSymptomData = {
    name: "string", // Placeholder, consider fetching from auth context or a form
    age: 0, // Placeholder, consider fetching from auth context or a form
    symptoms: [
      {
        symptom: "string", // This could be the userMessage or part of it
        onset: "string",
        severity: "string"
      }
    ],
    medical_history: {
      conditions: ["string"],
      allergies: ["string"]
    }
  };

  const [currentSymptomData, setCurrentSymptomData] = useState(initialSymptomData);

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
      // Prepare the data to be sent, ensuring the user\'s message updates the description
      const dataToSend = {
        ...currentSymptomData,
        symptoms: currentSymptomData.symptoms.map((symptomItem, index) =>
          index === 0 ? { ...symptomItem, symptom: userMessage } : symptomItem
        ),
        // If no symptoms exist, create one with the user message
        ...(currentSymptomData.symptoms.length === 0 && {
          symptoms: [{ ...initialSymptomData.symptoms[0], symptom: userMessage }]
        })
      };
      if (dataToSend.symptoms.length > 0 && dataToSend.symptoms[0].symptom === "" && userMessage) {
          dataToSend.symptoms[0].symptom = userMessage;
      }

      const currentLanguageCode = i18n.language;
      const currentLanguageFullName = t(`languages.${currentLanguageCode}`);

      const response = await axios.post(chatBotApiUrl, {
        answer: userMessage, 
        template: dataToSend, 
        conversation_history: conversationHistory, // Send current conversation history
        language: currentLanguageFullName // Send the full language name
      });
      
      console.log("Backend Response:", response); // Log the full response object
      const data = response.data;
      console.log("Response Data:", data); // Log the data part of the response
      let messageText;

      // Update currentSymptomData if updated_template is received
      if (data && data.updated_template && typeof data.updated_template === 'object') {
        setCurrentSymptomData(data.updated_template);
      }

      // Update conversationHistory if received from backend
      if (data && Array.isArray(data.conversation_history)) {
        setConversationHistory(data.conversation_history);
      }

      // Check for completion and redirect
      if (data && data.complete === true) {
        let finalSummaryReport;
        const templateSource = data.updated_template || currentSymptomData;

        if (templateSource && typeof templateSource === 'object') {
          const { name, age, symptoms, medical_history } = templateSource;
          let summaryString = `Patient Name: ${name || 'N/A'}\nAge: ${age || 'N/A'}\n\nSymptoms:\n`;
          if (symptoms && symptoms.length > 0) {
            symptoms.forEach(symptom => {
              summaryString += `  - ${symptom.symptom || 'N/A'}`;
              if (symptom.location) summaryString += ` (Location: ${symptom.location})`;
              if (symptom.onset) summaryString += ` (Onset: ${symptom.onset})`;
              if (symptom.severity) summaryString += ` (Severity: ${symptom.severity})`;
              summaryString += '\n';
            });
          } else {
            summaryString += '  No symptoms detailed.\n';
          }
          summaryString += '\nMedical History:\n';
          if (medical_history) {
            summaryString += `  Known Conditions: ${(medical_history.conditions && medical_history.conditions.length > 0) ? medical_history.conditions.join(', ') : 'None'}\n`;
            summaryString += `  Allergies: ${(medical_history.allergies && medical_history.allergies.length > 0) ? medical_history.allergies.join(', ') : 'None'}\n`;
          } else {
            summaryString += '  No medical history detailed.\n';
          }
          finalSummaryReport = summaryString;
        } else if (data.summary_report) {
          finalSummaryReport = data.summary_report;
        } else {
          finalSummaryReport = t('summaryPage.defaultSummary', 'No summary provided.');
        }

        navigate('/summary', { 
          state: { 
            summaryReport: finalSummaryReport, 
            possibleRemedies: data.possible_remedies, 
            diagnosticsTests: data.diagnostics_tests,
            patientName: templateSource.name || currentSymptomData.name || t('summaryPage.defaultPatientName', 'Patient') 
          } 
        });
        return; // Stop further processing in handleSubmit
      }

      if (data && data.reply && typeof data.reply === 'string' && data.reply.trim() !== '') {
        messageText = data.reply;
      } else if (data && data.next_question && typeof data.next_question === 'string' && data.next_question.trim() !== '') {
        messageText = data.next_question;
      } else if (data && typeof data === 'object') {
        const templateToUse = data.updated_template || currentSymptomData; // Use updated or current state
        // Attempt to find a meaningful field in the template for display, e.g., a general notes or summary
        // This part might need adjustment based on how the new template structure is used by the bot
        if (templateToUse.symptoms && templateToUse.symptoms.length > 0 && templateToUse.symptoms[0].symptom) {
            messageText = t('chatbot.received_data_summary_v2', { symptom: templateToUse.symptoms[0].symptom });
        } else {
          messageText = t('chatbot.received_data_summary', "I've processed the information. Is there anything else I can help with?");
        }
      } else {
        messageText = t('chatbot.default_reply', "Sorry, I received a response I couldn't understand.");
      }

      setMessages([...newMessages, { text: messageText, sender: 'bot' }]);
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
    <div className="flex flex-col h-[calc(100vh-120px)] max-w-4xl mx-auto bg-white shadow-2xl rounded-2xl overflow-hidden border border-gray-200">
      {/* Enhanced Header */}
      <header className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-700 text-white p-6 flex items-center justify-between shadow-lg">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-white/20 rounded-xl backdrop-blur-sm">
            <MessageSquare size={32} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">{t('chatbot.newTitle')}</h1>
            <p className="text-blue-100 text-sm">{t('chatbot.subtitle', 'Your AI Health Assistant')}</p>
          </div>
        </div>
        <div className="hidden sm:flex items-center space-x-2 text-sm bg-white/10 px-3 py-1 rounded-full">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-blue-100">{t('chatbot.online', 'Online')}</span>
        </div>
      </header>

      {/* Display Speech Error */}
      {speechErrorKey && (
        <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-xl shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-100 rounded-full">
              <AlertTriangle size={20} className="text-red-500" />
            </div>
            <div>
              <p className="text-red-800 font-medium">{t('chatbot.speechError', 'Voice Input Error')}</p>
              <p className="text-red-600 text-sm">{t(speechErrorKey, { defaultValue: "Voice input error" })}</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Display General Error */}
      {error && !speechErrorKey && (
        <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-xl shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-100 rounded-full">
              <AlertTriangle size={20} className="text-red-500" />
            </div>
            <div>
              <p className="text-red-800 font-medium">{t('chatbot.error', 'Error')}</p>
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Enhanced Messages Area */}
      <div className="flex-grow p-6 space-y-6 overflow-y-auto bg-gradient-to-b from-gray-50 to-white custom-scrollbar">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <MessageSquare size={32} className="text-blue-500" />
            </div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">{t('chatbot.welcomeTitle', 'Welcome to Your AI Health Assistant')}</h3>
            <p className="text-gray-600 max-w-md mx-auto">{t('chatbot.welcomeMessage', 'Start by describing your symptoms or health concerns. I\'m here to help you understand your health better.')}</p>
            <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-lg mx-auto">
              <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
                <h4 className="font-medium text-blue-900 mb-1">{t('chatbot.feature1', 'Symptom Analysis')}</h4>
                <p className="text-blue-700 text-sm">{t('chatbot.feature1Desc', 'Describe your symptoms for personalized insights')}</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-xl border border-purple-100">
                <h4 className="font-medium text-purple-900 mb-1">{t('chatbot.feature2', 'Voice Support')}</h4>
                <p className="text-purple-700 text-sm">{t('chatbot.feature2Desc', 'Use voice input for hands-free interaction')}</p>
              </div>
            </div>
          </div>
        )}
        
        {messages.map((msg, index) => (
          <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} items-end space-x-2`}>
            {msg.sender === 'bot' && (
              <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center shadow-lg">
                <MessageSquare size={16} className="text-white" />
              </div>
            )}
            
            <div className={`max-w-xs lg:max-w-md ${msg.sender === 'user' ? 'order-1' : 'order-2'}`}>
              <div
                className={`px-4 py-3 rounded-2xl shadow-md transition-all duration-200 hover:shadow-lg ${
                  msg.sender === 'user'
                    ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-md'
                    : msg.isError
                    ? 'bg-gradient-to-r from-red-400 to-red-500 text-white rounded-bl-md'
                    : 'bg-white border border-gray-200 text-gray-800 rounded-bl-md'
                }`}
              >
                {msg.text}
              </div>
              <div className={`text-xs text-gray-500 mt-1 ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}>
                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
            
            {msg.sender === 'user' && (
              <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center shadow-lg">
                <span className="text-white font-semibold text-sm">U</span>
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Enhanced Input Form */}
      <form onSubmit={handleSubmit} className="p-6 border-t border-gray-200 bg-white">
        <div className="flex items-center space-x-4">
          {/* Speech Component */}
          <div className="flex-shrink-0">
            <SpeechComponent 
              onRecordingEnd={handleSpeechRecognitionEnd}
            />
          </div>
          
          {/* Input Field */}
          <div className="flex-grow relative">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={handleInputChange}
              placeholder={isVoiceInputActive ? t('chatbot.voice_input_active_placeholder') : t('chatbot.input_placeholder')}
              className="w-full p-4 pr-12 border-2 border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all duration-200 disabled:bg-gray-100 disabled:text-gray-500 text-gray-800 placeholder-gray-500"
              disabled={isLoading || isVoiceInputActive}
            />
            {(input.trim() || isVoiceInputActive) && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              </div>
            )}
          </div>
          
          {/* Send Button */}
          <button
            type="submit"
            disabled={isLoading || (!input.trim() && !isVoiceInputActive)}
            className="flex-shrink-0 w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-2xl hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-4 focus:ring-blue-500/20 transition-all duration-200 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed flex items-center justify-center shadow-lg hover:shadow-xl transform hover:scale-105 disabled:transform-none"
            aria-label={t('chatbot.send_button_aria_label')}
          >
            {isLoading ? (
              <svg className="animate-spin h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <Send size={22} />
            )}
          </button>
        </div>
        
        {/* Input Helper Text */}
        <div className="mt-3 flex items-center justify-between text-sm text-gray-500">
          <span>{t('chatbot.inputHelper', 'Type your message or use voice input')}</span>
          <span className="text-xs">{input.length}/500</span>
        </div>
      </form>
    </div>
  );
};

export default ChatBot;