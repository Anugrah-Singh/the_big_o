import gradio as gr
import requests
import json
import tempfile
import os

# Configuration
# To allow Gradio to be accessible on the local network, set server_name to "0.0.0.0"
GRADIO_SERVER_NAME = "0.0.0.0"
GRADIO_SERVER_PORT = 7860
VASS_API_URL = "http://127.0.0.1:6969/vass"  # Ensure chat.py Flask server is running here

INITIAL_HISTORY_STATE = []  # Start with an empty conversation history
INITIAL_TEMPLATE_STATE = {} # Start with an empty template; backend will initialize

def process_voice_chat_for_gradio(mic_audio_path, language, current_history_state, current_template_state):
    """
    Handles the interaction with the VASS backend.
    Takes audio input, language, and current conversation state.
    Returns paths to response audio, text spoken, final summary, and updated states.
    """
    if mic_audio_path is None:
        return None, "Please record your voice first.", None, current_history_state, current_template_state

    files = {'file': open(mic_audio_path, 'rb')}
    data = {
        'language': language,
        'conversation_history': json.dumps(current_history_state),
        'template': json.dumps(current_template_state)
    }

    response_audio_path_to_return = None
    bot_text_to_return = "Error: Could not process the request."
    final_summary_to_return = None
    next_history_state = current_history_state
    next_template_state = current_template_state

    try:
        print(f"Sending to VASS API: lang={language}, history_len={len(current_history_state)}, template_keys={list(current_template_state.keys()) if current_template_state else 'None'}")
        
        response = requests.post(VASS_API_URL, files=files, data=data, timeout=120) # 2-minute timeout
        
        print(f"VASS API Response Status: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}")

        if response.status_code == 200 and response.headers.get('Content-Type') == 'audio/mpeg':
            # Successful audio response
            temp_dir_resp = tempfile.mkdtemp()
            response_audio_path_to_return = os.path.join(temp_dir_resp, "response.mp3")
            with open(response_audio_path_to_return, "wb") as f:
                f.write(response.content)
            print(f"Response audio saved to: {response_audio_path_to_return}")

            metadata_header = response.headers.get("X-Chat-Metadata")
            if metadata_header:
                print(f"Metadata header (snippet): {metadata_header[:200]}...")
                metadata = json.loads(metadata_header)
                next_history_state = metadata.get("conversation_history", current_history_state)
                next_template_state = metadata.get("updated_template", current_template_state)
                bot_text_to_return = metadata.get("text_spoken", "Audio response received.")
                final_summary_to_return = metadata.get("final_summary")
                print(f"Received from metadata: bot_text='{bot_text_to_return}', summary_present={final_summary_to_return is not None}, new_history_len={len(next_history_state)}")
            else:
                bot_text_to_return = "Audio received, but metadata is missing from the server."
                print(bot_text_to_return)
        
        elif response.status_code != 200:
            # Handle HTTP errors (non-200 status)
            error_message = f"API Error (Status {response.status_code}): "
            try:
                error_json = response.json()
                error_message += error_json.get('error', response.text)
            except ValueError: # If response is not JSON
                error_message += response.text[:200] # Show a snippet
            bot_text_to_return = error_message
            print(bot_text_to_return)
            # No audio expected on server error
            response_audio_path_to_return = None

        else: # Status 200 but not audio/mpeg
            bot_text_to_return = f"Error: Unexpected response format from server (Status 200, Content-Type: {response.headers.get('Content-Type')}). Expected audio/mpeg."
            print(bot_text_to_return)
            response_audio_path_to_return = None


    except requests.exceptions.Timeout:
        bot_text_to_return = f"Error: The request to the VASS API at {VASS_API_URL} timed out."
        print(bot_text_to_return)
    except requests.exceptions.ConnectionError:
        bot_text_to_return = f"Error: Could not connect to the VASS API at {VASS_API_URL}. Ensure the backend Flask server (chat.py) is running."
        print(bot_text_to_return)
    except requests.exceptions.RequestException as e: # Catch other request-related errors
        bot_text_to_return = f"API Request Error: {str(e)}"
        print(bot_text_to_return)
    except json.JSONDecodeError as e:
        # This would be if metadata_header itself is malformed JSON
        bot_text_to_return = f"Error: Could not parse metadata from server: {str(e)}. Header (snippet): {metadata_header[:200] if 'metadata_header' in locals() else 'N/A'}"
        print(bot_text_to_return)
        # Audio might have been received if this error is specific to metadata parsing
    except Exception as e:
        bot_text_to_return = f"An unexpected error occurred in Gradio app: {str(e)}"
        print(bot_text_to_return)
        # Ensure audio path is None if a severe error occurs before/during audio handling
        if response_audio_path_to_return and not os.path.exists(response_audio_path_to_return):
             response_audio_path_to_return = None
    finally:
        if 'files' in locals() and files.get('file'):
            files['file'].close()
        # Gradio handles cleanup of its input temp files (mic_audio_path).
        # Response audio files (response_audio_path_to_return) are in system temp dirs.
        # Gradio's Audio output component will use this path. For long-running apps,
        # these temp response audio files might accumulate if not explicitly managed,
        # but for typical Gradio usage, system temp cleanup or app restart handles it.

    return response_audio_path_to_return, bot_text_to_return, final_summary_to_return, next_history_state, next_template_state

# Gradio Interface
with gr.Blocks(title="Medical Voice Assistant", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🩺 Medical Voice Assistant
        Record your medical query in the selected language. 
        The assistant will respond in voice and update the medical report below.
        *Note:* Ensure the backend Flask server (chat.py) is running.
        """
    )

    with gr.Row():
        mic_input = gr.Audio(sources=["microphone"], type="filepath", label="Your Voice Input 🎤")
        language_input = gr.Dropdown(
            choices=["english", "kannada", "hindi", "tamil", "telugu", "malayalam", "bengali", "marathi", "gujarati", "punjabi"],
            value="english",
            label="Language of Interaction 🌐"
        )
    
    submit_button = gr.Button("Send to Assistant 🚀", variant="primary")

    with gr.Accordion("Assistant's Response", open=True):
        with gr.Row():
            response_audio_output = gr.Audio(label="Voice Response 🔊", type="filepath", autoplay=True)
        response_text_output = gr.Textbox(label="Assistant Says 💬", lines=3, interactive=False)

    gr.Markdown("---")
    final_report_output = gr.Json(label="Final Medical Report 📄")

    # State variables to maintain conversation context across interactions
    chat_history_state = gr.State(value=INITIAL_HISTORY_STATE)
    current_template_state = gr.State(value=INITIAL_TEMPLATE_STATE)

    submit_button.click(
        fn=process_voice_chat_for_gradio,
        inputs=[mic_input, language_input, chat_history_state, current_template_state],
        outputs=[response_audio_output, response_text_output, final_report_output, chat_history_state, current_template_state],
        api_name="voice_chat" # For API access if needed
    )
    
    gr.Examples(
        examples=[
            ["english"], # Example with language, mic input will be None initially
            ["kannada"],
        ],
        inputs=[language_input], # Only provide example for language dropdown
        label="Example Languages (record audio after selecting)"
    )

if __name__ == "__main__":
    print("Starting Gradio Voice Assistant...")
    print(f"Please ensure the backend Flask server (chat.py) is running and accessible at {VASS_API_URL}")
    demo.launch(share=True, server_name=GRADIO_SERVER_NAME, server_port=GRADIO_SERVER_PORT, debug=True)