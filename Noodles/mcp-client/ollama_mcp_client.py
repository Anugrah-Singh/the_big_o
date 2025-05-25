import asyncio
import json
import ollama
from pydantic_ai.mcp import MCPServerStdio

class OllamaMCPClient:
    def __init__(self, mcp_server, ollama_model='llama3.1'):
        self.server = mcp_server
        self.ollama_client = ollama.AsyncClient()
        self.model = ollama_model
        
    async def call_mcp_tool(self, tool_name, arguments=None):
        """Call a specific MCP tool with the given arguments"""
        try:
            # This is a simplified version - you'd need to implement the actual MCP protocol
            # For now, let's assume your MCP server has a date calculation tool
            if tool_name == "calculate_days_between":
                # You would implement the actual MCP call here
                # For demonstration, let's calculate it directly
                from datetime import datetime
                
                start_date = datetime.strptime(arguments['start_date'], '%Y-%m-%d')
                end_date = datetime.strptime(arguments['end_date'], '%Y-%m-%d')
                delta = end_date - start_date
                return f"There are {delta.days} days between {arguments['start_date']} and {arguments['end_date']}."
        except Exception as e:
            return f"Error calling MCP tool: {e}"
    
    async def chat_with_tools(self, user_message):
        """Chat with Ollama and automatically call MCP tools when needed"""
        
        # First, ask Ollama to identify if we need to use any tools
        tool_detection_prompt = f"""
        Analyze this user message and determine if it requires calling external tools:
        "{user_message}"
        
        If this is asking for:
        - Date calculations between two dates, respond with: {{"tool": "calculate_days_between", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}
        - Mathematical calculations, respond with: {{"tool": "calculate", "expression": "math expression"}}
        - Otherwise respond with: {{"tool": "none"}}
        
        Only respond with the JSON, nothing else.
        """
        
        # Get tool detection response
        tool_response = await self.ollama_client.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': tool_detection_prompt}]
        )
        
        try:
            tool_data = json.loads(tool_response['message']['content'])
            
            if tool_data.get('tool') == 'calculate_days_between':
                # Call the MCP tool for date calculation
                mcp_result = await self.call_mcp_tool('calculate_days_between', {
                    'start_date': tool_data['start_date'],
                    'end_date': tool_data['end_date']
                })
                
                # Now ask Ollama to provide a nice response with the accurate result
                final_prompt = f"""
                The user asked: "{user_message}"
                
                I calculated the exact result using a date calculation tool: {mcp_result}
                
                Please provide a clear, concise response to the user incorporating this accurate calculation.
                """
                
                final_response = await self.ollama_client.chat(
                    model=self.model,
                    messages=[{'role': 'user', 'content': final_prompt}]
                )
                
                return final_response['message']['content']
            
        except json.JSONDecodeError:
            # If JSON parsing fails, fall back to normal chat
            pass
        
        # Normal chat without tools
        response = await self.ollama_client.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': user_message}]
        )
        
        return response['message']['content']

async def main():
    # Keep the MCP server connection
    server = MCPServerStdio(
        'python',
        args=['c:\\Users\\Noodl\\Projects\\Big_O\\Hackathon\\Sristi\\mcp_server.py'],
        env={
            'PATH': 'c:\\Users\\Noodl\\Projects\\New_Tech_Test\\Scripts;%PATH%'
        }
    )
    
    # Create our Ollama + MCP client
    client = OllamaMCPClient(server)
    
    # Start the MCP server
    async with server:
        # Test query
        user_message = 'How many days between 2000-01-01 and 2025-03-18?'
        
        print(f"User: {user_message}")
        print("AI: ", end="")
        
        response = await client.chat_with_tools(user_message)
        print(response)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
