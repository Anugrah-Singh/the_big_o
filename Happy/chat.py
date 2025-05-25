from flask import Flask, request, jsonify
import dwani
import json
import copy
import logging
from flask_cors import CORS
import google.generativeai as genai
import os
import requests # Added import
import tempfile
from werkzeug.utils import secure_filename
from flask import send_file


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
  "age": "string",
  "blood_group": "string",
  "dob": "string",
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
6. Don't ever ask for personal information like phone number, email, address etc

Important fields to prioritize (if not yet filled and questions remaining < {max_questions}):
- Patient name and (age), blood group, date of birth
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

# --- Final Summary Template ---
final_summary_template_structure = {
    "patient_name": "Full name of the patient",
    "date_of_birth": "Date of birth in YYYY-MM-DD format",
    "gender": "Patient's gender (Male, Female, Other)",
    "blood_group": "Blood type of the patient",
    "contact_info": "Relevant contact details if required",
    "summary": "Brief conclusion about the patient's current health status, treatment progress, and doctor's recommendations",
    "detailed_history": {}, # Placeholder for more detailed structured data if extracted
    "medical_history": {}, # Placeholder
    "medical_condition": {}, # Placeholder
    "current_medication": {}, # Placeholder
    "test_results": {}, # Placeholder
    "lifestyle_risk_factors": {} # Placeholder
}

class FinalSummaryLLM:
    """LLM instance for generating a final patient summary using Google Gemini."""
    def __init__(self):
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not found. Final summary generation will not work.")
            self.model = None
        else:
            self.model = genai.GenerativeModel('gemini-1.5-flash') # Or your preferred Gemini model

    def generate_summary(self, conversation_history, summary_structure):
        if not self.model:
            logger.error("Gemini model not initialized for FinalSummaryLLM. Please set GEMINI_API_KEY.")
            return False, {"error": "Model not initialized"}

        try:
            # Format conversation history for the prompt
            formatted_history = "\\n".join([
                f"{msg['type'].replace('_', ' ').capitalize()}: {msg['content']}"
                for msg in conversation_history
            ])

            prompt = f"""
You are a medical scribe AI. Based on the entire following conversation history, your task is to meticulously fill out the provided JSON template with all relevant patient information.
Be comprehensive and accurate. If specific details for a field are not explicitly mentioned in the conversation, use "Not specified" or leave the corresponding structured field (like medical_history) as an empty object.

Conversation History:
{formatted_history}

JSON Template to fill:
{json.dumps(summary_structure, indent=2)}

Instructions:
1.  Carefully read the entire conversation history.
2.  Extract all pertinent information for each field in the JSON template.
3.  For "summary", provide a concise paragraph summarizing the patient's situation, key symptoms, and any mentioned next steps or advice.
4.  For structured fields like "detailed_history", "medical_history", etc., populate them based on information gathered. If these were part of the earlier data collection template, try to map them. If not, extract relevant details from the conversation.
5.  Ensure the output is ONLY the filled JSON object, with no additional text, explanations, or markdown.

Return ONLY the updated JSON summary:
"""
            response = self.model.generate_content(prompt)
            
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != 0:
                json_str = response_text[json_start:json_end]
                generated_summary = json.loads(json_str)
                logger.info("Final summary generated successfully using Gemini.")
                return True, generated_summary
            else:
                logger.error("No valid JSON found in Gemini response for final summary.")
                logger.error(f"Gemini response: {response_text}")
                return False, {"error": "No valid JSON in response"}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response for final summary as JSON: {e}")
            logger.error(f"Gemini response: {response_text}")
            return False, {"error": f"JSON parsing error: {e}"}
        except Exception as e:
            logger.error(f"Final summary generation failed with Gemini: {e}", exc_info=True)
            return False, {"error": f"API call failed: {e}"}

