# Dwani ASR Transcription and Translation Server

A Flask-based REST API server that provides audio transcription and text translation services using the Dwani API. This server accepts audio files via POST requests and returns transcribed text, and also provides text translation between different languages.

## Features

- 🎤 **File Upload Transcription**: Upload audio files directly via multipart/form-data
- 📤 **Base64 Transcription**: Send base64-encoded audio data via JSON
- 🌐 **Text Translation**: Translate text between different languages
- 🌍 **Multiple Language Support**: Supports Kannada, English and other languages supported by Dwani
- 🔍 **Health Check**: Monitor server status
- 📝 **Comprehensive Error Handling**: User-friendly error messages
- 🧹 **Automatic Cleanup**: Temporary files are automatically cleaned up

## Supported Audio Formats

- WAV (.wav)
- MP3 (.mp3)
- MP4 (.mp4)
- M4A (.m4a)
- FLAC (.flac)
- OGG (.ogg)

## API Endpoints

### 1. Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "Dwani ASR transcription server is running",
  "api_base": "https://dwani-dwani-api.hf.space"
}
```

### 2. File Upload Transcription
```
POST /transcribe
```

**Request (multipart/form-data):**
- `audio` (file, required): Audio file to transcribe
- `language` (string, optional): Language for transcription (default: "kannada")

**Response:**
```json
{
  "success": true,
  "transcription": "transcribed text here",
  "language": "kannada",
  "message": "Transcription completed successfully"
}
```

### 3. Base64 Transcription
```
POST /api/transcribe
```

**Request (JSON):**
```json
{
  "audio_data": "base64_encoded_audio_data",
  "language": "kannada",
  "file_extension": "wav"
}
```

**Response:**
```json
{
  "success": true,
  "transcription": "transcribed text here",
  "language": "kannada",
  "message": "Transcription completed successfully"
}
```

### 4. Audio Translation (Transcription + Translation)
```
POST /translate
```

**Request (multipart/form-data):**
- `audio` (file, required): Audio file to transcribe and translate
- `transcription_language` (string, optional): Language for transcription (default: "kannada")
- `src_lang` (string, optional): Source language for translation (default: transcription language)
- `tgt_lang` (string, optional): Target language for translation (default: "english")

**Response:**
```json
{
  "success": true,
  "transcription": "ನಮಸ್ಕಾರ ನೀವು ಹೇಗಿದ್ದೀರಿ",
  "translation": "Hello, how are you?",
  "transcription_language": "kannada",
  "src_lang": "kannada",
  "tgt_lang": "english",
  "message": "Audio transcribed and translated successfully"
}
```

## Usage Examples

### Using curl

#### File Upload:
```bash
curl -X POST http://localhost:6960/transcribe \
  -F "audio=@kann.wav" \
  -F "language=kannada"
```

#### Base64 Upload:
```bash
# First encode your audio file
BASE64_AUDIO=$(base64 -i kann.wav)

curl -X POST http://localhost:6960/api/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "'$BASE64_AUDIO'",
    "language": "kannada",
    "file_extension": "wav"
  }'
```

#### Audio Translation:
```bash
curl -X POST http://localhost:6960/translate \
  -F "audio=@kann.wav" \
  -F "transcription_language=kannada" \
  -F "src_lang=kannada" \
  -F "tgt_lang=english"
```

### Using Python requests

#### File Upload:
```python
import requests

with open('kann.wav', 'rb') as audio_file:
    files = {'audio': audio_file}
    data = {'language': 'kannada'}
    
    response = requests.post(
        'http://localhost:6960/transcribe',
        files=files,
        data=data
    )
    
    result = response.json()
    print(result['transcription'])
```

#### Base64 Upload:
```python
import requests
import base64

# Read and encode audio file
with open('kann.wav', 'rb') as audio_file:
    audio_bytes = audio_file.read()
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

# Send request
data = {
    'audio_data': audio_base64,
    'language': 'kannada',
    'file_extension': 'wav'
}

response = requests.post(
    'http://localhost:6960/api/transcribe',
    json=data
)

result = response.json()
print(result['transcription'])
```

#### Audio Translation:
```python
import requests

with open('kann.wav', 'rb') as audio_file:
    files = {'audio': audio_file}
    data = {
        'transcription_language': 'kannada',
        'src_lang': 'kannada', 
        'tgt_lang': 'english'
    }
    
    response = requests.post(
        'http://localhost:6960/translate',
        files=files,
        data=data
    )
    
    result = response.json()
    print(f"Transcription: {result['transcription']}")
    print(f"Translation: {result['translation']}")
```
```

## Running the Server

### Start the server:
```bash
python server.py
```

The server will start on `http://localhost:6960` by default.

### Test the server:
```bash
python test_audio_translation.py
```

## Configuration

The server uses the following Dwani API configuration:
- **API Key**: `abhishekr.23.becs@acharya.ac.in_dwani_krishnadevaraya`
- **API Base**: `https://dwani-dwani-api.hf.space`

## Error Handling

The server provides detailed error messages for common issues:

- **Missing audio file**: When no file is provided
- **Invalid file format**: When unsupported file types are uploaded
- **File too large**: When files exceed the 16MB limit
- **Audio too short**: When audio is less than 1KB or too brief
- **API errors**: Server errors, timeouts, or transcription failures

## Limitations

- Maximum file size: 16MB
- Minimum audio duration: Recommended 2-3 seconds for best results
- Supported languages: Depends on Dwani API capabilities

## Development

The server includes:
- Comprehensive logging
- Automatic temporary file cleanup
- Input validation
- Security measures (secure filename handling)
- CORS support can be added if needed for web applications
