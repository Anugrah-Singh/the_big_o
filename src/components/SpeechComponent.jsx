import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const SpeechComponent = ({ onRecordingEnd }) => { // Removed targetInputSelector prop
  const { t, i18n } = useTranslation();
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);

  const backendUrl = import.meta.env.VITE_BACKEND_API_URL
    ? `${import.meta.env.VITE_BACKEND_API_URL.replace(/\/$/, '')}/translate`
    : '/transcribe';

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  const handleStartRecording = async () => {
    if (isRecording) return;

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.warn(t('speech.mic_not_supported'));
      if (onRecordingEnd) onRecordingEnd(null, 'mic_not_supported');
      return;
    }

    try {
      console.log(t('speech.requesting_permission'));
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const preferredMimeTypes = [
        'audio/wav',
        'audio/ogg;codecs=opus',
        'audio/ogg',
        'audio/mpeg',
        'audio/mp4',
      ];

      let supportedMimeType = '';
      for (const mimeType of preferredMimeTypes) {
        if (MediaRecorder.isTypeSupported(mimeType)) {
          supportedMimeType = mimeType;
          break;
        }
        console.warn(`MIME type ${mimeType} not supported.`);
      }

      if (!supportedMimeType) {
        console.error('Browser does not support any of the preferred audio recording formats (WAV, OGG, MP3, MP4).');
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
        if (onRecordingEnd) onRecordingEnd(null, 'no_supported_format');
        return;
      }
      
      console.log(`Using MIME type: ${supportedMimeType}`);
      
      const options = { mimeType: supportedMimeType };
      
      mediaRecorderRef.current = new MediaRecorder(stream, options);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        if (audioChunksRef.current.length === 0) {
          console.log(t('speech.no_audio_data'));
          // setIsRecording(false); // This will be handled by sendAudioToBackend or its absence
          if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
          }
          if (onRecordingEnd) onRecordingEnd(null, 'no_audio_data');
          setIsRecording(false); // Explicitly set here as sendAudioToBackend won't be called
          return;
        }
        const audioBlob = new Blob(audioChunksRef.current, { type: options.mimeType });
        audioChunksRef.current = [];
        await sendAudioToBackend(audioBlob, options.mimeType); 
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
      };
      
      mediaRecorderRef.current.onerror = (event) => {
        console.error('MediaRecorder error:', event.error);
        setIsRecording(false);
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        if (onRecordingEnd) onRecordingEnd(null, `recorder_error: ${event.error.name}`);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      console.log(t('speech.recording_in_progress'));
    } catch (error) {
      console.error('Error accessing microphone:', error);
      let errorKey = 'mic_error';
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        errorKey = 'mic_permission_denied';
      }
      setIsRecording(false);
      if (onRecordingEnd) onRecordingEnd(null, errorKey);
    }
  };

  const handleStopRecording = () => {
    if (!isRecording || !mediaRecorderRef.current || mediaRecorderRef.current.state !== 'recording') {
      console.warn('Stop recording called in an invalid state:', { isRecording, mediaRecorderState: mediaRecorderRef.current?.state });
      // If not recording but stop is called, ensure state is clean.
      // This might happen if an error occurred before user explicitly stopped.
      if (!isRecording) {
         if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
      }
      return;
    }
    
    console.log(t('speech.stopping_recording'));
    mediaRecorderRef.current.stop(); 
  };

  const sendAudioToBackend = async (audioBlob, mimeType) => {
    const formData = new FormData();
    let fileExtension = mimeType.split('/')[1];
    if (fileExtension.includes(';')) {
      fileExtension = fileExtension.split(';')[0];
    }

    if (fileExtension === 'mpeg') {
      fileExtension = 'mp3';
    }

    formData.append('audio', audioBlob, `recording.${fileExtension}`);
    formData.append('language', i18n.language);
    
    try {
      console.log(t('speech.sending_audio'));
      const response = await axios.post(backendUrl, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const result = response.data;
      if (result && typeof result.transcription === 'string') {
        console.log(t('speech.transcription_received_updated'));
        if (onRecordingEnd) onRecordingEnd(result.transcription, null);
      } else {
        console.warn('SpeechComponent: Invalid transcription format from backend.', result);
        if (onRecordingEnd) onRecordingEnd(null, 'invalid_transcription_format');
      }
    } catch (error) {
      console.error('Error sending audio to backend or processing response:', error);
      let specificErrorKey = 'generic_send_error';
      if (axios.isAxiosError(error) && error.response) {
        const backendErrorMessage = error.response.data?.error || error.response.data?.detail || error.response.data?.message || error.response.statusText || t('speech.unknown_backend_error');
        console.error(t('speech.backend_error_status', { status: error.response.status, backendErrorMessage }));
        specificErrorKey = `backend_error_${error.response.status}`;
      } else if (error.request) {
        console.error(t('speech.no_response_from_server'));
        specificErrorKey = 'no_server_response';
      } else {
        console.error(t('speech.error_message', { errorMessage: error.message }));
      }
      if (onRecordingEnd) onRecordingEnd(null, specificErrorKey);
    } finally {
      setIsRecording(false);
    }
  };

  const buttonText = isRecording ? t('speech.stop_recording_button') : t('speech.start_recording_button');
  const canRecord = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);

  return (
    <button
      onClick={isRecording ? handleStopRecording : handleStartRecording}
      disabled={!canRecord}
      className={`text-white font-semibold uppercase py-2 px-4 sm:py-3 sm:px-5 rounded-lg shadow-md transition-colors duration-150 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-opacity-50 ${
        !canRecord
          ? 'bg-gray-400 cursor-not-allowed'
          : isRecording
          ? 'bg-red-500 hover:bg-red-600 focus:ring-red-500' // Brighter red
          : 'bg-blue-500 hover:bg-blue-600 focus:ring-blue-500' // Brighter blue
      }`}
      title={!canRecord ? t('speech.mic_not_supported_message') : buttonText}
    >
      {buttonText}
    </button>
  );
};

export default SpeechComponent;
