from flask import Flask, request, jsonify
import dwani
import os
import tempfile
import logging
import base64
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_cors import CORS
from pydub import AudioSegment
import io
import json
# import google.generativeai as genai # User needs to install and configure this

# LangChain imports for conversation memory
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes



# --- Dwani API Configuration ---
DWANI_API_KEY = 'abhishekr.23.becs@acharya.ac.in_dwani_krishnadevaraya'  # Updated API Key
DWANI_API_BASE = 'https://dwani-dwani-api.hf.space'

# Configure Dwani API
dwani.api_key = DWANI_API_KEY # Uncommented and ensuring API key is set
dwani.api_base = DWANI_API_BASE # Ensuring API base is set for the main module as well

# Set API base for ASR module
if hasattr(dwani, 'ASR') and dwani.ASR is not None:
    dwani.ASR.api_key = DWANI_API_KEY # Ensure API key is set for ASR module
    dwani.ASR.api_base = DWANI_API_BASE
    logger.info(f"Configured Dwani ASR with API base: {DWANI_API_BASE}")

# Set API base for Translate module
if hasattr(dwani, 'Translate') and dwani.Translate is not None:
    dwani.Translate.api_base = DWANI_API_BASE
    logger.info(f"Configured Dwani Translate with API base: {DWANI_API_BASE}")

# Set API base for Chat module
# if hasattr(dwani, \'Chat\') and dwani.Chat is not None:
# dwani.Chat.api_base = DWANI_API_BASE # No longer using dwani for this endpoint
# logger.info(f"Configured Dwani Chat with API base: {DWANI_API_BASE}") # No longer using dwani for this endpoint
    # Ensure the chat model is set if required by the dwani library, e.g.
    # dwani.Chat.model = "default-model-name" # Or whatever model is appropriate

# Set API base for Documents module
if hasattr(dwani, 'Documents') and dwani.Documents is not None:
    try:
        dwani.Documents.api_base = DWANI_API_BASE
        logger.info(f"Attempted to set Dwani Documents API base to: {DWANI_API_BASE}")
        # Optional: Verify if the attribute now holds the correct value
        current_doc_api_base = getattr(dwani.Documents, 'api_base', 'Attribute not found after setting')
        if current_doc_api_base == DWANI_API_BASE:
            logger.info(f"Successfully verified Dwani Documents API base is: {current_doc_api_base}")
        else:
            logger.warning(f"Dwani Documents API base was set to {DWANI_API_BASE}, but verification check shows: '{current_doc_api_base}'. The library might handle this internally or the attribute may not be readable as expected.")
    except AttributeError:
        logger.error("CRITICAL: dwani.Documents module does not allow setting 'api_base' attribute (AttributeError). Document extraction will likely use defaults or fail.")
    except Exception as e:
        logger.error(f"CRITICAL: Unexpected error setting api_base for dwani.Documents at startup: {e}")
elif hasattr(dwani, 'Documents'): # This means dwani.Documents is None
    logger.warning("dwani.Documents module exists but is None at startup. Cannot configure API base.")
else: # This means dwani.Documents attribute itself doesn't exist on the dwani module
    logger.warning("dwani.Documents module not found at startup. Document extraction endpoint may not work.")

# Set environment variables as fallback
os.environ['DWANI_API_BASE'] = DWANI_API_BASE
os.environ['DWANI_API_KEY'] = DWANI_API_KEY

# --- Conversation Memory Storage ---
# Dictionary to store conversation memories by session_id
conversation_memories = {}

