#!/usr/bin/env python3
"""
Test script for the Medical Chatbot endpoint
"""

import requests
import json

# Server configuration
SERVER_URL = "http://localhost:6969"

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

def test_start_chat():
    """Test starting a new chat session"""
    print("\n🚀 Testing /start endpoint...")
    try:
        response = requests.get(f"{SERVER_URL}/start")
        print(f"📥 Start chat status: {response.status_code}")
        result = response.json()
        print(f"📥 Response: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print(f"✅ Chat started successfully")
            print(f"Initial question: {result.get('question')}")
            return True, result.get('template'), result.get('question')
        else:
            print(f"❌ Failed to start chat: {result.get('error')}")
            return False, None, None
            
    except Exception as e:
        print(f"❌ Start chat test failed: {e}")
        return False, None, None

def test_chat_interaction(template, answer):
    """Test a chat interaction"""
    print(f"\n💬 Testing chat interaction with answer: '{answer}'...")
    try:
        data = {
            "template": template,
            "answer": answer
        }
        
        response = requests.post(
            f"{SERVER_URL}/chat",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📥 Chat response status: {response.status_code}")
        result = response.json()
        print(f"📥 Response: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print(f"✅ Chat interaction successful")
            
            if result.get('complete'):
                print(f"🎉 Template completed! Message: {result.get('message')}")
                return True, result.get('updated_template'), None, True
            else:
                print(f"❓ Next question: {result.get('next_question')}")
                return True, result.get('updated_template'), result.get('next_question'), False
        else:
            print(f"❌ Chat interaction failed: {result.get('error')}")
            return False, template, None, False
            
    except Exception as e:
        print(f"❌ Chat interaction test failed: {e}")
        return False, template, None, False

def test_complete_conversation():
    """Test a complete conversation flow"""
    print("\n🗣️ Testing complete conversation flow...")
    
    # Start chat
    success, template, question = test_start_chat()
    if not success:
        return False
    
    # Simulate user answers
    user_answers = [
        "My name is John Doe",
        "I am 35 years old",
        "I have been experiencing severe headaches for the past 3 days",
        "The headaches started suddenly on Monday morning",
        "The pain is located in my forehead and temples",
        "The headaches are very severe, about 8 out of 10",
        "Bright lights seem to make it worse",
        "Taking rest in a dark room helps a bit",
        "I don't have any chronic medical conditions",
        "I don't take any regular medications",
        "No known allergies",
        "I don't smoke and rarely drink alcohol",
        "My email is john.doe@email.com and phone is 555-0123",
        "My emergency contact is my wife Sarah at 555-0124"
    ]
    
    current_template = template
    current_question = question
    completed = False
    
    for i, answer in enumerate(user_answers):
        if completed:
            break
            
        print(f"\n--- Interaction {i + 1} ---")
        print(f"Question: {current_question}")
        print(f"Answer: {answer}")
        
        success, updated_template, next_question, is_complete = test_chat_interaction(
            current_template, answer
        )
        
        if not success:
            print(f"❌ Conversation failed at step {i + 1}")
            return False
        
        current_template = updated_template
        current_question = next_question
        completed = is_complete
        
        if completed:
            print(f"\n🎉 Conversation completed successfully after {i + 1} interactions!")
            break
    
    if not completed:
        print(f"\n⚠️ Conversation not completed after {len(user_answers)} interactions")
        print(f"Next question would be: {current_question}")
    
    return completed

def test_invalid_requests():
    """Test various invalid request scenarios"""
    print("\n🧪 Testing invalid requests...")
    
    # Test missing JSON data
    try:
        response = requests.post(f"{SERVER_URL}/chat")
        print(f"Missing JSON test - Status: {response.status_code}")
        result = response.json()
        print(f"Expected error: {result.get('error')}")
    except Exception as e:
        print(f"Missing JSON test failed: {e}")
    
    # Test missing answer
    try:
        data = {"template": {}}
        response = requests.post(f"{SERVER_URL}/chat", json=data)
        print(f"Missing answer test - Status: {response.status_code}")
        result = response.json()
        print(f"Expected error: {result.get('error')}")
    except Exception as e:
        print(f"Missing answer test failed: {e}")
    
    # Test empty answer
    try:
        data = {
            "template": {},
            "answer": ""
        }
        response = requests.post(f"{SERVER_URL}/chat", json=data)
        print(f"Empty answer test - Status: {response.status_code}")
        result = response.json()
        print(f"Expected error: {result.get('error')}")
    except Exception as e:
        print(f"Empty answer test failed: {e}")

def main():
    """Run all chatbot tests"""
    print("🚀 Testing Medical Chatbot Server")
    print("=" * 50)
    
    # Test health first
    if not test_health():
        print("❌ Server is not healthy. Please check if it's running on port 5000")
        return
    
    # Run chatbot tests
    test_start_chat()
    test_complete_conversation()
    test_invalid_requests()
    
    print("\n" + "=" * 50)
    print("🎯 Medical chatbot tests completed!")
    print("\nTo use the medical chatbot:")
    print("1. Start chat: GET /start")
    print("2. Chat interaction: POST /chat with JSON:")
    print("   {")
    print('     "template": {...current_template...},')
    print('     "answer": "user response"')
    print("   }")
    print("3. Continue until template is complete")
    
    print("\nExample conversation flow:")
    print("1. GET /start -> receives initial question")
    print("2. POST /chat with user's name -> receives age question")
    print("3. POST /chat with user's age -> receives symptom question")
    print("4. Continue until complete")

if __name__ == "__main__":
    main()
