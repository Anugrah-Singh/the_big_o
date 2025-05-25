import dwani
import os
import requests

dwani.api_key = 'abhishekr.23.becs@acharya.ac.in_dwani_krishnadevaraya'
dwani.api_base = 'https://dwani-dwani-api.hf.space'

def run_asr():
    try:
        result = dwani.ASR.transcribe(file_path="kannada_sample.wav", language="kannada")
        print("ASR Response:", result)
    except Exception as e:
        print(f"Error in ASR module: {e}")

print("Running ASR...")
run_asr()
