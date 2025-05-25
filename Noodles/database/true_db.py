import mariadb
from dotenv import load_dotenv
import os
import sys # Added sys import
import datetime

load_dotenv()

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")

# Remove global connection and cursor
# connection = mariadb.connect(...)
# global cursor
# cursor = connection.cursor(dictionary=True)

from mcp.server.fastmcp import FastMCP
mcp = FastMCP("database")

def get_db_connection():
    """Establishes and returns a new database connection."""
    try:
        print("DEBUG: get_db_connection - Attempting to connect to MariaDB...", file=sys.stderr)
        conn = mariadb.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=3306,
            database=db_name, 
            connect_timeout=10,
        )
        print("DEBUG: get_db_connection - MariaDB connection successful.", file=sys.stderr)
        return conn
    except mariadb.Error as e:
        print(f"DEBUG: get_db_connection - Failed to connect to database: {e}", file=sys.stderr)
        return None

@mcp.tool()
def test_connection():
    """
    MCP handler for testing the database connection.
    Returns:
        str: Connection status message or a JSON-RPC error object.
    """
    print("DEBUG: test_connection - Entered method.", file=sys.stderr)
    conn = get_db_connection()
    print(f"DEBUG: test_connection - get_db_connection returned: Connection is {'not None' if conn else 'None'}", file=sys.stderr)
    if conn:
        conn.close()
        print("DEBUG: test_connection - Connection closed, returning success.", file=sys.stderr)
        return {"status": "Connection successful"}
    else:
        print("DEBUG: test_connection - No connection, returning error.", file=sys.stderr)
        return {"code": -32000, "message": "Database connection error"}

@mcp.tool()
def create_patient(
    first_name: str,
    last_name: str,
    age: int = None,
    conversation_summary: str = None
) -> dict:
    """
    Inserts a new patient record into the patients table.

    Args:
        first_name (str): The first name of the patient.
        last_name (str): The last name of the patient.
        age (int, optional): The age of the patient. Defaults to None.
        conversation_summary (str, optional): The initial conversation summary for the patient. Defaults to None.

    Returns:
        dict: The result of the operation, including the new patient_id on success, or an error object.
    """
    conn = get_db_connection()
    if not conn:
        return {"code": -32000, "message": "Database connection error"}

    try:
        cursor = conn.cursor(dictionary=True)

        # Construct the INSERT query dynamically to handle optional fields
        columns = ["first_name", "last_name"]
        values_placeholders = ["%s", "%s"]
        insert_values = [first_name, last_name]

        if age is not None:
            columns.append("age")
            values_placeholders.append("%s")
            insert_values.append(age)
        if conversation_summary is not None:
            columns.append("conversation_summary")
            values_placeholders.append("%s")
            insert_values.append(conversation_summary)

        sql_query = f"INSERT INTO patients ({', '.join(columns)}) VALUES ({', '.join(values_placeholders)})"

        cursor.execute(sql_query, tuple(insert_values))
        conn.commit()
        new_patient_id = cursor.lastrowid
        return {"status": "Patient created successfully", "patient_id": new_patient_id}
    except mariadb.Error as e:
        print(f"Error creating patient: {e}", file=sys.stderr)
        return {"code": -32000, "message": f"Database query error: {e}"}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