def get_or_create_memory(session_id):
    """Get or create a conversation memory for a session"""
    if session_id not in conversation_memories:
        conversation_memories[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        logger.info(f"Created new conversation memory for session: {session_id}")
    return conversation_memories[session_id]

def cleanup_old_conversations(max_sessions=100):
    """Clean up old conversation sessions if we have too many"""
    if len(conversation_memories) > max_sessions:
        # Remove oldest sessions (simple cleanup - in production you might want timestamp-based cleanup)
        oldest_sessions = list(conversation_memories.keys())[:-max_sessions]
        for session_id in oldest_sessions:
            del conversation_memories[session_id]
        logger.info(f"Cleaned up {len(oldest_sessions)} old conversation sessions")

# Configuration
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'mp4', 'm4a', 'flac', 'ogg'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Dwani API Service Functions ---

def dwani_transcribe(file_path, language='kannada'):
    """
    Transcribe audio file using Dwani ASR API
    
    Args:
        file_path (str): Path to the audio file to transcribe
        language (str): Language for transcription (default: 'kannada')
    
    Returns:
        tuple: (success, result/error_message)
    """
    try:
        logger.info(f"=== DWANI TRANSCRIPTION START ===")
        logger.info(f"File path: {file_path}")
        logger.info(f"Language: {language}")
        logger.info(f"File exists: {os.path.exists(file_path)}")
        
        if os.path.exists(file_path):
            logger.info(f"File size: {os.path.getsize(file_path)} bytes")
            # Read first few bytes to verify content
            with open(file_path, 'rb') as verify_file:
                first_bytes = verify_file.read(16)
                logger.info(f"First 16 bytes (hex): {first_bytes.hex()}")
                # Check if it looks like audio data
                if first_bytes.startswith(b'RIFF'):
                    logger.info("File appears to be WAV format (starts with RIFF)")
                else:
                    logger.warning("File does not appear to be WAV format")
        else:
            logger.error("File does not exist!")
            return False, "Audio file not found"
        
        # Force API base and key configuration before call
        dwani.api_key = DWANI_API_KEY # Ensure API key is set before call
        dwani.ASR.api_base = DWANI_API_BASE
        
        # Call Dwani ASR API
        result = dwani.ASR.transcribe(
            file_path=file_path, 
            language=language
        )
        
        logger.info(f"=== DWANI TRANSCRIPTION SUCCESS ===")
        logger.info(f"Raw result: {result}")
        
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
            return True, transcribed_text.strip()
        else:
            return False, "Transcription returned empty. The audio might be unclear or too short."
            
    except Exception as e:
        logger.error(f"=== DWANI TRANSCRIPTION FAILED ===")
        logger.error(f"Error: {e}")
        logger.error(f"Error type: {type(e)}")
        return False, f"Transcription failed: {str(e)}"

def dwani_translate(sentences, src_lang='english', tgt_lang='kannada'):
    """
    Translate text using Dwani Translate API
    
    Args:
        sentences (list): List of sentences to translate
        src_lang (str): Source language (default: 'english')
        tgt_lang (str): Target language (default: 'kannada')
    
    Returns:
        tuple: (success, result/error_message)
    """
    try:
        logger.info(f"=== DWANI TRANSLATION START ===")
        logger.info(f"Sentences: {sentences}")
        logger.info(f"Source language: {src_lang}")
        logger.info(f"Target language: {tgt_lang}")
        
        # Force API base configuration before call
        if hasattr(dwani, 'Translate'):
            dwani.Translate.api_base = DWANI_API_BASE
        
        # Call Dwani Translate API
        result = dwani.Translate.run_translate(
            sentences=sentences,
            src_lang=src_lang,
            tgt_lang=tgt_lang
        )
        
        logger.info(f"=== DWANI TRANSLATION SUCCESS ===")
        logger.info(f"Raw result: {result}")
        
        # Extract translated text
        if isinstance(result, list):
            translations = result
        elif isinstance(result, dict):
            translations = result.get('translations', result.get('text', [str(result)]))
        elif isinstance(result, str):
            translations = [result]
        else:
            translations = [str(result)]
        
        return True, translations
        
    except Exception as e:
        logger.error(f"=== DWANI TRANSLATION FAILED ===")
        logger.error(f"Error: {e}")
        logger.error(f"Error type: {type(e)}")
        return False, f"Translation failed: {str(e)}"

def dwani_chat(prompt, src_lang='english', tgt_lang='kannada', session_id=None):
    """
    Chat with Dwani Chat API with conversation memory support
    
    Args:
        prompt (str): User's message/prompt
        src_lang (str): Source language (default: 'english')
        tgt_lang (str): Target language (default: 'kannada')
        session_id (str): Session ID for conversation memory
    
    Returns:
        tuple: (success, result/error_message)
    """
    try:
        logger.info(f"=== DWANI CHAT START ===")
        logger.info(f"Prompt: {prompt}")
        logger.info(f"Source language: {src_lang}")
        logger.info(f"Target language: {tgt_lang}")
        logger.info(f"Session ID: {session_id}")
        
        # Get or create conversation memory for this session
        memory = get_or_create_memory(session_id)
        
        # Build conversation context from memory
        chat_history = memory.chat_memory.messages if hasattr(memory, 'chat_memory') else []
        
        # Prepare context with conversation history
        context_prompt = prompt
        if chat_history:
            # Build context from previous messages
            context_parts = []
            for message in chat_history[-10:]:  # Use last 10 messages for context
                if isinstance(message, HumanMessage):
                    context_parts.append(f"Human: {message.content}")
                elif isinstance(message, AIMessage):
                    context_parts.append(f"Assistant: {message.content}")
            
            if context_parts:
                context_prompt = "\n".join(context_parts) + f"\nHuman: {prompt}"
        
        logger.info(f"Context prompt: {context_prompt}")
        
        # Force API base configuration before call
        if hasattr(dwani, 'Chat'):
            dwani.Chat.api_base = DWANI_API_BASE
        
        # Call Dwani Chat API
        result = dwani.Chat.create(
            prompt=context_prompt,
            src_lang=src_lang,
            tgt_lang=tgt_lang
        )
        
        logger.info(f"=== DWANI CHAT SUCCESS ===")
        logger.info(f"Raw result: {result}")
        
        # Extract chat response
        if isinstance(result, str):
            chat_response = result
        elif hasattr(result, 'response'):
            chat_response = result.response
        elif isinstance(result, dict):
            chat_response = result.get('response', result.get('text', str(result)))
        else:
            chat_response = str(result)
        
        # Store conversation in memory
        memory.chat_memory.add_user_message(prompt)
        memory.chat_memory.add_ai_message(chat_response)
        
        logger.info(f"Stored conversation in memory for session: {session_id}")
        
        if chat_response and chat_response.strip():
            return True, chat_response.strip()
        else:
            return False, "Chat response was empty. Please try rephrasing your message."
            
    except Exception as e:
        logger.error(f"=== DWANI CHAT FAILED ===")
        logger.error(f"Error: {e}")
        logger.error(f"Error type: {type(e)}")
        return False, f"Chat failed: {str(e)}"

def process_audio_for_transcription(audio_file):
    """
    Process uploaded audio file for transcription
    
    Args:
        audio_file: Flask file object from request.files
    
    Returns:
        tuple: (success, final_audio_path_or_error, temp_files_to_cleanup)
    """
    temp_audio_file_path = None
    converted_wav_path = None
    
    try:
        # Create secure filename
        filename = secure_filename(audio_file.filename)
        original_ext = filename.rsplit('.', 1)[1].lower()
        
        # Reset file pointer to beginning (important!)
        audio_file.seek(0)
        
        # Save to temporary file first
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{original_ext}") as tmp_file:
            temp_audio_file_path = tmp_file.name
            # Read all data and write to temp file
            audio_data = audio_file.read()
            tmp_file.write(audio_data)
            tmp_file.flush()  # Ensure data is written to disk
        
        logger.info(f"Saved uploaded audio file: {temp_audio_file_path}")
        logger.info(f"Audio data written: {len(audio_data)} bytes")
        
        # Verify file was actually written
        if not os.path.exists(temp_audio_file_path):
            return False, "Failed to save audio file to disk", [temp_audio_file_path]
        
        actual_file_size = os.path.getsize(temp_audio_file_path)
        logger.info(f"Verified file on disk: {actual_file_size} bytes")
        
        # Convert to WAV format if not already WAV
        if original_ext != 'wav':
            logger.info(f"Converting {original_ext} to WAV format...")
            converted_wav_path = temp_audio_file_path.replace(f'.{original_ext}', '.wav')
            
            success, message = convert_audio_to_wav(temp_audio_file_path, converted_wav_path)
            
            if not success:
                logger.error(f"Audio conversion failed: {message}")
                return False, f"Audio conversion failed: {message}", [temp_audio_file_path, converted_wav_path]
            
            # Use the converted WAV file for transcription
            final_audio_path = converted_wav_path
            logger.info(f"Using converted WAV file: {final_audio_path}")
        else:
            # Already WAV, use original file
            final_audio_path = temp_audio_file_path
            logger.info(f"Using original WAV file: {final_audio_path}")
        
        # Validate audio file
        is_valid, validation_message = validate_audio_file(final_audio_path)
        
        if not is_valid:
            return False, validation_message, [temp_audio_file_path, converted_wav_path]
        
        return True, final_audio_path, [temp_audio_file_path, converted_wav_path]
        
    except Exception as e:
        logger.error(f"Audio processing error: {e}")
        return False, f"Audio processing failed: {str(e)}", [temp_audio_file_path, converted_wav_path]

def cleanup_temp_files(file_paths):
    """Clean up temporary files"""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up file {file_path}: {e}")

def convert_audio_to_wav(input_file_path, output_file_path):
    """
    Convert audio file to WAV format using pydub
    
    Args:
        input_file_path (str): Path to the input audio file
        output_file_path (str): Path where the WAV file should be saved
    
    Returns:
        tuple: (success, message)
    """
    try:
        logger.info(f"Converting audio file: {input_file_path} -> {output_file_path}")
        
        # Get the input file extension to determine format
        input_ext = input_file_path.split('.')[-1].lower()
        
        # Load audio file based on format
        if input_ext == 'mp3':
            audio = AudioSegment.from_mp3(input_file_path)
        elif input_ext == 'm4a':
            audio = AudioSegment.from_file(input_file_path, format='m4a')
        elif input_ext == 'mp4':
            audio = AudioSegment.from_file(input_file_path, format='mp4')
        elif input_ext == 'flac':
            audio = AudioSegment.from_file(input_file_path, format='flac')
        elif input_ext == 'ogg':
            audio = AudioSegment.from_file(input_file_path, format='ogg')
        elif input_ext == 'wav':
            # Already WAV, just copy
            audio = AudioSegment.from_wav(input_file_path)
        else:
            # Try generic format detection
            audio = AudioSegment.from_file(input_file_path)
        
        # Convert to WAV with standard settings
        # 16-bit PCM, mono, 16kHz sample rate (good for speech recognition)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        # Export as WAV
        audio.export(output_file_path, format="wav")
        
        # Verify the output file was created
        if os.path.exists(output_file_path):
            output_size = os.path.getsize(output_file_path)
            logger.info(f"Audio conversion successful. Output file size: {output_size} bytes")
            logger.info(f"Audio properties - Duration: {len(audio)}ms, Channels: {audio.channels}, Sample rate: {audio.frame_rate}Hz")
            return True, f"Audio converted successfully to WAV format"
        else:
            return False, "Conversion failed - output file not created"
            
    except Exception as e:
        logger.error(f"Audio conversion failed: {e}")
        return False, f"Audio conversion failed: {str(e)}"

def validate_audio_file(file_path):
    """Validate audio file for transcription requirements"""
    try:
        if not os.path.exists(file_path):
            return False, "Audio file not found"
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, "Audio file is empty"
        
        # Check minimum file size (at least 1KB)
        if file_size < 1024:
            return False, "Audio file too small. Please provide at least 2-3 seconds of audio"
        
        logger.info(f"Audio validation passed: {file_size} bytes")
        return True, "Audio file is valid"
        
    except Exception as e:
        logger.error(f"Audio validation error: {e}")
        return False, f"Audio validation failed: {str(e)}"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Dwani ASR transcription server is running',
        'api_base': DWANI_API_BASE
    })

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Transcribe audio file using Dwani ASR API
    
    Expected request:
    - Content-Type: multipart/form-data
    - File field: 'audio' (required)
    - Language field: 'language' (optional, defaults to 'kannada')
    
    Returns:
    - JSON response with transcription or error message
    """
    try:
        # Log incoming request details
        logger.info("=== TRANSCRIBE REQUEST RECEIVED ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request files keys: {list(request.files.keys())}")
        logger.info(f"Request form keys: {list(request.form.keys())}")
        
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided. Please include an audio file in the "audio" field.'
            }), 400
        
        audio_file = request.files['audio']
        
        # Check if file was actually uploaded
        if audio_file.filename == '':
            logger.error("No audio file selected - filename is empty")
            return jsonify({
                'success': False,
                'error': 'No audio file selected'
            }), 400
        
        # Get language parameter (default to kannada)
        language = request.form.get('language', 'kannada').lower()
        
        # Validate file extension
        if not allowed_file(audio_file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not supported. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Process audio file
        success, result, temp_files = process_audio_for_transcription(audio_file)
        
        try:
            if not success:
                return jsonify({
                    'success': False,
                    'error': result
                }), 400
            
            final_audio_path = result
            
            # Call Dwani transcription service
            success, transcription_result = dwani_transcribe(final_audio_path, language)
            
            if success:
                logger.info("Transcription successful")
                return jsonify({
                    'success': True,
                    'transcription': transcription_result,
                    'language': language,
                    'message': 'Transcription completed successfully'
                })
            else:
                error_message = transcription_result
                logger.error(f"Transcription failed: {error_message}")
                
                # Provide user-friendly error messages
                if "500" in error_message or "Internal Server Error" in error_message:
                    return jsonify({
                        'success': False,
                        'error': 'Server error during transcription. This might be due to audio being too short, unclear, or server issues. Please try with clear speech for 3+ seconds.'
                    }), 500
                elif "404" in error_message:
                    return jsonify({
                        'success': False,
                        'error': 'Transcription service not found. Please check the API configuration.'
                    }), 500
                elif "timeout" in error_message.lower():
                    return jsonify({
                        'success': False,
                        'error': 'Request timed out. Please try again.'
                    }), 408
                else:
                    return jsonify({
                        'success': False,
                        'error': error_message
                    }), 500
                    
        finally:
            # Clean up temporary files
            cleanup_temp_files(temp_files)
                
    except Exception as e:
        logger.error(f"Unexpected server error: {e}")
        return jsonify({
            'success': False,
            'error': f'Unexpected server error: {str(e)}'
        }), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe_from_base64():
    """
    Transcribe audio from base64 encoded data
    
    Expected request JSON:
    {
        "audio_data": "base64_encoded_audio_data",
        "language": "kannada" (optional),
        "file_extension": "wav" (optional, defaults to wav)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'audio_data' not in data:
            return jsonify({
                'success': False,
                'error': 'No audio data provided. Please include base64 encoded audio in "audio_data" field.'
            }), 400
        
        import base64
        
        # Get parameters
        audio_data = data['audio_data']
        language = data.get('language', 'kannada').lower()
        file_extension = data.get('file_extension', 'wav').lower()
        
        # Validate file extension
        if file_extension not in ALLOWED_EXTENSIONS:
            return jsonify({
                'success': False,
                'error': f'File extension not supported. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Invalid base64 audio data'
            }), 400
        
        # Save audio to temporary file
        temp_audio_file_path = None
        converted_wav_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                tmp_file.write(audio_bytes)
                temp_audio_file_path = tmp_file.name
            
            logger.info(f"Saved base64 audio file: {temp_audio_file_path} ({len(audio_bytes)} bytes)")
            
            # Convert to WAV format if not already WAV
            if file_extension != 'wav':
                logger.info(f"Converting {file_extension} to WAV format...")
                converted_wav_path = temp_audio_file_path.replace(f'.{file_extension}', '.wav')
                
                success, message = convert_audio_to_wav(temp_audio_file_path, converted_wav_path)
                
                if not success:
                    logger.error(f"Audio conversion failed: {message}")
                    return jsonify({
                        'success': False,
                        'error': f'Audio conversion failed: {message}'
                    }), 500
                
                # Use the converted WAV file for transcription
                final_audio_path = converted_wav_path
                logger.info(f"Using converted WAV file: {final_audio_path}")
            else:
                # Already WAV, use original file
                final_audio_path = temp_audio_file_path
                logger.info(f"Using original WAV file: {final_audio_path}")
            
            # Validate audio file
            is_valid, validation_message = validate_audio_file(final_audio_path)
            
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': validation_message
                }), 400
            
            # Call Dwani transcription service
            success, transcription_result = dwani_transcribe(final_audio_path, language)
            
            if success:
                logger.info("Transcription successful")
                return jsonify({
                    'success': True,
                    'transcription': transcription_result,
                    'language': language,
                    'message': 'Transcription completed successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': transcription_result
                }), 500
                
        finally:
            # Clean up temporary files
            cleanup_temp_files([temp_audio_file_path, converted_wav_path])
                
    except Exception as e:
        logger.error(f"Unexpected server error: {e}")
        return jsonify({
            'success': False,
            'error': f'Unexpected server error: {str(e)}'
        }), 500

