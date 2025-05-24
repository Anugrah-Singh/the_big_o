#!/usr/bin/env python3
"""
Example usage of the Medical Chatbot API
"""

import requests
import json

SERVER_URL = "http://localhost:6969"

def chatbot_example():
    """Demonstrate how to use the medical chatbot API"""
    
    print("🏥 Medical Chatbot Example")
    print("=" * 40)
    
    try:
        # Step 1: Start a new chat session
        print("1. Starting new chat session...")
        response = requests.get(f"{SERVER_URL}/start")
        
        if response.status_code != 200:
            print(f"❌ Failed to start chat: {response.status_code}")
            return
        
        result = response.json()
        current_template = result['template']
        current_question = result['question']
        
        print(f"✅ Chat started!")
        print(f"Initial question: {current_question}")
        
        # Step 2: Simulate conversation
        conversation_complete = False
        interaction_count = 0
        max_interactions = 10  # Prevent infinite loop
        
        # Example user responses (you would get these from user input)
        example_responses = [
            "My name is Alice Johnson",
            "I am 28 years old", 
            "I have been having chest pain",
            "The pain started yesterday evening",
            "It's a sharp pain in the center of my chest",
            "The pain is about 6 out of 10 in severity",
            "It gets worse when I take deep breaths",
            "Sitting upright seems to help a little",
            "No chronic conditions",
            "alice.johnson@email.com and my phone is 555-1234"
        ]
        
        while not conversation_complete and interaction_count < max_interactions:
            interaction_count += 1
            
            # Get user response (in real app, this would be user input)
            if interaction_count <= len(example_responses):
                user_answer = example_responses[interaction_count - 1]
                print(f"\n--- Interaction {interaction_count} ---")
                print(f"Question: {current_question}")
                print(f"User answer: {user_answer}")
            else:
                # Fallback if we run out of example responses
                user_answer = "I don't have any additional information to provide."
                print(f"\n--- Interaction {interaction_count} ---")
                print(f"Question: {current_question}")
                print(f"User answer: {user_answer}")
            
            # Step 3: Send user response to chatbot
            chat_data = {
                "template": current_template,
                "answer": user_answer
            }
            
            chat_response = requests.post(
                f"{SERVER_URL}/chat",
                json=chat_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if chat_response.status_code != 200:
                print(f"❌ Chat failed: {chat_response.status_code}")
                break
            
            chat_result = chat_response.json()
            
            if not chat_result.get('success'):
                print(f"❌ Chat error: {chat_result.get('error')}")
                break
            
            # Update template and check if complete
            current_template = chat_result['updated_template']
            conversation_complete = chat_result.get('complete', False)
            
            if conversation_complete:
                print(f"✅ {chat_result.get('message')}")
                print("\n🎉 Conversation completed!")
                print("\nFinal collected information:")
                print(json.dumps(current_template, indent=2))
                break
            else:
                current_question = chat_result.get('next_question')
                print(f"Next question: {current_question}")
        
        if not conversation_complete:
            print(f"\n⚠️ Conversation not completed after {interaction_count} interactions")
            print("In a real application, you would continue asking questions until complete.")
    
    except Exception as e:
        print(f"❌ Example failed: {e}")

if __name__ == "__main__":
    chatbot_example()
