import mariadb
from dotenv import load_dotenv
import os
load_dotenv()  # take environment variables from .env.

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")

connection = mariadb.connect(
    user=db_user,
    password=db_password,
    host=db_host,
    port=3306,
    database=db_name
)

global cursor 
cursor = connection.cursor(dictionary=True)

from mcp.server.fastmcp import FastMCP
import sys

mcp = FastMCP("database")

@mcp.tool()
def get_patient_details_mcp(patient_id: str):
    """
    MCP handler for getting patient details by ID.
    Args:
        patient_id (str): The ID of the patient to retrieve.
    Returns:
        dict: Patient details (e.g., {firstName, lastName, age}) or a JSON-RPC error object.
    """
    if not patient_id:
        return {"code": -32602, "message": "Invalid params: patient_id is required"}

    if not connection:
        print("Database connection is not available. Attempting to initialize.", file=sys.stderr)
        if not connection:
             return {"code": -32000, "message": "Database connection error"}
    cursor.execute("SELECT firstName, lastName, age FROM patients WHERE id = ?", (patient_id,))
    result = cursor.fetchone()
    if result:
        return {
            "firstName": result[0],
            "lastName": result[1],
            "age": result[2]
        }
    else:
        return {"code": -32602, "message": "Patient not found"}

if __name__ == "__main__":
    mcp.run(transport='stdio')