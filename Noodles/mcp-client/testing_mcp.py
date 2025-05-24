# flask_mcp_chat_client.py

import flask
from flask import Flask, request, jsonify
import ollama # Make sure to install: pip install ollama
import subprocess
import json
import threading
import os
import sys
import time
import atexit

# --- Configuration for the MCP Server (from your prompt) ---
# IMPORTANT:
# 1. Adjust 'MCP_SERVER_COMMAND' if 'uv.exe' is not in your PATH or if you're on a different OS.
#    It might need to be the full path to 'uv.exe' or simply 'uv' if 'uv.exe' is a Windows-specific name
#    for a cross-platform tool and you're on Linux/macOS.
# 2. Ensure 'MCP_SERVER_SCRIPT_NAME' points to your actual MCP server Python file.
# 3. The 'MCP_WORKING_DIRECTORY' must be the correct path where your MCP server script and its resources are located.

import sys
# Launch the MCP server as a stdio JSON-RPC process
MCP_SERVER_COMMAND = sys.executable  # Python interpreter
MCP_SERVER_ARGS_TEMPLATE = ["database.py"]  # Run the MCP server script directly
MCP_WORKING_DIRECTORY = "C:\\Users\\Noodl\\Projects\\Big_O\\Hackathon\\Sristi\\PROPER\\the_big_o\\Noodles\\database" # CWD for the subprocess

# --- Global variable for MCP process and request ID ---
mcp_process = None
mcp_request_id_counter = 0
mcp_stderr_thread = None

def get_next_request_id():
    global mcp_request_id_counter
    mcp_request_id_counter += 1
    return mcp_request_id_counter

def log_mcp_stderr(pipe):
    try:
        for line in iter(pipe.readline, ''):
            print(f"[MCP Server STDERR]: {line.strip()}", file=sys.stderr)
    except Exception as e:
        print(f"Error reading MCP stderr: {e}", file=sys.stderr)
    finally:
        if pipe:
            pipe.close()

def start_mcp_server():
    global mcp_process, mcp_stderr_thread
    if mcp_process and mcp_process.poll() is None:
        print("MCP server check: Already running.", file=sys.stderr)
        return

    print(f"Starting MCP server with command: {MCP_SERVER_COMMAND} {' '.join(MCP_SERVER_ARGS_TEMPLATE)}", file=sys.stderr)
    print(f"Working directory for MCP server: {MCP_WORKING_DIRECTORY}", file=sys.stderr)

    try:
        mcp_process = subprocess.Popen(
            [MCP_SERVER_COMMAND] + MCP_SERVER_ARGS_TEMPLATE,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=MCP_WORKING_DIRECTORY,
            bufsize=1  # Line-buffered
        )
        print(f"MCP server started. PID: {mcp_process.pid}", file=sys.stderr)

        # Thread to print MCP server's stderr for debugging
        mcp_stderr_thread = threading.Thread(target=log_mcp_stderr, args=(mcp_process.stderr,))
        mcp_stderr_thread.daemon = True
        mcp_stderr_thread.start()

        time.sleep(3) # Give server a moment to initialize.
                      # Monitor stderr output for "MCP server started." and "Starting MCP server via Uvicorn."
                      # (as per your server script's output) to confirm readiness.

        if mcp_process.poll() is not None:
            raise Exception(f"MCP Server failed to start or terminated prematurely. Exit code: {mcp_process.returncode}")
        print("MCP Server appears to be running.", file=sys.stderr)

    except FileNotFoundError:
        error_msg = (f"Error: The command '{MCP_SERVER_COMMAND}' was not found. "
                     "Please ensure it's in your system PATH or provide the full and correct path.")
        print(error_msg, file=sys.stderr)
        mcp_process = None
        raise Exception(error_msg)
    except Exception as e:
        print(f"Failed to start MCP server: {e}", file=sys.stderr)
        if mcp_process and hasattr(mcp_process, 'stderr') and mcp_process.stderr:
            # Attempt to read any immediate stderr output
            try:
                remaining_stderr = mcp_process.stderr.read()
                if remaining_stderr:
                    print(f"MCP Server STDERR at failure: {remaining_stderr}", file=sys.stderr)
            except Exception as e_stderr:
                 print(f"Could not read MCP stderr during failure: {e_stderr}", file=sys.stderr)
        mcp_process = None
        raise