@app.route('/translate', methods=['POST'])
def translate_audio():
    """
    Transcribe audio and then translate the transcribed text using Dwani APIs
    
    Expected request:
    - Content-Type: multipart/form-data
    - File field: 'audio' (required)
    - Form fields:
      - 'transcription_language': Language for transcription (optional, defaults to 'kannada')
      - 'src_lang': Source language for translation (optional, defaults to detected transcription language)
      - 'tgt_lang': Target language for translation (optional, defaults to 'english')
    
    Returns:
    - JSON response with transcription, translation, and metadata
    """
    try:
        # Log incoming request details
        logger.info("=== TRANSLATE AUDIO REQUEST RECEIVED ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request files keys: {list(request.files.keys())}")
        logger.info(f"Request form keys: {list(request.form.keys())}")
        
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided. Please include an audio file in the "audio" field.'
            }), 400
        
        audio_file = request.files['audio']
        
        # Check if file was actually uploaded
        if audio_file.filename == '':
            logger.error("No audio file selected - filename is empty")
            return jsonify({
                'success': False,
                'error': 'No audio file selected'
            }), 400
        
        # Get language parameters
        transcription_language = 'kannada'
        src_lang = transcription_language # Default to transcription language
        tgt_lang = 'english'  # Default target language
        
        # Validate file extension
        if not allowed_file(audio_file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not supported. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Process audio file
        success, result, temp_files = process_audio_for_transcription(audio_file)
        
        try:
            if not success:
                return jsonify({
                    'success': False,
                    'error': result
                }), 400
            
            final_audio_path = result
            
            # Step 1: Transcribe the audio
            logger.info(f"Step 1: Transcribing audio in {transcription_language}")
            transcription_success, transcription_result = dwani_transcribe(final_audio_path, transcription_language)
            
            if not transcription_success:
                error_message = transcription_result
                logger.error(f"Transcription failed: {error_message}")
                
                # Provide user-friendly error messages
                if "500" in error_message or "Internal Server Error" in error_message:
                    return jsonify({
                        'success': False,
                        'error': 'Server error during transcription. This might be due to audio being too short, unclear, or server issues. Please try with clear speech for 3+ seconds.'
                    }), 500
                elif "404" in error_message:
                    return jsonify({
                        'success': False,
                        'error': 'Transcription service not found. Please check the API configuration.'
                    }), 500
                elif "timeout" in error_message.lower():
                    return jsonify({
                        'success': False,
                        'error': 'Transcription request timed out. Please try again.'
                    }), 408
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Transcription failed: {error_message}'
                    }), 500
            
            transcribed_text = transcription_result
            logger.info(f"Transcription successful: {transcribed_text}")
            
            # Step 2: Translate the transcribed text
            logger.info(f"Step 2: Translating from {src_lang} to {tgt_lang}")
            translation_success, translation_result = dwani_translate([transcribed_text], src_lang, tgt_lang)
            
            if not translation_success:
                error_message = translation_result
                logger.error(f"Translation failed: {error_message}")
                
                # Return partial success with transcription but failed translation
                return jsonify({
                    'success': False,
                    'transcription': transcribed_text,
                    'transcription_language': transcription_language,
                    'error': f'Translation failed: {error_message}',
                    'message': 'Transcription was successful, but translation failed.'
                }), 500
            
            # Extract translation result
            if isinstance(translation_result, list) and len(translation_result) > 0:
                translated_text = translation_result[0]
            else:
                translated_text = str(translation_result)
            
            logger.info(f"Translation successful: {translated_text}")
            
            # Return successful result with both transcription and translation
            return jsonify({
                'success': True,
                'transcription': transcribed_text,
                'translation': translated_text,
                'transcription_language': transcription_language,
                'src_lang': src_lang,
                'tgt_lang': tgt_lang,
                'message': 'Audio transcribed and translated successfully'
            })
                    
        finally:
            # Clean up temporary files
            cleanup_temp_files(temp_files)
                
    except Exception as e:
        logger.error(f"Unexpected server error: {e}")
        return jsonify({
            'success': False,
            'error': f'Unexpected server error: {str(e)}'
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    """
    Chat with Dwani Chat API with conversation memory support
    
    Expected request JSON:
    {
        "prompt": "Your message here",
        "src_lang": "english" (optional, defaults to 'english'),
        "tgt_lang": "kannada" (optional, defaults to 'kannada'),
        "session_id": "unique_session_id" (optional, auto-generated if not provided)
    }
    
    Returns:
    - JSON response with chat response and session information
    """
    try:
        # Log incoming request details
        logger.info("=== CHAT REQUEST RECEIVED ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request content type: {request.content_type}")
        
        # Parse JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided. Please send a JSON request with a "prompt" field.'
            }), 400
        
        # Extract parameters
        prompt = """You are a helpful assistant. Please respond to the user's message. Your name is sankalp."""
        if not prompt or not prompt.strip():
            return jsonify({
                'success': False,
                'error': 'No prompt provided. Please include a "prompt" field with your message.'
            }), 400
        
        src_lang = 'english'
        tgt_lang = 'hindi'
        session_id = data.get('session_id')
        
        # Generate session_id if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new session ID: {session_id}")
        
        # Clean up old conversations periodically
        cleanup_old_conversations()
        
        # Call Dwani chat service with conversation memory
        success, chat_result = dwani_chat(
            prompt=prompt.strip(),
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            session_id=session_id
        )
        
        if success:
            logger.info("Chat request successful")
            return jsonify({
                'success': True,
                'response': chat_result,
                'session_id': session_id,
                'src_lang': src_lang,
                'tgt_lang': tgt_lang,
                'timestamp': datetime.now().isoformat(),
                'message': chat_result
            })
        else:
            error_message = chat_result
            logger.error(f"Chat failed: {error_message}")
            
            # Provide user-friendly error messages
            if "500" in error_message or "Internal Server Error" in error_message:
                return jsonify({
                    'success': False,
                    'error': 'Server error during chat. This might be due to service temporarily unavailable. Please try again.',
                    'session_id': session_id
                }), 500
            elif "404" in error_message:
                return jsonify({
                    'success': False,
                    'error': 'Chat service not found. Please check the API configuration.',
                    'session_id': session_id
                }), 500
            elif "timeout" in error_message.lower():
                return jsonify({
                    'success': False,
                    'error': 'Chat request timed out. Please try again.',
                    'session_id': session_id
                }), 408
            else:
                return jsonify({
                    'success': False,
                    'error': error_message,
                    'session_id': session_id
                }), 500
                
    except Exception as e:
        logger.error(f"Unexpected chat server error: {e}")
        return jsonify({
            'success': False,
            'error': f'Unexpected server error: {str(e)}'
        }), 500

