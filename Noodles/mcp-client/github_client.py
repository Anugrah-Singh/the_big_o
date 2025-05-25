import subprocess
import json
import ollama
import time
import threading

MCP_CONFIG = {
    "mcpServers": {
        "database": {
            "command": "C:\\Users\\Noodl\\Projects\\.venv\\Scripts\\uv.exe",
            "args": [
                "--directory",
                "C:\\Users\\Noodl\\Projects\\Big_O\\Hackathon\\Sristi\\PROPER\\the_big_o\\Noodles\\database",
                "run",
                "database.py"
            ]
        }
    }
}

def run_mcp_command(requests, max_lines=200, timeout=15):
    cmd = [MCP_CONFIG["mcpServers"]["database"]["command"]] + MCP_CONFIG["mcpServers"]["database"]["args"]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    # Give the server a second to start up (tune as needed)
    time.sleep(1.0)
    for req in requests:
        proc.stdin.write(json.dumps(req) + "\n")
        proc.stdin.flush()
        time.sleep(0.1)

    responses = []
    start_time = time.time()
    read_lines = 0
    while read_lines < max_lines and (time.time() - start_time) < timeout:
        line = proc.stdout.readline()
        if not line:
            break
        read_lines += 1
        line = line.strip()
        if not line:
            continue
        try:
            resp = json.loads(line)
            responses.append(resp)
        except Exception:
            print(f"SERVER LOG: {line}")  # Print any non-JSON output for debugging
            continue
        # If you get a result or error, you can break early (optional)
        if any([
            resp.get("id") == req.get("id") and ("result" in resp or "error" in resp)
            for req in requests
        ]):
            break

    proc.stdin.close()
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except Exception:
        proc.kill()
    return responses

def get_mcp_tools():
    initialize_req = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "1.0",
            "capabilities": {},
            "clientInfo": {
                "name": "noodles-mcp-client",
                "version": "0.1"
            }
        },
        "id": 1
    }
    tools_list_req = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }
    responses = run_mcp_command([initialize_req, tools_list_req])
    for resp in responses:
        if resp.get("id") == 2 and "result" in resp:
            return resp["result"]
    raise RuntimeError("Could not discover MCP tools")

def format_tools_for_prompt(tools_info):
    lines = []
    for tool in tools_info:
        name = tool.get("name", "")
        doc = tool.get("doc", "").strip()
        params = tool.get("params", [])
        returns = tool.get("returns", {})
        param_descs = []
        for p in params:
            desc = f'{p["name"]} ({p["annotation"]})'
            if p.get("doc"):
                desc += f": {p['doc']}"
            param_descs.append(desc)
        params_section = "\n      ".join(param_descs) if param_descs else "None"
        returns_type = returns.get("annotation", "unknown")
        returns_doc = returns.get("doc", "")
        returns_str = f"{returns_type}: {returns_doc}" if returns_doc else returns_type
        lines.append(
            f"Function: {name}\n"
            f"  Description: {doc}\n"
            f"  Arguments:\n      {params_section}\n"
            f"  Output: {returns_str}\n"
        )
    return "\n".join(lines)

def call_ollama(prompt, model="llama3.1:latest"):
    response = ollama.generate(
        model=model,
        prompt=prompt
    )
    return response['response']

def call_database_tool(tool_name, args_dict):
    initialize_req = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "1.0",
            "capabilities": {},
            "clientInfo": {
                "name": "noodles-mcp-client",
                "version": "0.1"
            }
        },
        "id": 1
    }
    call_tool_req = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "tool": tool_name,
            "args": args_dict
        },
        "id": 2
    }
    responses = run_mcp_command([initialize_req, call_tool_req])
    for resp in responses:
        if resp.get("id") == 2 and ("result" in resp or "error" in resp):
            return resp
    return {"error": "No valid JSON-RPC response"}

def main():
    try:
        tools_info = get_mcp_tools()
    except Exception as e:
        print("Failed to discover MCP tools:", e)
        return
    tools_list = format_tools_for_prompt(tools_info)
    print("Welcome to the MCP+LLM Client (with dynamic tool context).")
    print("Enter your request in natural language. Type 'exit' to quit.")
    while True:
        user_input = input("Enter your request: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        llm_prompt = (
            "You are an AI agent that receives user instructions and must select the best available MCP tool, "
            "and generate a JSON object for a JSON-RPC request to run it. "
            "Here are the available MCP tools, with their descriptions, arguments, and output types:\n\n"
            f"{tools_list}\n"
            "Output ONLY a single JSON object of the form: "
            "{\"method\": \"tool_name\", \"params\": {param_dict}}\n"
            f"User input: {user_input}\n"
            "Output:"
        )
        llm_response = call_ollama(llm_prompt)
        print("LLM raw response:", llm_response)
        try:
            tool_cmd = json.loads(llm_response)
            method = tool_cmd.get("method")
            params = tool_cmd.get("params", {})
            if not method:
                print("LLM did not specify a method/tool. Skipping.")
                continue
            result = call_database_tool(method, params)
            print("MCP tool result:", json.dumps(result, indent=2))
        except Exception as e:
            print("Failed to interpret LLM response or invoke MCP tool:", e)

if __name__ == "__main__":
    main()