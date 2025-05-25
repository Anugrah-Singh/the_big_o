from flask import Flask, request, jsonify
import google.generativeai as genai
import json
import os # For API Key management
import requests # Added for making HTTP requests

app = Flask(__name__)

# Define the base URL for the external service
# Replace this with the actual URL you want to send the command to
EXTERNAL_SERVICE_BASE_URL = os.environ.get("EXTERNAL_SERVICE_BASE_URL", "http://192.168.28.205:5000/chat")
if EXTERNAL_SERVICE_BASE_URL == "YOUR_EXTERNAL_SERVICE_URL_HERE":
    print("WARNING: EXTERNAL_SERVICE_BASE_URL is not set. Please set it as an environment variable or directly in the code.")


# --- Google Gemini API Configuration ---
# IMPORTANT: Replace with your actual API key or use environment variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyB_BJayIXwmUF_BDlk6cUjkqLn2cKtPngY") 
if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    print("WARNING: GEMINI_API_KEY is not set. Please set it as an environment variable or directly in the code.")
    # Potentially raise an error or exit if the key is critical and not found
    # For now, we'll let it proceed, but LLM calls will fail.

if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Initialize the Gemini Pro model
        specialty_model = genai.GenerativeModel('gemini-1.5-flash') # Or your preferred model
        print("Gemini model for specialty matching initialized successfully.")
    except Exception as e:
        print(f"Error initializing Gemini model: {e}")
        specialty_model = None
else:
    specialty_model = None
    print("Gemini model not initialized due to missing API key.")


def determine_specialty_with_llm(patient_details):
    """
    Determines the required medical specialty based on patient details using an LLM.
    """
    if not specialty_model:
        print("Error: Specialty matching LLM not initialized.")
        return "general physician" # Fallback

    symptoms_list = patient_details.get("symptoms", [])
    if isinstance(symptoms_list, str): # If symptoms are a single string
        symptoms_description = symptoms_list
    elif isinstance(symptoms_list, list): # If symptoms are a list of strings
        symptoms_description = ", ".join(symptoms_list)
    else:
        symptoms_description = "Not specified"

    # For more context, you could include other patient_details fields
    # patient_info_str = json.dumps(patient_details, indent=2)

    prompt = f"""
You are an expert medical system. Based on the following patient symptoms, please identify the most appropriate medical specialty.
Return ONLY the name of the specialty in lowercase (e.g., "dermatologist", "cardiologist", "general physician"). Do not add any other text or punctuation.

Patient Symptoms: {symptoms_description}

Consider these common specialties:
- dermatologist
- cardiologist
- orthopedist
- pediatrician
- ophthalmologist
- gastroenterologist
- neurologist
- nephrologist
- urologist
- pulmonologist
- endocrinologist
- oncologist
- psychiatrist
- ENT specialist (otolaryngologist)
- rheumatologist
- allergist/immunologist
- general physician

If the symptoms are very general, or if you are unsure, suggest "general physician".

Specialty:
"""

    try:
        response = specialty_model.generate_content(prompt)
        # Ensure response.text is accessed correctly
        if hasattr(response, 'text') and response.text:
            suggested_specialty = response.text.strip().lower()
            # Basic validation: check if it's a single word or common phrase
            if " " in suggested_specialty and "specialist" not in suggested_specialty and "physician" not in suggested_specialty:
                 # If LLM returns a phrase not expected, fallback or take first word
                 print(f"LLM returned a phrase: '{suggested_specialty}'. Using first part or fallback.")
                 suggested_specialty = suggested_specialty.split()[0] # Simplistic, might need refinement
            
            # Further clean up if LLM adds quotes or other minor artifacts
            suggested_specialty = suggested_specialty.replace('"', '').replace("'", "").replace('.', '')

            print(f"LLM suggested specialty: {suggested_specialty}")
            return suggested_specialty if suggested_specialty else "general physician"
        elif response.parts: # Handle cases where response might be in parts
            full_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            suggested_specialty = full_text.strip().lower().replace('"', '').replace("'", "").replace('.', '')
            print(f"LLM suggested specialty (from parts): {suggested_specialty}")
            return suggested_specialty if suggested_specialty else "general physician"
        else:
            print(f"LLM response did not contain text. Response: {response}")
            return "general physician" # Fallback
    except Exception as e:
        print(f"Error calling Gemini API for specialty matching: {e}")
        return "general physician" # Fallback

@app.route('/find_doctor_and_slots', methods=['POST']) # Renamed endpoint for clarity
def find_doctor_and_slots():
    try:
        patient_details = request.get_json()

        if not patient_details:
            return jsonify({"success": False, "error": "No JSON data provided."}), 400

        if EXTERNAL_SERVICE_BASE_URL == "YOUR_EXTERNAL_SERVICE_URL_HERE":
            return jsonify({"success": False, "error": "External service URL is not configured."}), 500

        # Step 1: Determine the specialty using LLM
        specialty = determine_specialty_with_llm(patient_details)
        if not specialty: # Should ideally not happen due to fallback in determine_specialty_with_llm
            return jsonify({"success": False, "error": "Could not determine specialty."}), 500

        # Step 2: Create the natural language command
        command = f"fetch all the {specialty}s available for the next week with the time slots"
        print(f"Generated command: {command}")

        # Step 3: Make an HTTP POST request to the external service
        try:
            print(f"Sending command to: {EXTERNAL_SERVICE_BASE_URL}")
            # Assuming the external service expects a JSON payload with a 'command' field
            external_response = requests.post(EXTERNAL_SERVICE_BASE_URL, json={"message": command}, timeout=10) # Added timeout
            external_response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            
            # Step 4: Return the response from the external service to the frontend
            # We assume the external service returns JSON
            response_data_from_external = external_response.json()
            print(f"Received response from external service: {response_data_from_external}")
            
            return jsonify({
                "success": True, 
                "determined_specialty": specialty,
                "sent_command": command,
                "availability_info": response_data_from_external # This is the actual response from the external URL
            })

        except requests.exceptions.RequestException as e:
            print(f"Error calling external service: {e}")
            return jsonify({
                "success": False, 
                "error": f"Failed to communicate with the doctor availability service: {str(e)}",
                "determined_specialty": specialty,
                "sent_command": command
            }), 503 # Service Unavailable
        except json.JSONDecodeError:
            print("Error decoding JSON response from external service.")
            return jsonify({
                "success": False,
                "error": "Received an invalid response format from the doctor availability service.",
                "determined_specialty": specialty,
                "sent_command": command
            }), 502 # Bad Gateway


    except Exception as e:
        print(f"Error in /find_doctor_and_slots endpoint: {e}")
        return jsonify({"success": False, "error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    # It's good practice to run on a different port if you have multiple Flask apps
    # or to make it configurable, e.g., via environment variables.
    app.run(debug=True, port=5002, host='0.0.0.0')