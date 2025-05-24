#!/usr/bin/env python3
"""
Test client for the Dwani ASR Transcription Server
This script demonstrates how to send requests to the server for transcription.
"""

import requests
import json
import base64
import os

# Server configuration
SERVER_URL = "http://localhost:5000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{SERVER_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_file_upload(audio_file_path, language="kannada"):
    """Test transcription by uploading an audio file"""
    print(f"\n🎤 Testing file upload transcription with {audio_file_path}...")
    
    if not os.path.exists(audio_file_path):
        print(f"❌ Audio file not found: {audio_file_path}")
        return False
    
    try:
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            data = {'language': language}
            
            response = requests.post(f"{SERVER_URL}/transcribe", files=files, data=data)
            
            print(f"Status: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print(f"✅ Transcription: {result.get('transcription')}")
                return True
            else:
                print(f"❌ Error: {result.get('error')}")
                return False
                
    except Exception as e:
        print(f"❌ File upload test failed: {e}")
        return False

def test_base64_upload(audio_file_path, language="kannada"):
    """Test transcription by sending base64 encoded audio"""
    print(f"\n📤 Testing base64 upload transcription with {audio_file_path}...")
    
    if not os.path.exists(audio_file_path):
        print(f"❌ Audio file not found: {audio_file_path}")
        return False
    
    try:
        # Read and encode audio file
        with open(audio_file_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Get file extension
        file_extension = audio_file_path.split('.')[-1].lower()
        
        # Prepare request data
        data = {
            'audio_data': audio_base64,
            'language': language,
            'file_extension': file_extension
        }
        
        # Send request
        response = requests.post(
            f"{SERVER_URL}/transcribe/text",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print(f"✅ Transcription: {result.get('transcription')}")
            return True
        else:
            print(f"❌ Error: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Base64 upload test failed: {e}")
        return False

def test_invalid_requests():
    """Test various invalid request scenarios"""
    print("\n🧪 Testing invalid requests...")
    
    # Test missing audio file
    try:
        response = requests.post(f"{SERVER_URL}/transcribe", data={'language': 'kannada'})
        print(f"Missing file test - Status: {response.status_code}")
        result = response.json()
        print(f"Expected error: {result.get('error')}")
    except Exception as e:
        print(f"Missing file test failed: {e}")
    
    # Test invalid base64 data
    try:
        data = {
            'audio_data': 'invalid_base64_data',
            'language': 'kannada'
        }
        response = requests.post(f"{SERVER_URL}/transcribe/text", json=data)
        print(f"Invalid base64 test - Status: {response.status_code}")
        result = response.json()
        print(f"Expected error: {result.get('error')}")
    except Exception as e:
        print(f"Invalid base64 test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting Dwani ASR Server Tests")
    print("=" * 50)
    
    # Test health check
    if not test_health_check():
        print("❌ Server is not running or not healthy. Please start the server first.")
        return
    
    # Look for audio files to test with
    audio_files = []
    for filename in ['kann.wav', 'kannada_sample.wav']:
        if os.path.exists(filename):
            audio_files.append(filename)
    
    if not audio_files:
        print("⚠️ No audio files found for testing. Looking for kann.wav or kannada_sample.wav")
        print("You can still test with your own audio files by modifying this script.")
    else:
        # Test with available audio files
        for audio_file in audio_files:
            test_file_upload(audio_file)
            test_base64_upload(audio_file)
    
    # Test invalid requests
    test_invalid_requests()
    
    print("\n" + "=" * 50)
    print("🎯 Tests completed!")
    print("\nTo use the server:")
    print("1. Upload file: POST /transcribe with multipart/form-data")
    print("2. Send base64: POST /transcribe/text with JSON data")
    print("3. Health check: GET /health")

if __name__ == "__main__":
    main()
