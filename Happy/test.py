import dwani
import os
import requests

dwani.api_key = 'abhishekr.23.becs@acharya.ac.in_dwani_krishnadevaraya'
dwani.api_base = 'https://dwani-dwani-api.hf.space'


def run_chat():
    try:
        resp = dwani.Chat.create(prompt="Hello!", src_lang="english", tgt_lang="kannada")
        print("Chat Response:", resp)
    except Exception as e:
        print(f"Error in Chat module: {e}")

def make_post_request():
    url = "https://sanky02.app.n8n.cloud/webhook-test/14530249-7a62-4625-926e-8961d6884924"
    data = {"message": "Hello from Python!"}
    try:
        response = requests.post(url, json=data)
        print("POST Response:", response.text)
    except Exception as e:
        print(f"Error in POST request: {e}")

make_post_request()