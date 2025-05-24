import asyncio
from pydantic_ai.mcp import MCPServerStdio

async def list_mcp_tools():
    """List all available tools from the MCP server"""
    server = MCPServerStdio(
        'python',
        args=['c:\\Users\\Noodl\\Projects\\Big_O\\Hackathon\\Sristi\\mcp_server.py'],
        env={
            'PATH': 'c:\\Users\\Noodl\\Projects\\New_Tech_Test\\Scripts;%PATH%'
        }
    )
    
    async with server:
        try:
            # Get the list of available tools
            tools = await server.list_tools()
            
            print("🔧 Available MCP Tools:")
            print("=" * 50)
            
            if not tools:
                print("No tools found.")
                return
            
            for i, tool in enumerate(tools, 1):
                print(f"\n{i}. **{tool.name}**")
                if hasattr(tool, 'description') and tool.description:
                    print(f"   📝 Description: {tool.description}")
                
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    print(f"   📥 Input Schema:")
                    schema = tool.inputSchema
                    if hasattr(schema, 'properties') and schema.properties:
                        for prop_name, prop_info in schema.properties.items():
                            prop_type = prop_info.get('type', 'unknown')
                            prop_desc = prop_info.get('description', 'No description')
                            required = prop_name in getattr(schema, 'required', [])
                            required_str = " (required)" if required else " (optional)"
                            print(f"      • {prop_name}: {prop_type}{required_str} - {prop_desc}")
                
                print("-" * 30)
                
        except Exception as e:
            print(f"Error listing tools: {e}")
            print("\nLet me try to inspect the server directly...")
            
            # Alternative approach - check what functions are available
            try:
                # This will show us what the server can do
                print("\n🔍 Attempting to discover tools...")
                
                # Try to call a test connection if available
                result = await server.call_tool("d94_test_connection", {})
                print("✅ Server is responsive!")
                
                # List some known tools based on your MCP server
                known_tools = [
                    "d94_test_connection",
                    "d94_get_patient_detail", 
                    "d94_create_patient",
                    "d94_get_medical_history",
                    "d94_create_medical_history",
                    "d94_update_medical_history",
                    "d94_get_appointment_detail",
                    "d94_book_appointment",
                    "d94_update_appointment",
                    "d94_create_bill",
                    "d94_update_bill",
                    "d94_delete_bill",
                    "d94_update_patient_summary"
                ]
                
                print("\n🏥 Healthcare Management Tools Available:")
                print("=" * 50)
                
                for tool in known_tools:
                    print(f"• {tool}")
                    
            except Exception as inner_e:
                print(f"Could not discover tools: {inner_e}")

if __name__ == "__main__":
    asyncio.run(list_mcp_tools())
