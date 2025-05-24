from flask import Flask, request, jsonify
import dwani
import json
import copy
import logging
from flask_cors import CORS
import google.generativeai as genai
import os


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# --- Dwani API Configuration ---
DWANI_API_KEY = 'abhishekr.23.becs@acharya.ac.in_dwani_krishnadevaraya'
DWANI_API_BASE = 'https://dwani-dwani-api.hf.space'

# Configure Dwani API
dwani.api_key = DWANI_API_KEY
dwani.api_base = DWANI_API_BASE

# Set API base for Chat module
if hasattr(dwani, 'Chat') and dwani.Chat is not None:
    dwani.Chat.api_base = DWANI_API_BASE
    logger.info(f"Configured Dwani Chat with API base: {DWANI_API_BASE}")

# --- Google Gemini API Configuration ---
GEMINI_API_KEY = "AIzaSyB_BJayIXwmUF_BDlk6cUjkqLn2cKtPngY"  # Set your Gemini API key as environment variable
if GEMINI_API_KEY:
    genai.configure(api_key="AIzaSyB_BJayIXwmUF_BDlk6cUjkqLn2cKtPngY")
    logger.info("Configured Google Gemini API")
else:
    logger.warning("GEMINI_API_KEY not found in environment variables. Please set it to use Gemini.")

template = {
  "name": "string",
  "age": "number",
  "symptoms": [
    {
      "symptom": "string",
      "onset": "string",
      "severity": "string"
    }
  ],
  "medical_history": {
    "conditions": ["string"],
    "allergies": ["string"]
  }
}

class TemplateUpdaterLLM:
    """LLM instance for updating the template based on user answers using Google Gemini 1.5-flash"""
    
    def __init__(self):
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not found. Template updating will not work.")
            self.model = None
        else:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def update_template(self, current_template, user_answer, conversation_history=None):
        """Update the template based on user's answer using Gemini with conversation context"""
        if not self.model:
            logger.error("Gemini model not initialized. Please set GEMINI_API_KEY environment variable.")
            return False, current_template
        
        if conversation_history is None:
            conversation_history = []
            
        try:
            # Format conversation history for context
            context_str = ""
            if conversation_history:
                context_str = "\n\nConversation History:\n"
                for i, msg in enumerate(conversation_history[-10:]):  # Last 10 messages to avoid token limits
                    if msg['type'] == 'system_question':
                        context_str += f"Assistant: {msg['content']}\n"
                    elif msg['type'] == 'user_answer':
                        context_str += f"User: {msg['content']}\n"
                    elif msg['type'] == 'system_message':
                        context_str += f"Assistant: {msg['content']}\n"
            
            # Create prompt for template updating
            prompt = f"""
You are a helpful and empathetic medical assistant helping to collect patient information. Your goal is to be understanding, conversational, supportive, and thorough while filling out a patient information template.

IMPORTANT GUIDELINES:
1. Be helpful and considerate - patients may be worried or in discomfort
2. Extract ALL relevant information from the user's answer carefully
3. Use conversation history to maintain context and avoid repetitive questions
4. Be intelligent about interpreting medical terms and symptoms
5. If information is ambiguous, make reasonable medical interpretations
6. DO NOT hallucinate or make up information not provided by the user

Current template:
{json.dumps(current_template, indent=2)}

User's current answer: {user_answer}

{context_str}

Instructions:
1. Extract relevant information from the user's answer and conversation history
2. Update the template fields with the extracted information intelligently
3. Replace "string"/"unknown" placeholders with actual values when information is provided
4. Keep existing values if the user's answer doesn't relate to those fields
5. For arrays, add new items or replace placeholder items appropriately
6. If the patient is unsure about a field or doesn't provide information, mark as 'N/A' or 'unknown'
7. Use medical knowledge to categorize symptoms appropriately
8. Consider the conversation flow - don't lose previously provided information

Return ONLY the updated template as valid JSON, no additional text or explanations:
"""
            
            # Call Google Gemini API
            response = self.model.generate_content(prompt)
            
            # Extract response text
            if hasattr(response, 'text'):
                response_text = response.text
            else:
                response_text = str(response)
            
            # Try to parse the response as JSON
            try:
                # Extract JSON from response if it contains other text
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start != -1 and json_end != 0:
                    json_str = response_text[json_start:json_end]
                    updated_template = json.loads(json_str)
                    logger.info("Template updated successfully using Gemini")
                    return True, updated_template
                else:
                    logger.error("No valid JSON found in Gemini response")
                    return False, current_template
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}")
                logger.error(f"Gemini response: {response_text}")
                return False, current_template
                
        except Exception as e:
            logger.error(f"Template update failed with Gemini: {e}")
            return False, current_template

