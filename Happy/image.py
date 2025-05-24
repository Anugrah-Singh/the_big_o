import dwani
import os
from flask import Flask, request, jsonify
import uuid  # For generating unique temporary filenames
from flask_cors import CORS  # For handling CORS if needed

DWANI_API_KEY = 'abhishekr.23.becs@acharya.ac.in_dwani_krishnadevaraya'
DWANI_API_BASE = 'https://dwani-dwani-api.hf.space'

# Configure Dwani API
dwani.api_key = DWANI_API_KEY
dwani.api_base = DWANI_API_BASE

app = Flask(__name__)
CORS(app)  # Enable CORS if your frontend is hosted on a different domain

@app.route('/generate-captions', methods=['POST'])
def generate_captions():
    if 'images' not in request.files:
        return jsonify({"error": "No images part in the request"}), 400

    files = request.files.getlist('images')
    captions = []
    temp_files_to_delete = []

    if not files or all(file.filename == '' for file in files):
        return jsonify({"error": "No selected files"}), 400

    for file_storage in files:
        if file_storage:
            try:
                # Save the file temporarily
                temp_filename = str(uuid.uuid4()) + os.path.splitext(file_storage.filename)[1]
                temp_filepath = os.path.join('.', temp_filename)  # Save in current dir, or specify a temp dir
                file_storage.save(temp_filepath)
                temp_files_to_delete.append(temp_filepath)

                # Generate caption
                result = dwani.Vision.caption(
                    file_path=temp_filepath,
                    query="Describe this document",  # Generic query for captioning
                    src_lang="english"
                )

                # Assuming the result structure contains a 'caption' or similar key.
                # Adjust based on the actual structure of `result` from dwani.Vision.caption
                if result and isinstance(result, dict) and result.get('caption'):
                    captions.append(result['caption'])
                elif result and isinstance(result, dict) and result.get('description'):  # Fallback if 'caption' key doesn't exist
                    captions.append(result['description'])
                elif result and isinstance(result, dict) and result.get('answer'): # Fallback for 'answer' key
                    captions.append(result['answer'])
                elif result and isinstance(result, str):  # If the result itself is the caption string
                    captions.append(result)
                else:
                    # Log or handle cases where caption is not found or result format is unexpected
                    print(f"Warning: Could not extract caption for {file_storage.filename}. Result: {result}")
                    captions.append(f"Could not generate caption for {file_storage.filename}")

            except Exception as e:
                print(f"Error processing file {file_storage.filename}: {e}")
                captions.append(f"Error processing {file_storage.filename}: {str(e)}")
            finally:
                # Clean up temporary files
                for temp_file in temp_files_to_delete:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                temp_files_to_delete.clear()

    return jsonify({"captions": captions}), 200


if __name__ == '__main__':
    # Ensure the server runs on a port that's likely free, e.g., 5001
    # And accessible from network if needed (host='0.0.0.0')
    app.run(debug=True, port=5001, host = '0.0.0.0')