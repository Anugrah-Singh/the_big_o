import dwani
import requests

DWANI_API_KEY = 'abhishekr.23.becs@acharya.ac.in_dwani_krishnadevaraya'
DWANI_API_BASE = 'https://dwani-dwani-api.hf.space'

# Configure Dwani API
dwani.api_key = DWANI_API_KEY
dwani.api_base = DWANI_API_BASE
def run_asr():
    try:
        result = dwani.ASR.transcribe(file_path="kann.wav", language="kannada")
        print("ASR Response:", result)
    except Exception as e:
        print(f"Error in ASR module: {e}")


run_asr()