@app.route('/appointment', methods=['POST'])
def appointment_handler():
    logger.info("=== APPOINTMENT REQUEST RECEIVED ===")
    try:
        patient_data = request.get_json()
        if not patient_data:
            logger.error("No JSON data provided for appointment.")
            return jsonify({"success": False, "error": "No JSON data provided."}), 400

        logger.info(f"Received patient data: {patient_data}")

        # Construct the prompt for the LLM
        llm_prompt_template = """You are a medical assistant AI designed to process patient symptoms provided in a JSON file and recommend an action based on a predefined database of medical actions. Your task is to:

1. Read the input JSON containing patient symptoms and relevant details.
2. Analyze the symptoms to determine the appropriate medical specialty or condition.
3. Based on the analysis, select an action from the following database of possible actions:
   - For skin-related symptoms (e.g., rash, itching, lesions): Return a query for dermatologist vacancies.
   - For respiratory symptoms (e.g., cough, shortness of breath): Return a query for pulmonologist vacancies.
   - For fever or infection symptoms (e.g., high fever, chills): Return a query for general physician vacancies.
   - For joint pain or mobility issues (e.g., arthritis, joint swelling): Return a query for rheumatologist vacancies.
   - For other symptoms: Return a query for general physician vacancies as a default.
4. The action must be formatted as a valid JSON object with a single key "action" containing the query string.
5. The query string should follow this format: "show me top 10 [specialty] vacancy sorted by date, by earliest to farthest".
6. Ensure the output is valid JSON and contains only the action, with no additional explanation or text.

Example Input:
{{
  "patient_id": "12345",
  "symptoms": ["rash", "itching", "red spots"],
  "duration": "3 days"
}}

Example Output:
{{
  "action": "show me top 10 dermatologist vacancy sorted by date, by earliest to farthest"
}}

Now, process the provided JSON input and return the appropriate action in valid JSON format.
Input JSON:
{input_json}"""

        input_json_str = json.dumps(patient_data, indent=2)
        full_prompt = llm_prompt_template.format(input_json=input_json_str)

        logger.info("Sending prompt to Gemini API.")
        
        # --- Replace Dwani with Gemini ---
        # User needs to configure their API key, e.g.:
        # genai.configure(api_key="YOUR_GEMINI_API_KEY")
        # model = genai.GenerativeModel(\'gemini-pro\') # Or other appropriate Gemini model
        # gemini_response = model.generate_content(full_prompt)
        # llm_response_str = gemini_response.text # Assuming response has a .text attribute

        # Placeholder for llm_response_str until Gemini is integrated
        llm_response_str = '''{
          "action": "show me top 10 general physician vacancy sorted by date, by earliest to farthest"
        }'''
        logger.warning("Using placeholder LLM response. Integrate Gemini API call.")
        # --- End of Gemini replacement section ---
        
        # Original Dwani call (commented out):
        # chat_response_obj = dwani.Chat.create(
        # prompt=full_prompt,
        # src_lang=\'english\',
        # tgt_lang=\'english\'
        # )
        # logger.info(f"Raw LLM response object: {chat_response_obj}")
        # if isinstance(chat_response_obj, str):
        # llm_response_str = chat_response_obj
        # elif hasattr(chat_response_obj, \'response\'):
        # llm_response_str = chat_response_obj.response
        # elif hasattr(chat_response_obj, \'text\'):
        # llm_response_str = chat_response_obj.text
        # elif isinstance(chat_response_obj, dict) and \'response\' in chat_response_obj:
        # llm_response_str = chat_response_obj[\'response\']
        # elif isinstance(chat_response_obj, dict) and \'text\' in chat_response_obj:
        # llm_response_str = chat_response_obj[\'text\']
        # else:
        # logger.error(f"Could not extract string response from LLM object: {chat_response_obj}")
        # return jsonify({"success": False, "error": "Failed to get a valid response string from LLM."}), 500

        logger.info(f"LLM response string: {llm_response_str}")

        try:
            action_json = json.loads(llm_response_str)
            if not isinstance(action_json, dict) or "action" not in action_json:
                logger.error(f"LLM response is not the expected JSON format ({{\'action\': \'...\'}}): {llm_response_str}")
                return jsonify({"success": False, "error": "LLM response was not in the expected JSON format.", "details": llm_response_str}), 500
            logger.info(f"Successfully parsed LLM action: {action_json}")
            return jsonify({"success": True, "data": action_json}), 200
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {llm_response_str}. Error: {e}")
            return jsonify({"success": False, "error": "LLM response was not valid JSON.", "details": llm_response_str}), 500

    except Exception as e:
        logger.error(f"Unexpected error in /appointment: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"Unexpected server error: {str(e)}"}), 500


@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size allowed is {MAX_CONTENT_LENGTH // (1024*1024)}MB'
    }), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found. Available endpoints: /health (GET), /transcribe (POST), /api/transcribe (POST), /translate (POST), /chat (POST), /appointment (POST)'
    }), 404