class CompletenessCheckerLLM:
    """LLM instance for checking if template is complete and generating questions using Google Gemini 1.5-flash"""

    def __init__(self):
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not found. Completeness checking will not work.")
            self.model = None
        else:
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    def check_completeness(self, current_template, conversation_history=None, questions_asked_count=0, max_questions=15): # Added parameters
        """Check if template is complete and generate next question if needed using Gemini with conversation context"""
        if not self.model:
            logger.error("Gemini model not initialized. Please set GEMINI_API_KEY environment variable.")
            # Return assuming incomplete if model not present, but let the caller handle forced completion due to count
            return False, {"complete": False, "question": "Could you provide more details about your symptoms?"}

        if conversation_history is None:
            conversation_history = []

        # --- External check for max questions ---
        # This is an important change: if max_questions is already reached, force completion
        # We'll also add this check in the main chat_endpoint for robustness
        if questions_asked_count >= max_questions:
            logger.info(f"Max questions ({max_questions}) reached. Forcing completion.")
            return True, {"complete": True, "message": "Thank you for providing your information. We have collected the necessary details. A healthcare professional will review your case."}
        # ---

        try:
            context_str = ""
            # We don't need to rebuild asked_questions list here if we pass the count directly
            if conversation_history:
                context_str = "\n\nConversation History:\n"
                for msg in conversation_history[-15:]:  # Keep context reasonable for token limits
                    if msg['type'] == 'system_question':
                        context_str += f"Assistant asked: {msg['content']}\n"
                    elif msg['type'] == 'user_answer':
                        context_str += f"User answered: {msg['content']}\n"
                    elif msg['type'] == 'system_message':
                        context_str += f"Assistant: {msg['content']}\n"

            prompt = f"""
You are a helpful and empathetic medical assistant reviewing a patient information template for completeness. You should be considerate of the patient's situation while ensuring you collect necessary medical information.

Current template:
{json.dumps(current_template, indent=2)}

{context_str}

Number of questions already asked by the assistant: {questions_asked_count}
Maximum allowed questions for this conversation: {max_questions}

IMPORTANT GUIDELINES:
1. Be helpful, empathetic, and understanding.
2. Review conversation history to avoid asking duplicate questions.
3. Ask intelligent follow-up questions based on previous answers.
4. Prioritize the most important missing information.
5. If the number of questions asked ({questions_asked_count}) has reached or exceeded the maximum ({max_questions}), you MUST indicate the process is complete.

Instructions:
1. Evaluate if the template has sufficient information for a basic medical consultation.
2. If {questions_asked_count} >= {max_questions}:
   Respond with: {{"complete": true, "message": "Thank you! Your information has been collected successfully. A healthcare professional will review your case."}}
3. Else if the template is sufficiently complete OR if all critical information has been gathered even if slightly under {max_questions}:
   Respond with: {{"complete": true, "message": "Thank you! Your information has been collected successfully. A healthcare professional will review your case."}}
4. Else (template is incomplete and more questions can be asked):
   Respond with: {{"complete": false, "question": "Ask ONE specific, helpful, and empathetic question about the most important missing information. Ensure this question has not been effectively answered before by reviewing the conversation history."}}
5. Do not ask too many questions. If the previous question was about symptoms, consider asking about medical history next, or vice versa, if appropriate and information is missing.

Important fields to prioritize (if not yet filled and questions remaining < {max_questions}):
- Patient name and basic info (age)
- Primary symptom with clear description
- Symptom onset, duration, and severity
- Relevant medical history (conditions, allergies)

Respond with ONLY valid JSON, no additional text or explanations:
"""
            # ... (rest of your Gemini call and JSON parsing remains the same)
            # Call Google Gemini API
            response = self.model.generate_content(prompt)

            # Extract response text
            if hasattr(response, 'text'):
                response_text = response.text
            else:
                response_text = str(response)

            # Try to parse the response as JSON
            try:
                # Extract JSON from response if it contains other text
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1

                if json_start != -1 and json_end != 0:
                    json_str = response_text[json_start:json_end]
                    result_data = json.loads(json_str)

                    if 'complete' in result_data:
                        logger.info("Completeness check completed successfully using Gemini")
                        # If LLM says complete=false but we are at max questions, override
                        if not result_data.get('complete', False) and questions_asked_count >= max_questions:
                            logger.warning(f"LLM suggested incomplete, but max questions ({max_questions}) reached. Overriding to complete.")
                            return True, {"complete": True, "message": "Thank you for providing your information. We have collected the necessary details for now. A healthcare professional will review your case."}
                        return True, result_data
                    else:
                        logger.error("Invalid response format from Gemini completeness checker")
                        return False, {"complete": False, "question": "Could you provide more details about your symptoms?"}
                else:
                    logger.error("No valid JSON found in Gemini completeness checker response")
                    return False, {"complete": False, "question": "Could you provide more details about your symptoms?"}

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini completeness checker response as JSON: {e}")
                logger.error(f"Gemini response: {response_text}")
                return False, {"complete": False, "question": "Could you provide more details about your symptoms?"}

        except Exception as e:
            logger.error(f"Completeness check failed with Gemini: {e}")
            return False, {"complete": False, "question": "Could you provide more details about your symptoms?"}
        

