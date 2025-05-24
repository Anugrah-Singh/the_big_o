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
    
    try:
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio': (os.path.basename(audio_file_path), audio_file, 'audio/wav')}
            data = {
                'transcription_language': transcription_language,
                'src_lang': src_lang,
                'tgt_lang': tgt_lang
            }
            
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
                print(f"   🎤 Transcription: {result.get('transcription')}")
                print(f"   🌐 Translation: {result.get('translation')}")
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

def test_translation_multiple():
    """Test translation with multiple sentences"""
    print("\n🌐 Testing translation with multiple sentences...")
    
    data = {
        "sentences": [
            "Hello, how are you?",
            "What is your name?",
            "Nice to meet you!"
        ],
        "src_lang": "english",
        "tgt_lang": "kannada"
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/translate",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📥 Response status: {response.status_code}")
        result = response.json()
        print(f"📥 Response JSON: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print(f"✅ Translation successful:")
            for i, translation in enumerate(result.get('translations', [])):
                print(f"   {i+1}. {translation}")
            return True
        else:
            print(f"❌ Translation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Translation test failed: {e}")
        return False

def test_translation_string():
    """Test translation with a single string (not array)"""
    print("\n🌐 Testing translation with single string...")
    
    data = {
        "sentences": "Good morning!",
        "src_lang": "english",
        "tgt_lang": "kannada"
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/translate",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📥 Response status: {response.status_code}")
        result = response.json()
        print(f"📥 Response JSON: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print(f"✅ Translation successful:")
            for i, translation in enumerate(result.get('translations', [])):
                print(f"   {i+1}. {translation}")
            return True
        else:
            print(f"❌ Translation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Translation test failed: {e}")
        return False

def test_translation_reverse():
    """Test translation from Kannada to English"""
    print("\n🌐 Testing reverse translation (Kannada to English)...")
    
    data = {
        "sentences": ["ನಮಸ್ಕಾರ", "ನಿಮ್ಮ ಹೆಸರೇನು?"],
        "src_lang": "kannada",
        "tgt_lang": "english"
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/translate",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📥 Response status: {response.status_code}")
        result = response.json()
        print(f"📥 Response JSON: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print(f"✅ Translation successful:")
            for i, translation in enumerate(result.get('translations', [])):
                print(f"   {i+1}. {translation}")
            return True
        else:
            print(f"❌ Translation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Translation test failed: {e}")
        return False

def test_invalid_requests():
    """Test various invalid request scenarios"""
    print("\n🧪 Testing invalid translation requests...")
    
    # Test missing sentences
    try:
        data = {"src_lang": "english", "tgt_lang": "kannada"}
        response = requests.post(f"{SERVER_URL}/translate", json=data)
        print(f"Missing sentences test - Status: {response.status_code}")
        result = response.json()
        print(f"Expected error: {result.get('error')}")
    except Exception as e:
        print(f"Missing sentences test failed: {e}")
    
    # Test empty sentences
    try:
        data = {
            "sentences": [],
            "src_lang": "english",
            "tgt_lang": "kannada"
        }
        response = requests.post(f"{SERVER_URL}/translate", json=data)
        print(f"Empty sentences test - Status: {response.status_code}")
        result = response.json()
        print(f"Expected error: {result.get('error')}")
    except Exception as e:
        print(f"Empty sentences test failed: {e}")
    
    # Test no JSON data
    try:
        response = requests.post(f"{SERVER_URL}/translate")
        print(f"No JSON data test - Status: {response.status_code}")
        result = response.json()
        print(f"Expected error: {result.get('error')}")
    except Exception as e:
        print(f"No JSON data test failed: {e}")

def main():
    """Run all translation tests"""
    print("🚀 Testing Dwani Translation Server")
    print("=" * 50)
    
    # Test health first
    if not test_health():
        print("❌ Server is not healthy. Please check if it's running on port 6960")
        return
    
    # Run translation tests
    test_translation_single()
    test_translation_multiple()
    test_translation_string()
    test_translation_reverse()
    test_invalid_requests()
    
    print("\n" + "=" * 50)
    print("🎯 Translation tests completed!")
    print("\nTo use the translation endpoint:")
    print("POST /translate with JSON data:")
    print('{')
    print('  "sentences": ["text to translate"],')
    print('  "src_lang": "english",')
    print('  "tgt_lang": "kannada"')
    print('}')

if __name__ == "__main__":
    main()
