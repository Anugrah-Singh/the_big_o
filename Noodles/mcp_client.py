import subprocess
import sys
import os
import json
import time
import datetime # For handling date/time strings for some methods

def start_mcp_server(command, args, directory):
    """
    Starts the MCP server process with the specified command, arguments, and working directory.
    """
    full_command = [command] + args
    print(f"Starting MCP server with command: {' '.join(full_command)} in directory: {directory}", file=sys.stderr)

    try:
        # Use Popen to control stdin and stdout of the subprocess
        process = subprocess.Popen(
            full_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Handle as text (UTF-8 by default)
            bufsize=1,  # Line-buffered for stdout/stderr
            cwd=directory, # Set the working directory for the subprocess
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0 # Optional: open new console on Windows
        )
        # Give the server a moment to start up and print its initial messages
        # You might need to adjust this delay based on how long your DB connection takes
        time.sleep(3)
        return process
    except FileNotFoundError:
        print(f"Error: Command '{command}' not found. Make sure 'uv.exe' is in your PATH or the full path is correct.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error starting MCP server process: {e}", file=sys.stderr)
        return None

def send_json_rpc_request(process, method, params, request_id):
    """
    Constructs and sends a JSON-RPC request to the server, then waits for a response.
    """
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params
    }
    
    json_request = json.dumps(request)
    # print(f"CLIENT SENDING ({method}): {json_request}", file=sys.stderr) # Uncomment for verbose client sending

    try:
        process.stdin.write(json_request + '\n')
        process.stdin.flush()

        # Read the response line by line, allowing for potential delays
        response_line = ""
        start_time = time.time()
        timeout = 15 # Increased timeout for database operations
        while not response_line and (time.time() - start_time) < timeout:
            response_line = process.stdout.readline().strip()
            if not response_line:
                time.sleep(0.05) # Small delay to prevent busy-waiting
        
        if not response_line:
            print(f"Error: No response received from server for '{method}' within {timeout} seconds.", file=sys.stderr)
            return {"jsonrpc": "2.0", "error": {"code": -32001, "message": "Client timeout"}}

        # print(f"CLIENT RECEIVED RAW: {response_line}", file=sys.stderr) # Uncomment for verbose raw response

        try:
            response_obj = json.loads(response_line)
            return response_obj
        except json.JSONDecodeError as e:
            print(f"JSON decoding error for '{method}': {e} from line: '{response_line}'", file=sys.stderr)
            return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error", "data": str(e)}}
    except BrokenPipeError:
        print("Error: Server pipe broken. Server might have terminated unexpectedly.", file=sys.stderr)
        return {"jsonrpc": "2.0", "error": {"code": -32002, "message": "Server pipe broken"}}
    except Exception as e:
        print(f"Error during communication for '{method}': {e}", file=sys.stderr)
        return {"jsonrpc": "2.0", "error": {"code": -32003, "message": f"Client communication error: {e}"}}

def read_server_stderr(process):
    """Reads and prints any output from the server's stderr."""
    while True:
        line = process.stderr.readline()
        if not line: # EOF or pipe closed
            break
        print(f"SERVER STDERR: {line.strip()}", file=sys.stderr)