# --- Translation Helper Function ---
def translate_text_to_language(text, target_language):
    """
    Translate text to target language using Dwani API
    
    Args:
        text (str): Text to translate
        target_language (str): Target language (e.g., 'kannada', 'english', 'hindi', etc.)
    
    Returns:
        tuple: (success, translated_text/error_message)
    """
    try:
        # If target language is English or the text is already in target language, return as is
        if target_language.lower() in ['english', 'en'] or not text.strip():
            return True, text
            
        logger.info(f"=== TRANSLATING TEXT ===")
        logger.info(f"Text: {text}")
        logger.info(f"Target language: {target_language}")
        
        # Force API base configuration before call
        if hasattr(dwani, 'Translate'):
            dwani.Translate.api_base = DWANI_API_BASE
        
        # Call Dwani Translate API
        result = dwani.Translate.run_translate(
            sentences=[text],
            src_lang='english',  # Assuming the chat responses are in English
            tgt_lang=target_language.lower()
        )
        
        logger.info(f"=== TRANSLATION SUCCESS ===")
        logger.info(f"Raw result: {result}")
        
        # Extract translated text
        if isinstance(result, list) and len(result) > 0:
            translated_text = result[0]
        elif isinstance(result, dict):
            translated_text = result.get('translations', result.get('text', [text]))[0] if result.get('translations') or result.get('text') else text
        elif isinstance(result, str):
            translated_text = result
        else:
            translated_text = str(result) if result else text
        
        if translated_text and translated_text.strip():
            return True, translated_text.strip()
        else:
            logger.warning("Translation returned empty, using original text")
            return True, text  # Return original text if translation is empty
            
    except Exception as e:
        logger.error(f"=== TRANSLATION FAILED ===")
        logger.error(f"Error: {e}")
        logger.error(f"Error type: {type(e)}")
        # Return original text if translation fails
        logger.warning("Translation failed, returning original text")
        return True, text

