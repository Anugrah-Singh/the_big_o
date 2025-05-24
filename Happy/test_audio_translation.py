#!/usr/bin/env python3
"""
Test script for the /translate endpoint (audio transcription + translation)
"""

import requests
import json
import os

# Server configuration
SERVER_URL = "http://localhost:6960"

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

def test_audio_translation(audio_file_path, transcription_language='kannada', src_lang='kannada', tgt_lang='english'):
    """Test audio translation (transcription + translation)"""
    print(f"\n🎤🌐 Testing audio translation with {audio_file_path}...")
    print(f"Transcription language: {transcription_language}")
    print(f"Translation: {src_lang} → {tgt_lang}")
    
    if not os.path.exists(audio_file_path):
        print(f"❌ Audio file not found: {audio_file_path}")
        return False
    
    file_size = os.path.getsize(audio_file_path)
    print(f"📁 File size: {file_size} bytes")
    
    try:
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio': (os.path.basename(audio_file_path), audio_file, 'audio/wav')}
            data = {
                'transcription_language': transcription_language,
                'src_lang': src_lang,
                'tgt_lang': tgt_lang
            }
            
            print("📤 Sending audio file to /translate endpoint...")
            response = requests.post(
                f"{SERVER_URL}/translate",
                files=files,
                data=data
            )
            
            print(f"📥 Response status: {response.status_code}")
            result = response.json()
            print(f"📥 Response JSON: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print(f"✅ Audio translation successful:")
                print(f"   🎤 Transcription ({transcription_language}): {result.get('transcription')}")
                print(f"   🌐 Translation ({src_lang} → {tgt_lang}): {result.get('translation')}")
                return True
            else:
                print(f"❌ Audio translation failed: {result.get('error')}")
                # Check if transcription succeeded but translation failed
                if result.get('transcription'):
                    print(f"   ℹ️ Transcription was successful: {result.get('transcription')}")
                return False
                
    except Exception as e:
        print(f"❌ Audio translation test failed: {e}")
        return False

def test_kannada_to_english_translation():
    """Test Kannada to English translation"""
    audio_files = ['kann.wav', 'kannada_sample.wav']
    
    for audio_file in audio_files:
        if os.path.exists(audio_file):
            print(f"\n📂 Found Kannada audio file: {audio_file}")
            return test_audio_translation(
                audio_file, 
                transcription_language='kannada',
                src_lang='kannada', 
                tgt_lang='english'
            )
    
    print("⚠️ No Kannada audio files found. Create a 'kann.wav' file to test.")
    return False

def test_english_to_kannada_translation():
    """Test English to Kannada translation"""
    audio_files = ['english_sample.wav', 'eng.wav']
    
    for audio_file in audio_files:
        if os.path.exists(audio_file):
            print(f"\n📂 Found English audio file: {audio_file}")
            return test_audio_translation(
                audio_file, 
                transcription_language='english',
                src_lang='english', 
                tgt_lang='kannada'
            )
    
    print("⚠️ No English audio files found. Create an 'english_sample.wav' file to test.")
    return False

def test_invalid_audio_requests():
    """Test various invalid audio request scenarios"""
    print("\n🧪 Testing invalid audio translation requests...")
    
    # Test missing audio file
    try:
        data = {
            'transcription_language': 'kannada',
            'src_lang': 'kannada',
            'tgt_lang': 'english'
        }
        response = requests.post(f"{SERVER_URL}/translate", data=data)
        print(f"Missing audio file test - Status: {response.status_code}")
        result = response.json()
        print(f"Expected error: {result.get('error')}")
    except Exception as e:
        print(f"Missing audio file test failed: {e}")
    
    # Test invalid file format (if we had a .txt file)
    try:
        if os.path.exists('test.txt'):
            with open('test.txt', 'rb') as test_file:
                files = {'audio': ('test.txt', test_file, 'text/plain')}
                data = {'transcription_language': 'kannada'}
                response = requests.post(f"{SERVER_URL}/translate", files=files, data=data)
                print(f"Invalid file format test - Status: {response.status_code}")
                result = response.json()
                print(f"Expected error: {result.get('error')}")
    except Exception as e:
        print(f"Invalid file format test failed: {e}")

def main():
    """Run all audio translation tests"""
    print("🚀 Testing Dwani Audio Translation Server")
    print("=" * 50)
    
    # Test health first
    if not test_health():
        print("❌ Server is not healthy. Please check if it's running on port 6960")
        return
    
    # Run audio translation tests
    test_kannada_to_english_translation()
    test_english_to_kannada_translation()
    test_invalid_audio_requests()
    
    print("\n" + "=" * 50)
    print("🎯 Audio translation tests completed!")
    print("\nTo use the audio translation endpoint:")
    print("POST /translate with multipart/form-data:")
    print("- File: 'audio' (required) - audio file to transcribe and translate")
    print("- Form fields:")
    print("  - 'transcription_language': Language for transcription (optional, default: 'kannada')")
    print("  - 'src_lang': Source language for translation (optional, default: transcription language)")
    print("  - 'tgt_lang': Target language for translation (optional, default: 'english')")
    print("\nExample with curl:")
    print("curl -X POST http://localhost:6960/translate \\")
    print("  -F 'audio=@kann.wav' \\")
    print("  -F 'transcription_language=kannada' \\")
    print("  -F 'src_lang=kannada' \\")
    print("  -F 'tgt_lang=english'")

if __name__ == "__main__":
    main()