def stop_mcp_server():
    global mcp_process, mcp_stderr_thread
    if mcp_process and mcp_process.poll() is None:
        print("Stopping MCP server...", file=sys.stderr)
        mcp_process.terminate()
        try:
            mcp_process.wait(timeout=5)
            print("MCP server terminated.", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print("MCP server did not terminate gracefully, killing.", file=sys.stderr)
            mcp_process.kill()
            print("MCP server killed.", file=sys.stderr)
    if mcp_stderr_thread and mcp_stderr_thread.is_alive():
        print("Waiting for MCP stderr thread to finish...", file=sys.stderr)
        # Stderr pipe will be closed when process terminates, thread should exit.
        mcp_stderr_thread.join(timeout=2)
    mcp_process = None

def send_mcp_request(method_name, params):
    global mcp_process
    if not mcp_process or mcp_process.poll() is not None:
        print("MCP server not running. Attempting to restart...", file=sys.stderr)
        try:
            start_mcp_server()
        except Exception as e:
            return {"error": f"MCP server could not be (re)started: {str(e)}"}

    request_id = get_next_request_id()
    rpc_request = {
        "jsonrpc": "2.0",
        "method": method_name,
        "params": params,
        "id": request_id
    }

    try:
        print(f"Sending to MCP stdin: {json.dumps(rpc_request)}", file=sys.stderr)
        mcp_process.stdin.write(json.dumps(rpc_request) + '\n')
        mcp_process.stdin.flush()
        
        # Read response from MCP server's stdout with timeout using threading
        response_str = None
        response_ready = threading.Event()
        exception_caught = [None]  # Use list to store exception from thread
        
        def read_response():
            try:
                nonlocal response_str
                response_str = mcp_process.stdout.readline()
                response_ready.set()
            except Exception as e:
                exception_caught[0] = e
                response_ready.set()
        
        # Start thread to read response
        read_thread = threading.Thread(target=read_response)
        read_thread.daemon = True
        read_thread.start()
        
        # Wait up to 10 seconds for response
        timeout = 10
        if not response_ready.wait(timeout):
            return {"error": f"Timeout waiting for MCP server response after {timeout} seconds"}
        
        # Check if thread encountered an exception
        if exception_caught[0]:
            raise exception_caught[0]
        
        # Check if process is still alive
        if mcp_process.poll() is not None:
            return {"error": f"MCP Server terminated unexpectedly. Exit code: {mcp_process.poll()}"}
        
        if not response_str or not response_str.strip():
            return {"error": "No response from MCP server (empty line)."}

        print(f"Received from MCP stdout: {response_str.strip()}", file=sys.stderr)
        response_json = json.loads(response_str)

        if response_json.get("id") != request_id:
            return {"error": f"MCP response ID mismatch. Expected {request_id}, got {response_json.get('id')}"}
        if "error" in response_json: # JSON-RPC error object
            return {"error": f"MCP Error: {response_json['error'].get('message', response_json['error'])}", "mcp_error_details": response_json['error']}
        return response_json.get("result")

    except BrokenPipeError:
        print("Broken pipe: MCP server may have crashed or closed stdin/stdout.", file=sys.stderr)
        mcp_process = None # Mark as dead
        return {"error": "Broken pipe communication with MCP server."}
    except Exception as e:
        print(f"Error communicating with MCP server: {e}", file=sys.stderr)
        return {"error": f"Generic communication error with MCP server: {str(e)}"}

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat_handler():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "JSON payload must include a 'message' field"}), 400

    user_message = data['message']
    ollama_model = data.get('model', 'llama3.1:latest') # Default to 'llama3.1:latest'

    # 1. Interact with Ollama
    try:
        print(f"Sending to Ollama: model='{ollama_model}', message='{user_message}'", file=sys.stderr)
        ollama_client = ollama.Client() # Assumes Ollama is running at http://localhost:11434
        ollama_resp = ollama_client.chat(
            model=ollama_model,
            messages=[{'role': 'user', 'content': user_message}]
        )
        ollama_content = ollama_resp['message']['content']
        print(f"Received from Ollama: {ollama_content[:100]}...", file=sys.stderr)
    except Exception as e:
        error_message = f"Ollama interaction failed: {str(e)}. Ensure Ollama is running and the model '{ollama_model}' is available."
        print(error_message, file=sys.stderr)
        return jsonify({"error": error_message}), 500

    # 2. Interact with MCP Server if specified
    mcp_method_name = data.get('mcp_method')
    mcp_params = data.get('mcp_params', {})

    if mcp_method_name:
        mcp_server_response = send_mcp_request(mcp_method_name, mcp_params)
    else:
        mcp_server_response = None

    if mcp_server_response and isinstance(mcp_server_response, dict) and "error" in mcp_server_response:
        return jsonify({
            "warning": "Partial success: Ollama responded but MCP server interaction failed.",
            "ollama_response": ollama_content,
            "mcp_error": mcp_server_response["error"],
            "mcp_error_details": mcp_server_response.get("mcp_error_details")
        }), 200 # Or 500 if MCP failure is critical

    return jsonify({
        "user_message": user_message,
        "ollama_response": ollama_content,
        "mcp_server_response": mcp_server_response
    })