# Initialize LLM instances
template_updater = TemplateUpdaterLLM()
completeness_checker = CompletenessCheckerLLM()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Medical chatbot server is running',
        'api_base': DWANI_API_BASE
    })

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        logger.info("=== CHAT REQUEST RECEIVED ===")
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided. Please send template and answer.'
            }), 400

        current_template = data.get('template')
        user_answer = data.get('answer')
        conversation_history = data.get('conversation_history', [])
        target_language = data.get('language', 'english')  # Get target language, default to English
        MAX_QUESTIONS_ALLOWED = 10 # Define your limit

        if not current_template:
            current_template = copy.deepcopy(template)

        if not user_answer or not user_answer.strip():
            return jsonify({
                'success': False,
                'error': 'No answer provided. Please include an "answer" field.'
            }), 400

        logger.info(f"Processing answer: {user_answer}")
        logger.info(f"Target language: {target_language}")
        logger.info(f"Conversation history has {len(conversation_history)} messages")

        # Add user's current answer to history *before* processing
        # This makes the history more complete for the current turn's decisions
        # Ensure no duplicate user_answer if client sends full history including last user message
        if not conversation_history or conversation_history[-1].get('content') != user_answer.strip() or conversation_history[-1].get('type') != 'user_answer':
            conversation_history.append({
                'type': 'user_answer',
                'content': user_answer.strip(),
                'timestamp': None # Could add timestamp if needed
            })
        else:
            logger.info("Last message in history is already the current user answer. Not appending.")


        logger.info("Step 1: Updating template...")
        update_success, updated_template = template_updater.update_template(
            current_template, user_answer.strip(), conversation_history # Pass full history here
        )

        if not update_success:
            return jsonify({
                'success': False,
                'error': 'Failed to update template',
                'template': current_template,
                'conversation_history': conversation_history # Send back history
            }), 500
        logger.info("Template updated successfully")

        # Count how many questions the system has asked so far
        num_system_questions = sum(1 for msg in conversation_history if msg['type'] == 'system_question')
        logger.info(f"Number of questions asked by system so far: {num_system_questions}")


        response_data = {
            'success': True,
            'updated_template': updated_template,
        }
        updated_conversation_history = conversation_history.copy() # Start with the history that includes the current user answer

        # --- HARD CHECK FOR MAX QUESTIONS ---
        if num_system_questions >= MAX_QUESTIONS_ALLOWED:
            logger.info(f"Maximum number of questions ({MAX_QUESTIONS_ALLOWED}) reached. Forcing completion.")
            completion_message = "Thank you! Your information has been collected successfully as we've reached our question limit. A healthcare professional will review your case."
            
            # Translate completion message if needed
            translation_success, translated_message = translate_text_to_language(completion_message, target_language)
            if translation_success:
                completion_message = translated_message
            
            response_data['complete'] = True
            response_data['message'] = completion_message
            # Append final system message to history
            updated_conversation_history.append({
                'type': 'system_message',
                'content': completion_message,
                'timestamp': None
            })
        else:
            # --- Proceed to check completeness with LLM only if under question limit ---
            logger.info("Step 2: Checking template completeness (under question limit)...")
            check_success, completeness_result = completeness_checker.check_completeness(
                updated_template,
                updated_conversation_history, # Pass history that includes the latest user answer
                questions_asked_count=num_system_questions, # Pass current count
                max_questions=MAX_QUESTIONS_ALLOWED
            )

            if not check_success:
                return jsonify({
                    'success': False,
                    'error': 'Failed to check template completeness',
                    'template': updated_template,
                    'conversation_history': updated_conversation_history
                }), 500

            response_data['complete'] = completeness_result.get('complete', False)

            if response_data['complete']:
                completion_message = completeness_result.get(
                    'message',
                    'Thank you! Your medical information has been collected successfully.'
                )
                
                # Translate completion message if needed
                translation_success, translated_message = translate_text_to_language(completion_message, target_language)
                if translation_success:
                    completion_message = translated_message
                
                response_data['message'] = completion_message
                updated_conversation_history.append({
                    'type': 'system_message',
                    'content': completion_message,
                    'timestamp': None
                })
                logger.info("Template collection completed by LLM or limit.")
            else:
                # Check again if LLM wants to ask a question but we are now at the limit
                # This can happen if num_system_questions was MAX_QUESTIONS_ALLOWED - 1,
                # and the LLM generates one more question.
                if num_system_questions + 1 > MAX_QUESTIONS_ALLOWED and completeness_result.get('question'): # If asking one more makes it over
                    logger.info(f"LLM wanted to ask another question, but it would exceed max questions. Forcing completion.")
                    completion_message = "Thank you! We've gathered sufficient information for now. A healthcare professional will review your case."
                    
                    # Translate completion message if needed
                    translation_success, translated_message = translate_text_to_language(completion_message, target_language)
                    if translation_success:
                        completion_message = translated_message
                    
                    response_data['complete'] = True
                    response_data['message'] = completion_message
                    updated_conversation_history.append({
                        'type': 'system_message',
                        'content': completion_message,
                        'timestamp': None
                    })
                else:
                    next_question = completeness_result.get(
                        'question',
                        'Could you provide more details about your symptoms?'
                    )
                    
                    # Translate question if needed
                    translation_success, translated_question = translate_text_to_language(next_question, target_language)
                    if translation_success:
                        next_question = translated_question
                    
                    response_data['next_question'] = next_question
                    updated_conversation_history.append({
                        'type': 'system_question',
                        'content': next_question,
                        'timestamp': None
                    })
                    logger.info(f"Next question: {next_question}")

        response_data['conversation_history'] = updated_conversation_history
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Unexpected chat error: {e}", exc_info=True) # exc_info=True for traceback
        return jsonify({
            'success': False,
            'error': f'Unexpected server error: {str(e)}'
        }), 500
