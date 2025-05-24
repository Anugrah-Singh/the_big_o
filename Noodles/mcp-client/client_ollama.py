import asyncio
import ollama
from pydantic_ai.mcp import MCPServerStdio

# Keep the MCP server connection
server = MCPServerStdio(
    'python',
    args=['c:\\Users\\Noodl\\Projects\\Big_O\\Hackathon\\Sristi\\mcp_server.py'],
    env={
        'PATH': 'c:\\Users\\Noodl\\Projects\\New_Tech_Test\\Scripts;%PATH%'
    }
)

async def main():
    # Start the MCP server
    async with server:
        # Use Ollama directly for the AI model
        ollama_client = ollama.AsyncClient()
        
        # Test query
        user_message = 'show me details of patient with id 1'
        
        print(f"Sending query to Ollama: {user_message}")
        
        # Call Ollama
        response = await ollama_client.chat(
            model='llama3.1',
            messages=[{'role': 'user', 'content': user_message}]
        )
        
        print("Ollama response:")
        print(response['message']['content'])

if __name__ == "__main__":
    asyncio.run(main())
