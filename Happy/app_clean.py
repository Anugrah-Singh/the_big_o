import streamlit as st
from st_audiorec import st_audiorec
import dwani
import os
import tempfile
import logging

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

st.set_page_config(layout="wide")
st.title("Kannada Live Speech-to-Text with Dwani ASR")

st.markdown("""
Speak in Kannada using the recorder below. 
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
    transcription_placeholder.info("Processing audio and transcribing...")

    temp_audio_file_path = None
    try:
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio_file:
            tmp_audio_file.write(audio_bytes)
            temp_audio_file_path = tmp_audio_file.name

        logger.info(f"Saved audio file: {temp_audio_file_path} ({len(audio_bytes)} bytes)")
        
        # Force API base configuration before call
        dwani.ASR.api_base = DWANI_API_BASE
        
        # Call Dwani ASR API
        try:
            # Try with explicit api_base parameter first
            result = dwani.ASR.transcribe(
                file_path=temp_audio_file_path, 
                language="kannada", 
                api_base=DWANI_API_BASE
            )
            logger.info("Transcription successful with explicit api_base")
        except Exception as e1:
            logger.warning(f"Failed with explicit api_base: {e1}")
            try:
                # Fallback: try without explicit api_base
                result = dwani.ASR.transcribe(
                    file_path=temp_audio_file_path, 
                    language="kannada"
                )
                logger.info("Transcription successful without explicit api_base")
            except Exception as e2:
                logger.error(f"All transcription methods failed: {e2}")
                raise e2

        # Extract transcribed text
        if isinstance(result, str):
            transcribed_text = result
        elif hasattr(result, 'text'):
            transcribed_text = result.text
        elif isinstance(result, dict):
            transcribed_text = result.get('text', result.get('transcription', str(result)))
        else:
            transcribed_text = str(result)
            
        if transcribed_text:
            transcription_placeholder.markdown(f"""**Transcription:**
```text
{transcribed_text}
```
""")
        else:
            transcription_placeholder.warning("Transcription returned empty.")

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        error_placeholder.error(f"An error occurred: {e}")
        
    finally:
        # Clean up temporary file
        if temp_audio_file_path and os.path.exists(temp_audio_file_path):
            os.remove(temp_audio_file_path)
            logger.info("Cleaned up temporary file")
            
else:
    transcription_placeholder.info("Click the microphone icon above to start recording your speech in Kannada.")

st.markdown("---")
st.caption("Powered by Dwani and Streamlit.")
