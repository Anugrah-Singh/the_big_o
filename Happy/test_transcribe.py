#!/usr/bin/env python3
"""
Simple test script to test the /transcribe endpoint with detailed logging
"""

import requests
import os

# Server configuration
SERVER_URL = "http://localhost:6960"

def test_transcribe_with_file(audio_file_path):
    """Test the /transcribe endpoint with an audio file"""
    print(f"🎤 Testing /transcribe with file: {audio_file_path}")
    
    if not os.path.exists(audio_file_path):
        print(f"❌ Audio file not found: {audio_file_path}")
        return False
    
    file_size = os.path.getsize(audio_file_path)
    print(f"📁 File size: {file_size} bytes")
    
    try:
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio': (os.path.basename(audio_file_path), audio_file, 'audio/wav')}
            data = {'language': 'kannada'}
            
            print("📤 Sending request to server...")
            response = requests.post(f"{SERVER_URL}/transcribe", files=files, data=data)
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📥 Response headers: {dict(response.headers)}")
            
            try:
                result = response.json()
                print(f"📥 Response JSON: {result}")
                
                if result.get('success'):
                    print(f"✅ Transcription successful: {result.get('transcription')}")
                    return True
                else:
                    print(f"❌ Transcription failed: {result.get('error')}")
                    return False
            except Exception as json_error:
                print(f"❌ Failed to parse JSON response: {json_error}")
                print(f"Raw response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing /health endpoint...")
    try:
        response = requests.get(f"{SERVER_URL}/health")
        print(f"📥 Health check status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Server is healthy: {response.json()}")
            return True
        else:
            print(f"❌ Server health check failed")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    print("🚀 Testing Dwani ASR Server")
    print("=" * 50)
    
    # Test health first
    if not test_health():
        print("❌ Server is not healthy. Please check if it's running on port 6960")
        return
    
    # Test with available audio files
    audio_files = ['kann.wav', 'kannada_sample.wav']
    
    for audio_file in audio_files:
        if os.path.exists(audio_file):
            print(f"\n📂 Found audio file: {audio_file}")
            test_transcribe_with_file(audio_file)
            break
    else:
        print("\n⚠️ No test audio files found. Create a 'kann.wav' file to test.")
        print("You can record a short audio file and save it as 'kann.wav' in the current directory.")

if __name__ == "__main__":
    main()
