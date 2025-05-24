import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom'; // Added import
import SpeechComponent from './SpeechComponent';
import { Send, MessageSquare, AlertTriangle } from 'lucide-react';

const ChatBot = () => {
  const { t } = useTranslation();
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
      // Prepare the data to be sent, ensuring the user's message updates the description
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

      const response = await axios.post(chatBotApiUrl, {
        answer: userMessage, 
        template: dataToSend, 
        conversation_history: conversationHistory // Send current conversation history
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