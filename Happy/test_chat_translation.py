#!/usr/bin/env python3
"""
Test script for chat endpoint with language translation
"""
import requests
import json
import time

# Server configuration
SERVER_URL = "http://localhost:6969"

def test_health():
    """Test if the chat server is running"""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Chat server is healthy")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_start_chat_with_language(language="kannada"):
    """Test starting a chat session with language parameter"""
    try:
        print(f"\n📝 Testing start chat with language: {language}")
        response = requests.get(f"{SERVER_URL}/start?language={language}", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Start chat successful")
            print(f"Initial question: {result.get('question', 'N/A')}")
            return result
        else:
            print(f"❌ Start chat failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Start chat failed: {e}")
        return None

def test_chat_with_language(template, conversation_history, answer, language="kannada"):
    """Test chat endpoint with language parameter"""
    try:
        print(f"\n💬 Testing chat with language: {language}")
        print(f"Answer: {answer}")
        
        data = {
            "template": template,
            "answer": answer,
            "conversation_history": conversation_history,
            "language": language
        }
        
        response = requests.post(
            f"{SERVER_URL}/chat",
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chat response successful")
            
            if result.get('complete'):
                print(f"📋 Conversation completed!")
                print(f"Final message: {result.get('message', 'N/A')}")
            else:
                print(f"❓ Next question: {result.get('next_question', 'N/A')}")
            
            return result
        else:
            print(f"❌ Chat failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Chat failed: {e}")
        return None

def test_english_workflow():
    """Test complete workflow in English"""
    print("\n" + "="*60)
    print("🇺🇸 TESTING ENGLISH WORKFLOW")
    print("="*60)
    
    # Start chat in English
    start_result = test_start_chat_with_language("english")
    if not start_result:
        return
    
    # First interaction
    chat_result = test_chat_with_language(
        start_result['template'],
        start_result['conversation_history'],
        "My name is John Doe",
        "english"
    )
    
    if chat_result and not chat_result.get('complete'):
        # Second interaction
        chat_result = test_chat_with_language(
            chat_result['updated_template'],
            chat_result['conversation_history'],
            "I am 35 years old and have been experiencing severe headaches for the past 3 days",
            "english"
        )

def test_kannada_workflow():
    """Test complete workflow in Kannada"""
    print("\n" + "="*60)
    print("🇮🇳 TESTING KANNADA WORKFLOW")
    print("="*60)
    
    # Start chat in Kannada
    start_result = test_start_chat_with_language("kannada")
    if not start_result:
        return
    
    # First interaction
    chat_result = test_chat_with_language(
        start_result['template'],
        start_result['conversation_history'],
        "My name is Ravi Kumar",
        "kannada"
    )
    
    if chat_result and not chat_result.get('complete'):
        # Second interaction  
        chat_result = test_chat_with_language(
            chat_result['updated_template'],
            chat_result['conversation_history'],
            "I am 28 years old and have been having stomach pain for 2 days",
            "kannada"
        )

def main():
    """Run all translation tests"""
    print("🚀 Testing Chat Server with Language Translation")
    print("=" * 60)
    
    # Test health first
    if not test_health():
        print("❌ Chat server is not healthy. Please check if it's running on port 6969")
        print("💡 Run: python chat.py")
        return
    
    # Test English workflow
    test_english_workflow()
    
    # Wait a bit between tests
    time.sleep(2)
    
    # Test Kannada workflow
    test_kannada_workflow()
    
    print("\n" + "=" * 60)
    print("🎯 Translation tests completed!")
    print("\n📖 Usage:")
    print("GET /start?language=kannada - Start chat in Kannada")
    print("POST /chat with JSON:")
    print('{')
    print('  "template": {...},')
    print('  "answer": "user response",')
    print('  "conversation_history": [...],')
    print('  "language": "kannada"')
    print('}')

if __name__ == "__main__":
    main()