@mcp.tool()
def get_patient_detail(patient_id):
    """
    MCP handler for getting a specific patient's details.
    Args:
        patient_id (int): The ID of the patient to retrieve.
    Returns:
        dict: The patient record or a JSON-RPC error object.
    """
    conn = get_db_connection()
    if not conn:
        return {"code": -32000, "message": "Database connection error"}

    try:
        cursor = conn.cursor(dictionary=True)
        # Use %s instead of ? for MariaDB/MySQL parameterized queries
        cursor.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
        patient = cursor.fetchone()
        return patient if patient else {"code": -32000, "message": "Patient not found"} 
    except mariadb.Error as e:
        import traceback
        print(f"Error fetching patients: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {"code": -32000, "message": f"Database query error: {e}", "input": patient_id}
    finally:
        cursor.close()
        conn.close()

@mcp.tool()
def book_appointment(patient_id: int, doctor_id: int, appointment_date: str, reason: str = None) -> dict:
    """
    MCP handler for booking an appointment.
    Args:
        patient_id (int): The ID of the patient.
        doctor_id (int): The ID of the doctor.
        appointment_date (str): The appointment date and time (e.g., "YYYY-MM-DD HH:MM:SS").
        reason (str, optional): The reason for the appointment. Defaults to None.
    Returns:
        dict: The result of the booking operation or a JSON-RPC error object.
    """
    conn = get_db_connection()
    if not conn:
        return {"code": -32000, "message": "Database connection error"}

    try:
        cursor = conn.cursor(dictionary=True)
        # Updated SQL to use 'appointment_date' and include 'reason'
        cursor.execute(
            "INSERT INTO appointments (patient_id, doctor_id, appointment_date, reason) VALUES (%s, %s, %s, %s)",
            (patient_id, doctor_id, appointment_date, reason)
        )
        conn.commit()
        return {"status": "Appointment booked successfully", "appointment_id": cursor.lastrowid}
    except mariadb.Error as e:
        import traceback
        print(f"Error booking appointment: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {
            "code": -32000,
            "message": f"Database query error: {e}",
            "input": {
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "appointment_date": appointment_date,
                "reason": reason
            }
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@mcp.tool() # Uncomment if you're using an MCP decorator
def get_appointment_detail(patient_id: int) -> dict:
    """
    MCP handler for getting all appointments for a specific patient.
    Args:
        patient_id (int): The ID of the patient to retrieve appointments for.
    Returns:
        list: A list of appointment records, or a JSON-RPC error object if none found or error occurs.
    """
    conn = get_db_connection()
    if not conn:
        return {"code": -32000, "message": "Database connection error"}

    try:
        cursor = conn.cursor(dictionary=True)
        # The column name in the DB is 'appointment_date', not 'time'
        cursor.execute("SELECT * FROM appointments WHERE patient_id = %s", (patient_id,))
        appointments = cursor.fetchall() # Changed from fetchone to fetchall

        if appointments:
            return {"appointments": appointments}
        else:
            return {"code": -32000, "message": f"No appointments found for patient ID: {patient_id}"}
    except mariadb.Error as e:
        import traceback
        print(f"Error fetching appointments: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {
            "code": -32000,
            "message": f"Database query error: {e}",
            "input": {"patient_id": patient_id}
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@mcp.tool()
def update_appointment(
    appointment_id: int,
    doctor_id: int = None,
    appointment_date: str = None, # Expects "YYYY-MM-DD HH:MM:SS"
    reason: str = None,
    status: str = None
) -> dict:
    """
    MCP handler for updating one or more details of a specific appointment.
    Only provided parameters will be updated.

    Args:
        appointment_id (int): The ID of the appointment to update.
        doctor_id (int, optional): The new ID of the doctor for the appointment.
        appointment_date (str, optional): The new date and time for the appointment (e.g., "YYYY-MM-DD HH:MM:SS").
        reason (str, optional): The new reason for the appointment.
        status (str, optional): The new status for the appointment (e.g., 'scheduled', 'completed', 'canceled').

    Returns:
        dict: The result of the update operation or a JSON-RPC error object.
    """
    conn = get_db_connection()
    if not conn:
        return {"code": -32000, "message": "Database connection error"}

    try:
        cursor = conn.cursor(dictionary=True)
        update_fields = []
        update_values = []

        # Check each optional parameter and add it to the update list if provided
        if doctor_id is not None:
            update_fields.append("doctor_id = %s")
            update_values.append(doctor_id)
        if appointment_date is not None:
            update_fields.append("appointment_date = %s")
            update_values.append(appointment_date)
        if reason is not None:
            update_fields.append("reason = %s")
            update_values.append(reason)
        if status is not None:
            update_fields.append("status = %s")
            update_values.append(status)

        # If no fields were provided for update, return immediately
        if not update_fields:
            return {"status": "No valid fields provided for update. No action taken."}

        # Construct the SQL query dynamically
        sql_query = f"UPDATE appointments SET {', '.join(update_fields)} WHERE appointment_id = %s"
        update_values.append(appointment_id) # Add appointment_id to the end for the WHERE clause

        cursor.execute(sql_query, tuple(update_values))
        conn.commit()

        if cursor.rowcount > 0:
            return {"status": "Appointment updated successfully", "appointment_id": appointment_id}
        else:
            # This means the appointment_id was not found in the database
            return {"code": -32000, "message": f"Appointment with ID {appointment_id} not found or no changes made."}
    except mariadb.Error as e:
        print(f"Error updating appointment: {e}", file=sys.stderr)
        return {
            "code": -32000,
            "message": f"Database query error: {e}",
            "input": {
                "appointment_id": appointment_id,
                "doctor_id": doctor_id,
                "appointment_date": appointment_date,
                "reason": reason,
                "status": status
            }
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ---
# Function to update or set a patient's summary
# ---

@mcp.tool() # Uncomment if you're using an MCP decorator
def update_patient_summary(patient_id: int, new_conversation_summary: str) -> dict:
    """
    Updates or sets a patient's conversation summary directly in the patients table.
    If a summary already exists for the patient, it will be overwritten.
    Args:
        patient_id (int): The ID of the patient.
        new_conversation_summary (str): The new content for the patient's summary.
    Returns:
        dict: The result of the operation or a JSON-RPC error object.
    """
    conn = get_db_connection()
    if not conn:
        return {"code": -32000, "message": "Database connection error"}

    try:
        cursor = conn.cursor(dictionary=True)
        # Update the conversation_summary directly in the patients table
        cursor.execute(
            "UPDATE patients SET conversation_summary = %s WHERE patient_id = %s",
            (new_conversation_summary, patient_id)
        )
        conn.commit()

        if cursor.rowcount > 0:
            return {"status": "Patient summary updated successfully", "patient_id": patient_id}
        else:
            # This case means the patient_id was not found, so no row was updated.
            return {"code": -32000, "message": f"Patient with ID {patient_id} not found."}
    except mariadb.Error as e:
        print(f"Error updating patient summary: {e}", file=sys.stderr)
        return {
            "code": -32000,
            "message": f"Database query error: {e}",
            "input": {"patient_id": patient_id, "new_conversation_summary": new_conversation_summary}
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@mcp.tool()
def create_medical_history(
    patient_id: int,
    allergies: str = None,
    chronic_conditions: str = None,
    current_medications: str = None,
    past_medical_history: str = None
) -> dict:
    """
    MCP handler for creating an initial medical history record for a patient.
    This should be used when a patient does not yet have a history record.
    Args:
        patient_id (int): The ID of the patient.
        allergies (str, optional): Known allergies.
        chronic_conditions (str, optional): Ongoing chronic health conditions.
        current_medications (str, optional): Medications patient is currently taking.
        past_medical_history (str, optional): Significant past medical events or surgeries.
    Returns:
        dict: The result of the operation or an error object.
    """
    conn = get_db_connection()
    if not conn:
        return {"code": -32000, "message": "Database connection error"}

    try:
        cursor = conn.cursor(dictionary=True)
        # Optional: Check if history already exists to prevent primary key violation if called incorrectly
        cursor.execute("SELECT COUNT(*) FROM PatientMedicalHistory WHERE patient_id = %s", (patient_id,))
        if cursor.fetchone()['COUNT(*)'] > 0:
            print(f"Warning: Medical history already exists for patient ID {patient_id}. Use update_medical_history instead.", file=sys.stderr)
            return {"code": -32000, "message": f"Medical history already exists for patient ID {patient_id}. Use update_medical_history instead."}        # Insert the new record with provided data and current timestamp for last_updated_at
        cursor.execute(
            "INSERT INTO PatientMedicalHistory (patient_id, allergies, chronic_conditions, current_medications, past_medical_history, last_updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (patient_id, allergies, chronic_conditions, current_medications, past_medical_history, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        return {"status": "Medical history created successfully", "patient_id": patient_id}
    except mariadb.Error as e:
        print(f"Error creating medical history: {e}", file=sys.stderr)
        return {"code": -32000, "message": f"Database query error: {e}"}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@mcp.tool() # Uncomment if you're using an MCP decorator
def get_medical_history(patient_id: int) -> dict:
    """
    Retrieves a patient's medical history from the PatientMedicalHistory table.
    Args:
        patient_id (int): The ID of the patient.
    Returns:
        dict: A dictionary containing the patient's medical history details,
              or an error object if not found or an error occurs.
    """
    conn = get_db_connection()
    if not conn:
        return {"code": -32000, "message": "Database connection error"}

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT patient_id, allergies, chronic_conditions, current_medications, past_medical_history, last_updated_at "
            "FROM PatientMedicalHistory WHERE patient_id = %s",
            (patient_id,)
        )
        medical_history = cursor.fetchone()

        if medical_history:
            return medical_history
        else:
            # If no history record found for this patient_id
            return {"code": -32000, "message": f"Medical history not found for patient ID: {patient_id}"}
    except mariadb.Error as e:
        print(f"Error fetching medical history: {e}", file=sys.stderr)
        return {
            "code": -32000,
            "message": f"Database query error: {e}",
            "input": {"patient_id": patient_id}
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ---
# Function to update a patient's medical history
# ---

@mcp.tool() # Uncomment if you're using an MCP decorator
def update_medical_history(
    patient_id: int,
    allergies: str = None,
    chronic_conditions: str = None,
    current_medications: str = None,
    past_medical_history: str = None
) -> dict:
    """
    Updates a patient's medical history in the PatientMedicalHistory table.
    All fields are optional; only provided fields will be updated.
    Args:
        patient_id (int): The ID of the patient whose history is to be updated.
        allergies (str, optional): New allergies string.
        chronic_conditions (str, optional): New chronic conditions string.
        current_medications (str, optional): New current medications string.
        past_medical_history (str, optional): New past medical history string.
    Returns:
        dict: The result of the update operation or a JSON-RPC error object.
    """
    conn = get_db_connection()
    if not conn:
        return {"code": -32000, "message": "Database connection error"}

    try:
        cursor = conn.cursor(dictionary=True)
        update_fields = []
        update_values = []

        if allergies is not None:
            update_fields.append("allergies = %s")
            update_values.append(allergies)
        if chronic_conditions is not None:
            update_fields.append("chronic_conditions = %s")
            update_values.append(chronic_conditions)
        if current_medications is not None:
            update_fields.append("current_medications = %s")
            update_values.append(current_medications)
        if past_medical_history is not None:
            update_fields.append("past_medical_history = %s")
            update_values.append(past_medical_history)        # Always update last_updated_at
        update_fields.append("last_updated_at = %s")
        update_values.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')) # Format for DATETIME

        if not update_fields:
            return {"status": "No fields provided to update."}

        sql_query = f"UPDATE PatientMedicalHistory SET {', '.join(update_fields)} WHERE patient_id = %s"
        update_values.append(patient_id) # Add patient_id to the end for the WHERE clause

        cursor.execute(sql_query, tuple(update_values))
        conn.commit()

        if cursor.rowcount > 0:
            return {"status": "Medical history updated successfully", "patient_id": patient_id}
        else:
            # This happens if the patient_id does not exist in PatientMedicalHistory
            # (even if they exist in patients, they might not have a history record yet)
            return {"code": -32000, "message": f"Patient medical history for ID {patient_id} not found to update. "
                                              "Ensure a history record exists for this patient."}
    except mariadb.Error as e:
        print(f"Error updating medical history: {e}", file=sys.stderr)
        return {
            "code": -32000,
            "message": f"Database query error: {e}",
            "input": {"patient_id": patient_id, "allergies": allergies,
                      "chronic_conditions": chronic_conditions,
                      "current_medications": current_medications,
                      "past_medical_history": past_medical_history}
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@mcp.tool()
def create_bill(
    patient_id: int,
    total_amount: float,
    particulars: str = None,
    amount_paid: float = 0.00,
    paid_on: str = None, # Expects "YYYY-MM-DD HH:MM:SS" or None
    status: str = 'pending'
) -> dict:
    """
    Creates a new bill record in the bills table.

    Args:
        patient_id (int): The ID of the patient for whom the bill is created.
        total_amount (float): The total amount due for the bill.
        particulars (str, optional): A description of the bill. Defaults to None.
        amount_paid (float, optional): The amount already paid. Defaults to 0.00.
        paid_on (str, optional): Date and time when the bill was fully paid (YYYY-MM-DD HH:MM:SS). Defaults to None.
        status (str, optional): The initial status of the bill (e.g., 'pending', 'paid'). Defaults to 'pending'.

    Returns:
        dict: The result of the operation, including the new bill_id on success, or an error object.
    """
    conn = get_db_connection()
    if not conn:
        return {"code": -32000, "message": "Database connection error"}

    try:
        cursor = conn.cursor(dictionary=True)
        # SQL query to insert a new bill
        cursor.execute(
            "INSERT INTO bills (patient_id, particulars, total_amount, amount_paid, paid_on, status) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (patient_id, particulars, total_amount, amount_paid, paid_on, status)
        )
        conn.commit()
        new_bill_id = cursor.lastrowid
        return {"status": "Bill created successfully", "bill_id": new_bill_id}
    except mariadb.Error as e:
        print(f"Error creating bill: {e}", file=sys.stderr)
        return {"code": -32000, "message": f"Database query error: {e}"}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ---
# Function to delete a bill
# ---

@mcp.tool()
def delete_bill(bill_id: int) -> dict:
    """
    Deletes a bill record from the bills table.

    Args:
        bill_id (int): The ID of the bill to delete.

    Returns:
        dict: The result of the operation or an error object.
    """
    conn = get_db_connection()
    if not conn:
        return {"code": -32000, "message": "Database connection error"}

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("DELETE FROM bills WHERE bill_id = %s", (bill_id,))
        conn.commit()

        if cursor.rowcount > 0:
            return {"status": "Bill deleted successfully", "bill_id": bill_id}
        else:
            return {"code": -32000, "message": f"Bill with ID {bill_id} not found."}
    except mariadb.Error as e:
        print(f"Error deleting bill: {e}", file=sys.stderr)
        return {"code": -32000, "message": f"Database query error: {e}"}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ---
# Function to update an existing bill
# ---

@mcp.tool()
def update_bill(
    bill_id: int,
    particulars: str = None,
    total_amount: float = None,
    amount_paid: float = None,
    paid_on: str = None, # Expects "YYYY-MM-DD HH:MM:SS" or None
    status: str = None
) -> dict:
    """
    Updates one or more details of an existing bill record.
    Only provided parameters will be updated.

    Args:
        bill_id (int): The ID of the bill to update.
        particulars (str, optional): New description for the bill.
        total_amount (float, optional): New total amount due.
        amount_paid (float, optional): New amount paid.
        paid_on (str, optional): New date and time when the bill was fully paid (YYYY-MM-DD HH:MM:SS).
                                  Set to None to clear the paid_on date.
        status (str, optional): New status of the bill.

    Returns:
        dict: The result of the operation or an error object.
    """
    conn = get_db_connection()
    if not conn:
        return {"code": -32000, "message": "Database connection error"}

    try:
        cursor = conn.cursor(dictionary=True)
        update_fields = []
        update_values = []

        # Dynamically build the UPDATE query based on provided arguments
        if particulars is not None:
            update_fields.append("particulars = %s")
            update_values.append(particulars)
        if total_amount is not None:
            update_fields.append("total_amount = %s")
            update_values.append(total_amount)
        if amount_paid is not None:
            update_fields.append("amount_paid = %s")
            update_values.append(amount_paid)
        if paid_on is not None: # Can be set to a datetime string or None to clear
            update_fields.append("paid_on = %s")
            update_values.append(paid_on)
        elif 'paid_on' in locals() and paid_on is None: # Explicitly setting paid_on to NULL
             update_fields.append("paid_on = NULL")
        if status is not None:
            update_fields.append("status = %s")
            update_values.append(status)

        if not update_fields:
            return {"status": "No valid fields provided for update. No action taken."}

        sql_query = f"UPDATE bills SET {', '.join(update_fields)} WHERE bill_id = %s"
        update_values.append(bill_id) # Add bill_id for the WHERE clause

        cursor.execute(sql_query, tuple(update_values))
        conn.commit()

        if cursor.rowcount > 0:
            return {"status": "Bill updated successfully", "bill_id": bill_id}
        else:
            return {"code": -32000, "message": f"Bill with ID {bill_id} not found or no changes made."}
    except mariadb.Error as e:
        print(f"Error updating bill: {e}", file=sys.stderr)
        return {"code": -32000, "message": f"Database query error: {e}"}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    print("MCP server started.", file=sys.stderr)
    import uvicorn
    print("Starting MCP server via Uvicorn.", file=sys.stderr)
    mcp.run(transport="stdio")