# Initialize LLM instances
template_updater = TemplateUpdaterLLM()
completeness_checker = CompletenessCheckerLLM()
final_summary_generator = FinalSummaryLLM() # Add this line

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
        print(data.get('language'))
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
                    'Thank you! Your information has been collected successfully. A healthcare professional will review your case.'
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

        # --- Generate Final Summary if complete ---
        if response_data.get('complete'):
            logger.info("Step 3: Generating final summary...")
            summary_success, generated_summary = final_summary_generator.generate_summary(
                updated_conversation_history, # Use the most up-to-date history
                final_summary_template_structure # Pass the base structure
            )
            if summary_success:
                response_data['final_summary'] = generated_summary
                logger.info("Final summary generated.")

                # --- Save the generated summary to the database ---
                try:
                    # Assuming your Flask app is running on localhost:5000 or the relevant port
                    # and the /save_detailed_report endpoint is part of the same app.
                    # We need to construct the full URL.
                    # If running locally and this is the same app, you might need to adjust
                    # if the server is not on default http://127.0.0.1:5000/
                    # For now, let's assume it's a relative path accessible during the request context
                    # However, for robustness, an absolute URL is better if this were a separate service.
                    # Since it's the same app, we can call the function directly or use test_client,
                    # but a request is more illustrative of a microservice architecture

                    # Get base URL for the current request
                    base_url = 'http://192.168.28.205:2000'

                    save_report_url = f"{base_url}/save_detailed_report"
                    
                    logger.info(f"Attempting to save report to: {save_report_url}")
                    save_response = requests.post(save_report_url, json=generated_summary)
                    
                    if save_response.status_code == 200 or save_response.status_code == 201:
                        logger.info(f"Successfully saved detailed report. Response: {save_response.json()}")
                    else:
                        logger.error(f"Failed to save detailed report. Status: {save_response.status_code}, Response: {save_response.text}")
                        # Optionally, you could add this error to the main response if critical
                        # response_data['save_report_error'] = f"Failed to save report: {save_response.status_code}"
                except requests.exceptions.RequestException as req_err:
                    logger.error(f"Error making request to save_detailed_report: {req_err}")
                    # response_data['save_report_error'] = f"Error saving report: {req_err}"
                except Exception as e_save:
                    logger.error(f"An unexpected error occurred while trying to save the detailed report: {e_save}", exc_info=True)
                    # response_data['save_report_error'] = f"Unexpected error saving report: {e_save}"
                # --- End of save block ---
            else:
                logger.error("Failed to generate final summary.")
                # Optionally, reflect this failure in the response
                # response_data['final_summary_error'] = "Failed to generate final summary"
        
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True) # Log full traceback
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