if __name__ == "__main__":
    # --- Configuration from your Claude Desktop setup ---
    UV_EXECUTABLE = "C:\\Users\\Noodl\\Projects\\.venv\\Scripts\\uv.exe"
    MCP_SERVER_DIRECTORY = "C:\\Users\\Noodl\\Projects\\Big_O\\Hackathon\\Sristi\\PROPER\\the_big_o\\Noodles\\database"
    # Ensure database.py is directly in this directory
    MCP_SERVER_ARGS = [
        "--directory", MCP_SERVER_DIRECTORY,
        "run",
        "database.py" # The script that contains your FastMCP server
    ]
    # --- End Configuration ---

    print("Attempting to start MCP server process...", file=sys.stderr)
    server_process = start_mcp_server(UV_EXECUTABLE, MCP_SERVER_ARGS, MCP_SERVER_DIRECTORY)
    request_counter = 0 # To manage JSON-RPC request IDs

    if server_process:
        print("MCP server process started successfully.", file=sys.stderr)

        # Start a separate thread to continuously read server's stderr for debugging
        import threading
        stderr_thread = threading.Thread(target=read_server_stderr, args=(server_process,), daemon=True)
        stderr_thread.start()
        
        # --- Example Calls to your MCP Server Methods ---

        # 1. Test Connection
        request_counter += 1
        print(f"\n--- Calling test_connection (ID: {request_counter}) ---", file=sys.stderr)
        response = send_json_rpc_request(server_process, "test_connection", {}, request_counter)
        print(f"Response: {json.dumps(response, indent=2)}", file=sys.stderr)
        
        if response and "result" in response and response["result"].get("status") == "Connection successful":
            print("Database connection test PASSED.", file=sys.stderr)
        else:
            print("Database connection test FAILED.", file=sys.stderr)


        # 2. Create a Patient
        request_counter += 1
        print(f"\n--- Calling create_patient (ID: {request_counter}) ---", file=sys.stderr)
        patient_params = {
            "first_name": "John",
            "last_name": "Doe",
            "age": 35,
            "conversation_summary": "Initial consultation, patient concerned about general health."
        }
        response = send_json_rpc_request(server_process, "create_patient", patient_params, request_counter)
        print(f"Response: {json.dumps(response, indent=2)}", file=sys.stderr)
        patient_id = None
        if response and "result" in response and response["result"].get("patient_id"):
            patient_id = response["result"]["patient_id"]
            print(f"Created Patient with ID: {patient_id}", file=sys.stderr)
        else:
            print("Failed to create patient.", file=sys.stderr)

        # 3. Get Patient Detail (using the ID from creation)
        if patient_id:
            request_counter += 1
            print(f"\n--- Calling get_patient_detail (ID: {request_counter}) ---", file=sys.stderr)
            response = send_json_rpc_request(server_process, "get_patient_detail", {"patient_id": patient_id}, request_counter)
            print(f"Response: {json.dumps(response, indent=2)}", file=sys.stderr)

        # 4. Book an Appointment
        if patient_id:
            request_counter += 1
            print(f"\n--- Calling book_appointment (ID: {request_counter}) ---", file=sys.stderr)
            # Ensure the doctor_id exists in your DB, or adjust this.
            # Format date for MariaDB DATETIME column
            appointment_time = (datetime.datetime.now() + datetime.timedelta(days=7, hours=10)).strftime('%Y-%m-%d %H:%M:%S')
            appointment_params = {
                "patient_id": patient_id,
                "doctor_id": 1, # Assuming a doctor with ID 1 exists
                "appointment_date": appointment_time,
                "reason": "Routine check-up"
            }
            response = send_json_rpc_request(server_process, "book_appointment", appointment_params, request_counter)
            print(f"Response: {json.dumps(response, indent=2)}", file=sys.stderr)
            appointment_id = None
            if response and "result" in response and response["result"].get("appointment_id"):
                appointment_id = response["result"]["appointment_id"]
                print(f"Booked Appointment with ID: {appointment_id}", file=sys.stderr)


        # 5. Get Appointment Details
        if patient_id:
            request_counter += 1
            print(f"\n--- Calling get_appointment_detail (ID: {request_counter}) ---", file=sys.stderr)
            response = send_json_rpc_request(server_process, "get_appointment_detail", {"patient_id": patient_id}, request_counter)
            print(f"Response: {json.dumps(response, indent=2)}", file=sys.stderr)


        # 6. Update Appointment
        if appointment_id:
            request_counter += 1
            print(f"\n--- Calling update_appointment (ID: {request_counter}) ---", file=sys.stderr)
            updated_time = (datetime.datetime.now() + datetime.timedelta(days=14, hours=14)).strftime('%Y-%m-%d %H:%M:%S')
            update_appointment_params = {
                "appointment_id": appointment_id,
                "appointment_date": updated_time,
                "status": "rescheduled"
            }
            response = send_json_rpc_request(server_process, "update_appointment", update_appointment_params, request_counter)
            print(f"Response: {json.dumps(response, indent=2)}", file=sys.stderr)
        
        # 7. Create Medical History
        if patient_id:
            request_counter += 1
            print(f"\n--- Calling create_medical_history (ID: {request_counter}) ---", file=sys.stderr)
            medical_history_params = {
                "patient_id": patient_id,
                "allergies": "Pollen",
                "chronic_conditions": "Asthma",
                "current_medications": "Albuterol",
                "past_medical_history": "Childhood chickenpox"
            }
            response = send_json_rpc_request(server_process, "create_medical_history", medical_history_params, request_counter)
            print(f"Response: {json.dumps(response, indent=2)}", file=sys.stderr)

        # 8. Get Medical History
        if patient_id:
            request_counter += 1
            print(f"\n--- Calling get_medical_history (ID: {request_counter}) ---", file=sys.stderr)
            response = send_json_rpc_request(server_process, "get_medical_history", {"patient_id": patient_id}, request_counter)
            print(f"Response: {json.dumps(response, indent=2)}", file=sys.stderr)

        # 9. Update Medical History
        if patient_id:
            request_counter += 1
            print(f"\n--- Calling update_medical_history (ID: {request_counter}) ---", file=sys.stderr)
            update_history_params = {
                "patient_id": patient_id,
                "allergies": "Pollen, Dust",
                "current_medications": "Albuterol, Vitamin D"
            }
            response = send_json_rpc_request(server_process, "update_medical_history", update_history_params, request_counter)
            print(f"Response: {json.dumps(response, indent=2)}", file=sys.stderr)

        # 10. Create Bill
        if patient_id:
            request_counter += 1
            print(f"\n--- Calling create_bill (ID: {request_counter}) ---", file=sys.stderr)
            bill_params = {
                "patient_id": patient_id,
                "total_amount": 150.75,
                "particulars": "Consultation and tests"
            }
            response = send_json_rpc_request(server_process, "create_bill", bill_params, request_counter)
            print(f"Response: {json.dumps(response, indent=2)}", file=sys.stderr)
            bill_id = None
            if response and "result" in response and response["result"].get("bill_id"):
                bill_id = response["result"]["bill_id"]
                print(f"Created Bill with ID: {bill_id}", file=sys.stderr)
            else:
                print("Failed to create bill.", file=sys.stderr)

        # 11. Update Bill (to paid status)
        if bill_id:
            request_counter += 1
            print(f"\n--- Calling update_bill (ID: {request_counter}) ---", file=sys.stderr)
            paid_on_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            update_bill_params = {
                "bill_id": bill_id,
                "amount_paid": 150.75,
                "paid_on": paid_on_time,
                "status": "paid"
            }
            response = send_json_rpc_request(server_process, "update_bill", update_bill_params, request_counter)
            print(f"Response: {json.dumps(response, indent=2)}", file=sys.stderr)

        # 12. Delete Bill
        # Commenting out deletion for now to allow inspection of created data.
        # Uncomment if you want to test deletion.
        # if bill_id:
        #     request_counter += 1
        #     print(f"\n--- Calling delete_bill (ID: {request_counter}) ---", file=sys.stderr)
        #     response = send_json_rpc_request(server_process, "delete_bill", {"bill_id": bill_id}, request_counter)
        #     print(f"Response: {json.dumps(response, indent=2)}", file=sys.stderr)


        # --- Cleanup ---
        print("\nTerminating MCP server.", file=sys.stderr)
        try:
            # Send JSON-RPC shutdown and exit notifications
            shutdown_request = {"jsonrpc": "2.0", "id": request_counter + 1, "method": "shutdown", "params": {}}
            send_json_rpc_request(server_process, "shutdown", {}, request_counter + 1)
            
            exit_notification = {"jsonrpc": "2.0", "method": "exit", "params": {}}
            process.stdin.write(json.dumps(exit_notification) + '\n')
            process.stdin.flush()
            
            # Close client's stdin to server, signaling EOF
            server_process.stdin.close() 
            server_process.wait(timeout=5) # Wait for server to terminate

            if server_process.poll() is None:
                print("Server did not terminate gracefully within 5 seconds, killing it.", file=sys.stderr)
                server_process.kill()
        except Exception as e:
            print(f"Error during server shutdown: {e}", file=sys.stderr)

        # Read any remaining stdout/stderr from the server after it has closed
        stdout_output, stderr_output = server_process.communicate(timeout=5)
        if stdout_output:
            print("\nServer stdout (final):\n", stdout_output, file=sys.stderr)
        if stderr_output:
            print("\nServer stderr (final):\n", stderr_output, file=sys.stderr)
        
        print(f"MCP server process exited with code: {server_process.returncode}", file=sys.stderr)

    else:
        print("Failed to start MCP server process. Please check configuration and paths.", file=sys.stderr)