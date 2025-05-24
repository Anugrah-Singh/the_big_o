import streamlit as st
from st_audiorec import st_audiorec
import dwani
import os
import tempfile
import logging
import wave
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Dwani API Configuration ---
DWANI_API_KEY = 'abhishekr.23.becs@acharya.ac.in_dwani_krishnadevaraya'
DWANI_API_BASE = 'https://dwani-dwani-api.hf.space'

# Configure Dwani API
dwani.api_key = DWANI_API_KEY
dwani.api_base = DWANI_API_BASE

# Set API base for ASR module
if hasattr(dwani, 'ASR') and dwani.ASR is not None:
    dwani.ASR.api_base = DWANI_API_BASE
    logger.info(f"Configured Dwani ASR with API base: {DWANI_API_BASE}")

# Set environment variables as fallback
os.environ['DWANI_API_BASE'] = DWANI_API_BASE
os.environ['DWANI_API_KEY'] = DWANI_API_KEY

def validate_audio_file(file_path, audio_bytes):
    """Validate audio file for transcription requirements"""
    try:
        # Check if file exists and has content
        if not os.path.exists(file_path):
            return False, "Audio file not found"
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, "Audio file is empty"
        
        # Check minimum file size (e.g., at least 1KB)
        if file_size < 1024:
            return False, "Audio file too small. Please record for at least 2-3 seconds"
        
        # Check audio duration using wave module for basic validation
        try:
            with wave.open(file_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                duration = frames / float(sample_rate)
                
                # Require minimum 1 second of audio
                if duration < 1.0:
                    return False, f"Audio too short ({duration:.1f}s). Please record for at least 2-3 seconds"
                
                logger.info(f"Audio validation passed: {duration:.1f}s duration, {file_size} bytes")
                return True, f"Audio ready: {duration:.1f}s duration"
                
        except wave.Error as e:
            # If wave module fails, try alternative validation
            logger.warning(f"Wave validation failed: {e}")
            
            # Basic size-based validation as fallback
            if file_size > 10000:  # At least 10KB suggests reasonable audio content
                return True, "Audio file appears valid (fallback validation)"
            else:
                return False, "Audio file appears invalid or too short"
                
    except Exception as e:
        logger.error(f"Audio validation error: {e}")
        return False, f"Audio validation failed: {str(e)}"

st.set_page_config(layout="wide")
st.title("Kannada Live Speech-to-Text with Dwani ASR")

st.markdown("""
Speak in Kannada using the recorder below. 
**Important:** Please record for at least 2-3 seconds to ensure successful transcription.
After you stop the recording, the audio will be processed, and the transcription will appear.
""")

# --- Audio Recorder ---
audio_bytes = st_audiorec()

# --- Transcription Display Area ---
transcription_placeholder = st.empty()
error_placeholder = st.empty()

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")
    error_placeholder.empty()
    
    # Initial validation of audio data
    if len(audio_bytes) < 1024:
        error_placeholder.error("⚠️ Audio recording too short. Please record for at least 2-3 seconds.")
    else:
        transcription_placeholder.info("🎤 Processing audio and transcribing...")

        temp_audio_file_path = None
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio_file:
                tmp_audio_file.write(audio_bytes)
                temp_audio_file_path = tmp_audio_file.name

            logger.info(f"Saved audio file: {temp_audio_file_path} ({len(audio_bytes)} bytes)")
            
            # Validate audio file before sending to API
            is_valid, validation_message = validate_audio_file(temp_audio_file_path, audio_bytes)
            
            if not is_valid:
                error_placeholder.error(f"❌ {validation_message}")
                transcription_placeholder.empty()
            else:
                transcription_placeholder.info(f"✅ {validation_message}. Starting transcription...")
                
                # Force API base configuration before call
                dwani.ASR.api_base = DWANI_API_BASE
                
                # Call Dwani ASR API
                try:
                    # Ensure file exists before API call
                    if not os.path.exists(temp_audio_file_path):
                        raise FileNotFoundError(f"Audio file not found: {temp_audio_file_path}")
                    
                    result = dwani.ASR.transcribe(
                        file_path=temp_audio_file_path, 
                        language="kannada"
                    )
                    logger.info("Transcription successful")
                    
                    # Extract transcribed text
                    if isinstance(result, str):
                        transcribed_text = result
                    elif hasattr(result, 'text'):
                        transcribed_text = result.text
                    elif isinstance(result, dict):
                        transcribed_text = result.get('text', result.get('transcription', str(result)))
                    else:
                        transcribed_text = str(result)
                        
                    if transcribed_text and transcribed_text.strip():
                        transcription_placeholder.success("🎉 Transcription completed!")
                        st.markdown(f"""**Transcription:**
```text
{transcribed_text}
```
""")
                    else:
                        transcription_placeholder.warning("⚠️ Transcription returned empty. The audio might be unclear or too short.")
                        
                except FileNotFoundError as fe:
                    logger.error(f"File not found error: {fe}")
                    error_placeholder.error(f"❌ Audio file error: {str(fe)}")
                    transcription_placeholder.empty()
                    
                except Exception as e:
                    error_message = str(e)
                    logger.error(f"Transcription API error: {error_message}")
                    
                    # Provide user-friendly error messages
                    if "500" in error_message or "Internal Server Error" in error_message:
                        error_placeholder.error(
                            "❌ Server error during transcription. This might be due to:\n"
                            "- Audio file too short or unclear\n" 
                            "- Server temporarily unavailable\n"
                            "- Audio format issues\n\n"
                            "Please try recording again with clear speech for 3+ seconds."
                        )
                    elif "404" in error_message:
                        error_placeholder.error("❌ Transcription service not found. Please check the API configuration.")
                    elif "timeout" in error_message.lower():
                        error_placeholder.error("❌ Request timed out. Please try again.")
                    else:
                        error_placeholder.error(f"❌ Transcription failed: {error_message}")
                    
                    transcription_placeholder.empty()

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            error_placeholder.error(f"❌ An unexpected error occurred: {str(e)}")
            
        finally:
            # Clean up temporary file
            if temp_audio_file_path and os.path.exists(temp_audio_file_path):
                os.remove(temp_audio_file_path)
                logger.info("Cleaned up temporary file")
            
else:
    transcription_placeholder.info("Click the microphone icon above to start recording your speech in Kannada.")

st.markdown("---")
st.caption("Powered by Dwani and Streamlit.")