@app.route('/save_detailed_report', methods=['POST'])
def save_detailed_report():
    """
    Endpoint to save detailed report of a patient.
    Accepts JSON data in the request body.
    """
    try:
        report_data = request.get_json()
        if not report_data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        # Here you would typically save the report_data to your database
        # For example, using SQLAlchemy, a direct DB connection, or another service call.
        # This is a placeholder for your actual database saving logic.
        logger.info(f"Received report data to save: {json.dumps(report_data, indent=2)}")
        
        # --- Placeholder for DB saving logic ---
        # Example:
        # db_session.add(PatientReport(**report_data))
        # db_session.commit()
        # For now, we'll just log it and return success.
        # --- End Placeholder ---

        return jsonify({"success": True, "message": "Report saved successfully."}), 201 # 201 Created is often used for successful POSTs
    except Exception as e:
        logger.error(f"Error in save_detailed_report: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"Server error: {e}"}), 500

@app.route('/vass', methods=['POST'])
def vass_chat():
    try:
        logger.info("=== VASS CHAT REQUEST RECEIVED ===")
        
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No audio file part"}), 400
        
        file = request.files['file']
        language = request.form.get('language', 'english') # Default to English if not provided

        if file.filename == '':
            return jsonify({"success": False, "error": "No selected file"}), 400

        if not language:
            return jsonify({"success": False, "error": "Language parameter is required"}), 400

        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        temp_audio_path = os.path.join(temp_dir, filename)
        file.save(temp_audio_path)
        
        logger.info(f"Audio file saved to {temp_audio_path}")
        logger.info(f"Target language: {language}")

        # 1. Transcribe audio to text
        try:
            # Ensure Dwani API base is set
            if hasattr(dwani, 'ASR') and dwani.ASR is not None: # Changed from Audio to ASR
                dwani.ASR.api_base = DWANI_API_BASE # Set API base for ASR module
            
            transcription_result = dwani.ASR.transcribe( # Changed from dwani.Audio.run_transcribe
                file_path=temp_audio_path,
                language=language.lower() 
            )
            
            if isinstance(transcription_result, dict):
                user_text = transcription_result.get('text')
            elif isinstance(transcription_result, str): # Assuming direct text string if not dict
                user_text = transcription_result
            else: # Fallback if unexpected format
                user_text = str(transcription_result)


            if not user_text or not user_text.strip():
                logger.error(f"Transcription failed or returned empty text. Result: {transcription_result}")
                return jsonify({"success": False, "error": "Failed to transcribe audio or transcription was empty."}), 500
            logger.info(f"Transcription successful: {user_text}")
        except Exception as e_transcribe:
            logger.error(f"Error during audio transcription: {e_transcribe}", exc_info=True)
            return jsonify({"success": False, "error": f"Transcription error: {e_transcribe}"}), 500
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)

        # 2. Process text through chat logic (adapted from chat_endpoint)
        # We need to manage template and conversation_history.
        # For a VASS interaction, we might need to decide how state is passed.
        # For simplicity, let's assume each /vass call can be somewhat independent or
        # the client sends the necessary state (template, history).
        # Here, we'll assume a new/default template for each audio interaction for now.
        # A more robust solution would involve session management or client-side state.

        current_template_json = request.form.get('template')
        conversation_history_json = request.form.get('conversation_history', '[]')

        try:
            current_template = json.loads(current_template_json) if current_template_json else copy.deepcopy(template)
            conversation_history = json.loads(conversation_history_json)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON for template or conversation_history, using defaults.")
            current_template = copy.deepcopy(template)
            conversation_history = []
        
        MAX_QUESTIONS_ALLOWED = 15 # As defined in chat_endpoint

        # Add transcribed user text to history
        if not conversation_history or conversation_history[-1].get('content') != user_text.strip() or conversation_history[-1].get('type') != 'user_answer':
            conversation_history.append({
                'type': 'user_answer',
                'content': user_text.strip(),
                'timestamp': None 
            })

        logger.info("Step 1 (VASS): Updating template with transcribed text...")
        update_success, updated_template = template_updater.update_template(
            current_template, user_text.strip(), conversation_history
        )

        if not update_success:
            # If template update fails, we might not have a specific text response.
            # Consider a generic audio error message.
            error_message_text = "I'm sorry, I encountered an issue processing your information."
            # Fallthrough to generate audio for this error message.
        else:
            logger.info("Template updated successfully (VASS)")

        num_system_questions = sum(1 for msg in conversation_history if msg['type'] == 'system_question')
        
        response_text_to_speak = None
        is_complete = False
        updated_conversation_history = conversation_history.copy()

        if num_system_questions >= MAX_QUESTIONS_ALLOWED and update_success:
            logger.info(f"Max questions reached in VASS. Forcing completion.")
            response_text_to_speak = "Thank you! Your information has been collected successfully as we've reached our question limit."
            is_complete = True
            updated_conversation_history.append({
                'type': 'system_message',
                'content': response_text_to_speak, # Original English for history
                'timestamp': None
            })
        elif not update_success:
             response_text_to_speak = "I'm sorry, I had trouble understanding that. Could you please try again?"
             # No change to completeness or history for this specific error path yet
        else:
            logger.info("Step 2 (VASS): Checking template completeness...")
            check_success, completeness_result = completeness_checker.check_completeness(
                updated_template,
                updated_conversation_history,
                questions_asked_count=num_system_questions,
                max_questions=MAX_QUESTIONS_ALLOWED
            )

            if not check_success:
                response_text_to_speak = "I'm having a little trouble processing that. Let's try again."
                # No change to completeness or history for this specific error path yet
            else:
                is_complete = completeness_result.get('complete', False)
                if is_complete:
                    response_text_to_speak = completeness_result.get(
                        'message',
                        'Thank you! Your information has been collected successfully.'
                    )
                    updated_conversation_history.append({
                        'type': 'system_message',
                        'content': response_text_to_speak, # Original English for history
                        'timestamp': None
                    })
                else:
                    # Check for LLM wanting to ask a question that would exceed limit
                    if num_system_questions + 1 > MAX_QUESTIONS_ALLOWED and completeness_result.get('question'):
                        logger.info(f"LLM wanted to ask another question, but it would exceed max questions (VASS). Forcing completion.")
                        response_text_to_speak = "Thank you! We've gathered sufficient information for now."
                        is_complete = True
                        updated_conversation_history.append({
                            'type': 'system_message',
                            'content': response_text_to_speak, # Original English for history
                            'timestamp': None
                        })
                    else:
                        response_text_to_speak = completeness_result.get(
                            'question',
                            'Could you provide more details?'
                        )
                        updated_conversation_history.append({
                            'type': 'system_question',
                            'content': response_text_to_speak, # Original English for history
                            'timestamp': None
                        })
        
        final_summary_json = None
        if is_complete and update_success and check_success: # Only generate summary if prior steps were okay
            logger.info("Step 3 (VASS): Generating final summary...")
            summary_success, generated_summary = final_summary_generator.generate_summary(
                updated_conversation_history, 
                final_summary_template_structure
            )
            if summary_success:
                final_summary_json = json.dumps(generated_summary) # For potential inclusion in response
                logger.info("Final summary generated (VASS).")
                # Saving logic could be added here if needed, similar to chat_endpoint
            else:
                logger.error("Failed to generate final summary (VASS).")


        # 3. Convert response text to speech
        if not response_text_to_speak: # Fallback if no text was set
            response_text_to_speak = "I'm sorry, an unexpected error occurred."

        # Translate the response_text_to_speak to the target language *before* TTS
        # The TTS engine itself might handle language, but our text should be in the target lang.
        # However, the dwani.Audio.speech takes 'language' as a param, implying it handles translation or expects input in that lang.
        # Let's assume dwani.Audio.speech expects the *input text* to be in the target language if language param is also target.
        # Or, it expects English input and *it* translates then synthesizes.
        # The example `dwani.Audio.speech(input="ಕರ್ನಾಟಕ ದ ರಾಜಧಾನಿ ಯಾವುದು", response_format="mp3")` suggests input is already in target lang.
        # So, we should translate our `response_text_to_speak` first.

        translation_for_tts_success, text_for_tts = translate_text_to_language(response_text_to_speak, language)
        if not translation_for_tts_success:
            logger.warning(f"Failed to translate response text for TTS, using original: {response_text_to_speak}")
            # Use original English text if translation fails, and hope TTS can handle it or defaults.
            # Or, set language for TTS to 'english' in this case. For now, proceed with original text.
            text_for_tts = response_text_to_speak # Fallback to original text

        logger.info(f"Text for TTS (after attempting translation to {language}): {text_for_tts}")

        temp_response_audio_dir = tempfile.mkdtemp()
        # It's good practice to use a unique name for the output file too.
        temp_response_audio_filename = f"response_{secure_filename(language)}.mp3"
        temp_response_audio_path = os.path.join(temp_response_audio_dir, temp_response_audio_filename)

        try:
            if hasattr(dwani, 'Audio') and dwani.Audio is not None:
                dwani.Audio.api_base = DWANI_API_BASE # Ensure API base
            
            # The example `dwani.Audio.speech(input="ಕರ್ನಾಟಕ ದ ರಾಜಧಾನಿ ಯಾವುದು", response_format="mp3")`
            # does not specify a language parameter. If the `input` is already in the target language,
            # the `language` parameter to `speech` might be for voice selection or internal routing.
            # Let's assume the `input` text should be in the target language.
            speech_response_content = dwani.Audio.speech(
                input=text_for_tts, # Text already translated to target language
                response_format="mp3" # Assuming mp3 is desired
                # language=language.lower() # If the speech API needs a language hint for voice/accent
            )
            
            with open(temp_response_audio_path, "wb") as f:
                f.write(speech_response_content)
            logger.info(f"Response audio saved to {temp_response_audio_path}")

            # Prepare metadata to send along with the audio
            response_metadata = {
                "success": True,
                "text_spoken": text_for_tts, # The actual text that was converted to speech
                "original_response_text": response_text_to_speak, # The English version before TTS translation
                "language": language,
                "conversation_history": updated_conversation_history,
                "updated_template": updated_template if update_success else current_template,
                "complete": is_complete
            }
            if final_summary_json:
                response_metadata["final_summary"] = json.loads(final_summary_json)


            # Use a custom header to send JSON metadata, as send_file is for the file itself.
            # One way is to use a multipart response, but that's more complex.
            # A simpler way for now: send metadata in headers, or make client do a second request for state.
            # For now, let's just send the audio. The client would need to manage state.
            # A better approach might be to return JSON with a link to the audio or base64 encoded audio.
            # Given the prompt implies returning the audio file directly:
            
            # It's tricky to send both a file and rich JSON data in a single standard HTTP response
            # without using multipart/form-data, which is usually for uploads, not responses.
            # A common pattern is to return JSON that *includes* the audio, perhaps base64 encoded,
            # or provides a URL to fetch the audio.
            # If we must return the file directly via send_file, metadata is limited.

            # Let's try to send the metadata as a JSON string in a custom header.
            # Client would need to parse this header.
            resp = send_file(temp_response_audio_path, as_attachment=True, download_name=f"response_{language}.mp3", mimetype="audio/mpeg")
            resp.headers["X-Chat-Metadata"] = json.dumps(response_metadata)
            
            return resp

        except Exception as e_speech:
            logger.error(f"Error during text-to-speech: {e_speech}", exc_info=True)
            # Fallback: return a JSON error if TTS fails
            return jsonify({"success": False, "error": f"Speech synthesis error: {e_speech}", "text_that_failed_tts": text_for_tts}), 500
        finally:
            # Clean up temporary response audio file and directory
            if os.path.exists(temp_response_audio_path):
                os.remove(temp_response_audio_path)
            if os.path.exists(temp_response_audio_dir):
                os.rmdir(temp_response_audio_dir)

    except Exception as e:
        logger.error(f"VASS chat endpoint error: {e}", exc_info=True)
        # Ensure any created temp dirs are cleaned up if an early exception occurs
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            os.rmdir(temp_dir)
        if 'temp_response_audio_dir' in locals() and os.path.exists(temp_response_audio_dir):
            if 'temp_response_audio_path' in locals() and os.path.exists(temp_response_audio_path):
                os.remove(temp_response_audio_path)
            os.rmdir(temp_response_audio_dir)
            
        return jsonify({'success': False, 'error': f'Unexpected server error in VASS: {str(e)}'}), 500

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