@app.route('/doc', methods=['POST'])
def doc_extract_handler():
    """
    Receive multiple documents, extract text, and generate captions.

    Expected request:
    - Content-Type: multipart/form-data
    - Files: 'documents' (multiple files allowed)
    - Form fields:
      - 'page_number': Page number for extraction (optional, defaults to 1)
      - 'src_lang': Source language for extraction (optional, defaults to 'english')
      - 'tgt_lang': Target language for captions (optional, defaults to 'kannada')
    """
    logger.info("=== DOC EXTRACT REQUEST RECEIVED ===")
    try:
        if 'documents' not in request.files:
            return jsonify({"success": False, "error": "No documents provided. Please include files in the 'documents' field."}), 400

        files = request.files.getlist('documents')
        if not files or all(f.filename == '' for f in files):
            return jsonify({"success": False, "error": "No documents selected."}), 400

        page_number = 1
        src_lang = 'english'
        tgt_lang = 'kannada'

        results = []
        temp_files_to_cleanup = []

        for doc_file in files:
            if doc_file and doc_file.filename:
                filename = secure_filename(doc_file.filename)
                temp_file_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
                        doc_file.save(tmp_file.name)
                        temp_file_path = tmp_file.name
                    temp_files_to_cleanup.append(temp_file_path)

                    logger.info(f"Processing document: {filename}, page: {page_number}, src: {src_lang}, tgt: {tgt_lang}")
                    
                    # Configure Dwani Documents API base before each call if necessary
                    # This is a fallback/double-check; primary configuration is at startup.
                    if hasattr(dwani, 'Documents') and dwani.Documents is not None:
                        try:
                            # Attempt to set it, even if it was set at startup
                            dwani.Documents.api_base = DWANI_API_BASE 
                            # logger.debug(f"Re-confirmed Dwani Documents API base for {filename}: {DWANI_API_BASE}") # Optional: debug log
                        except AttributeError:
                            logger.warning(f"Could not set api_base for dwani.Documents for {filename} (AttributeError). Using existing/default.")
                        except Exception as e_config:
                            logger.warning(f"Error re-confirming api_base for dwani.Documents for {filename}: {e_config}. Using existing/default.")
                    elif not hasattr(dwani, 'Documents') or dwani.Documents is None:
                        logger.warning(f"Dwani Documents module not available when processing {filename}. Extraction will likely fail.")

                    extract_result = dwani.Documents.run_extract(
                        file_path=temp_file_path,
                        page_number=page_number,
                        src_lang=src_lang,
                        tgt_lang=tgt_lang
                    )
                    logger.info(f"Document Extract Response for {filename}: {extract_result}")
                    results.append({
                        "filename": filename,
                        "extraction": extract_result
                    })
                except Exception as e:
                    logger.error(f"Error processing document {filename}: {e}")
                    results.append({
                        "filename": filename,
                        "error": str(e)
                    })
                finally:
                    # Individual file cleanup can be done here if needed, 
                    # but we'll do a batch cleanup later.
                    pass 
            else:
                logger.warning("Received an empty file field.")

        return jsonify({
            "success": True,
            "results": results,
            "message": "Document processing complete."
        })

    except Exception as e:
        logger.error(f"Unexpected error in /doc endpoint: {e}")
        return jsonify({"success": False, "error": f"Unexpected server error: {str(e)}"}), 500
    finally:
        # Clean up all temporary files
        for f_path in temp_files_to_cleanup:
            if f_path and os.path.exists(f_path):
                try:
                    os.remove(f_path)
                    logger.info(f"Cleaned up temp doc file: {f_path}")
                except Exception as e_clean:
                    logger.warning(f"Failed to clean up temp doc file {f_path}: {e_clean}")


if __name__ == '__main__':
    # Ensure Dwani API key and base are set (can be from environment variables)
    # dwani.api_key = os.getenv('DWANI_API_KEY', DWANI_API_KEY)
    # dwani.api_base = os.getenv('DWANI_API_BASE', DWANI_API_BASE)
    
    # Log API base being used
    logger.info(f"Dwani API Key: {DWANI_API_KEY}")
    logger.info(f"Dwani API Base URL: {DWANI_API_BASE}")
    
    # Start Flask app
    app.run(host='0.0.0.0', port=9000, debug=True)
