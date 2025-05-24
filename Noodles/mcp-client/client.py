import asyncio
import ollama
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio(
    'python',
    args=['c:\\Users\\Noodl\\Projects\\Big_O\\Hackathon\\Sristi\\mcp_server.py'],
    env={
        'PATH': 'c:\\Users\\Noodl\\Projects\\New_Tech_Test\\Scripts;%PATH%'
    }
)

async def main():
    # Use Ollama directly since pydantic-ai doesn't support Ollama yet
    ollama_client = ollama.AsyncClient()
    
    async with server:
        # Test query
        user_message = 'How many days between 2000-01-01 and 2025-03-18?'
        
        print(f"Query: {user_message}")
        
        response = await ollama_client.chat(
            model='llama3.1',
            messages=[{'role': 'user', 'content': user_message}]
        )
        
        print("Response:")
        print(response['message']['content'])

if __name__ == "__main__":
    asyncio.run(main())