# --- Main execution ---
if __name__ == '__main__':
    print("--- Flask MCP/Ollama Chat Client ---", file=sys.stderr)
    print("Prerequisites:", file=sys.stderr)
    print("1. Ollama server must be running (e.g., `ollama serve`).", file=sys.stderr)
    print("   Ensure the model (default 'llama3') is downloaded: `ollama pull llama3`", file=sys.stderr)
    print("2. Your MCP server script (e.g., database.py from the prompt) must be correctly configured above.", file=sys.stderr)
    print("   It should expose a method callable via JSON-RPC (e.g., 'log_ollama_interaction').", file=sys.stderr)
    print("3. Python libraries needed: `pip install flask ollama`", file=sys.stderr)
    print("------------------------------------", file=sys.stderr)

    # Attempt to start the MCP server when the Flask app starts.
    try:
        start_mcp_server()
    except Exception as e:
        print(f"CRITICAL: Could not start MCP server on Flask app startup: {e}", file=sys.stderr)
        print("The /chat endpoint will likely fail to communicate with the MCP server.", file=sys.stderr)
        # You might want to exit here if MCP server is essential for Flask app to run
        # sys.exit(1)

    # Register a cleanup function to stop MCP server when Flask app exits
    atexit.register(stop_mcp_server)

    # Run Flask app
    flask_host = '127.0.0.1'
    flask_port = 5001 # Ensure this port is free
    print(f"Starting Flask client on http://{flask_host}:{flask_port}", file=sys.stderr)
    try:
        app.run(host=flask_host, port=flask_port, debug=True) # debug=False for production
    except Exception as e:
        print(f"Failed to start Flask app: {e}", file=sys.stderr)
    finally:
        # Ensure MCP server is stopped if Flask app crashes/stops unexpectedly
        # and atexit didn't run (e.g. forceful kill of Flask)
        # This final stop is a best-effort for cleanup.
        if mcp_process and mcp_process.poll() is None:
            print("Flask app is shutting down, ensuring MCP server is stopped...", file=sys.stderr)
            stop_mcp_server()