@app.route('/start', methods=['GET'])
def start_chat():
    """
    Start a new chat session with the initial question
    
    Parameters:
    - language (optional): Target language for responses (default: 'english')
    
    Returns:
    {
        "success": true,
        "template": {...}, // Initial empty template
        "question": "Hello! I'm here to help collect your medical information. What is your name?",
        "conversation_history": []
    }
    """
    try:
        # Get language parameter from query string
        target_language = request.args.get('language', 'english')
        
        initial_template = copy.deepcopy(template)
        initial_question = "Hello! I'm here to help collect your medical information. I understand this might be concerning, but I'm here to help. Could you please start by telling me your name?"
        
        # Translate initial question if needed
        translation_success, translated_question = translate_text_to_language(initial_question, target_language)
        if translation_success:
            initial_question = translated_question
        
        # Initialize conversation history
        conversation_history = [{
            'type': 'system_question',
            'content': initial_question,
            'timestamp': None
        }]
        
        return jsonify({
            'success': True,
            'template': initial_template,
            'question': initial_question,
            'conversation_history': conversation_history
        })
        
    except Exception as e:
        logger.error(f"Error starting chat: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start chat: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found. Available endpoints: /health (GET), /chat (POST), /start (GET)'
    }), 404

if __name__ == '__main__':
    logger.info("Starting Medical Chatbot Server...")
    logger.info(f"API Base: {DWANI_API_BASE}")
    logger.info("Available endpoints:")
    logger.info("  GET  /health - Health check")
    logger.info("  GET  /start - Start new chat session")
    logger.info("  POST /chat - Process user answer and update template")
    
    # Run the server
    app.run(
        host='0.0.0.0',  # Allow external connections
        port=6969,
        debug=True
    )
