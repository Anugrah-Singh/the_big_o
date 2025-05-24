# Medical Chatbot Setup Instructions

## Setting up Google Gemini API Key

To use the medical chatbot with Google Gemini 1.5-flash for template updating, you need to set up your Gemini API key.

### Step 1: Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Create a new API key or use an existing one

### Step 2: Set the Environment Variable

#### Option 1: Set in your terminal session (temporary)
```bash
export GEMINI_API_KEY="your_api_key_here"
```

#### Option 2: Add to your shell profile (permanent)
Add the following line to your `~/.zshrc` or `~/.bash_profile`:
```bash
export GEMINI_API_KEY="your_api_key_here"
```

Then reload your shell:
```bash
source ~/.zshrc
```

#### Option 3: Create a .env file (if using python-dotenv)
Create a `.env` file in the project directory:
```
GEMINI_API_KEY=your_api_key_here
```

### Step 3: Run the Server

```bash
python chat.py
```

The server will start on port 6969 and will use:
- **Google Gemini 1.5-flash** for template updating (first LLM instance)
- **Dwani API** for completeness checking (second LLM instance)

### Testing the Chatbot

```bash
# Test the chatbot functionality
python test_chatbot.py

# Run the example conversation
python chatbot_example.py
```

### API Endpoints

- `GET /health` - Health check
- `GET /start` - Start new chat session
- `POST /chat` - Process user answer and update template

### Example Usage

```python
import requests

# Start chat
response = requests.get("http://localhost:6969/start")
data = response.json()

# Send user answer
chat_data = {
    "template": data["template"],
    "answer": "My name is John Doe"
}
response = requests.post("http://localhost:6969/chat", json=chat_data)
result = response.json()
```

### Error Handling

If you see "GEMINI_API_KEY not found in environment variables" in the logs, make sure you've set the environment variable correctly and restarted the server.
