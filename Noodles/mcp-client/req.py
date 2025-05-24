import requests
import json

url = "http://127.0.0.1:5001/chat"
payload = {
    "message": "create a new patient with name 'Doe John' and age 30",
    "model": "llama3.1:latest", # Optional, defaults to llama3
    "mcp_method": "create_patient",
    "mcp_params": {
        "first_name": "Doe",
        "last_name": "John", 
        "age": 30
    }
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, data=json.dumps(payload), headers=headers)

if response.status_code == 200:
    print("Success:")
    print(json.dumps(response.json(), indent=2))
else:
    print(f"Error: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print(response.text)