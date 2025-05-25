#!/usr/bin/env python3
"""
Direct test of the MCP server without Flask
"""
import subprocess
import json
import sys
import os

# Path to the database directory
database_dir = r"C:\Users\Noodl\Projects\Big_O\Hackathon\Sristi\PROPER\the_big_o\Noodles\database"

def test_mcp_server():
    print("Starting MCP server for direct test...")
    
    # Start the MCP server
    process = subprocess.Popen(
        [sys.executable, "database.py"],
        cwd=database_dir,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0  # Unbuffered
    )
    
    try:
        # Test request
        request = {
            "jsonrpc": "2.0",
            "method": "create_patient", 
            "params": {
                "first_name": "Test",
                "last_name": "Patient",
                "age": 25
            },
            "id": 1
        }
        
        print(f"Sending: {json.dumps(request)}")
        
        # Send request
        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()
          # Read response with proper timeout using threading
        import threading
        import time
        
        response_received = threading.Event()
        response_data = {"data": None, "error": None}
        
        def read_response():
            try:
                response_line = process.stdout.readline()
                if response_line.strip():
                    print(f"Received: {response_line.strip()}")
                    try:
                        response_json = json.loads(response_line)
                        response_data["data"] = response_json
                        print(f"Parsed response: {json.dumps(response_json, indent=2)}")
                    except json.JSONDecodeError as e:
                        response_data["error"] = f"Failed to parse JSON: {e}"
                else:
                    response_data["error"] = "Empty response"
            except Exception as e:
                response_data["error"] = f"Error reading response: {e}"
            finally:
                response_received.set()
        
        # Start reading in a separate thread
        read_thread = threading.Thread(target=read_response)
        read_thread.daemon = True
        read_thread.start()
        
        # Wait for response or timeout
        timeout = 5
        print(f"Waiting for response (timeout: {timeout}s)...")
        
        if response_received.wait(timeout):
            if response_data["data"]:
                return True
            else:
                print(f"Error: {response_data['error']}")
                return False
        else:
            print(f"TIMEOUT: No response received within {timeout} seconds")
            
            # Check if process is still running
            if process.poll() is None:
                print("Process is still running, attempting to read stderr...")
                try:
                    stderr_output = process.stderr.read()
                    if stderr_output:
                        print(f"STDERR: {stderr_output}")
                except:
                    pass
            else:
                print(f"Process exited with code: {process.returncode}")
            
            return False
        
    finally:
        # Clean up
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=2)
        if process.poll() is None:
            process.kill()

if __name__ == "__main__":
    success = test_mcp_server()
    print(f"Test {'PASSED' if success else 'FAILED'}")
