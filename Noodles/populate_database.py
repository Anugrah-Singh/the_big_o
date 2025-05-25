
import sys
import os
import datetime

# Assuming the script is in 'Noodles' directory and 'tools' is a subdirectory 'Noodles/tools/'
# containing 'tools.py'. This makes 'tools' a package and 'tools.py' a module.
try:
    from tools import tools as clinic_tools
except ImportError as e:
    print(f"Failed to import 'tools.tools'. Error: {e}", file=sys.stderr)
    # This might happen if the script's CWD is not 'Noodles' or 'Noodles' is not in PYTHONPATH.
    # Adding 'Noodles' to sys.path if it's the presumed workspace root.
    # This path is an example; adjust if the execution context is different.
    # workspace_root_for_path = "c:/Users/Noodl/Projects/Big_O/Hackathon/Sristi/PROPER/the_big_o/Noodles"
    # if workspace_root_for_path not in sys.path:
    #    sys.path.insert(0, workspace_root_for_path)
    # try:
    #    from tools import tools as clinic_tools
    # except ImportError as e2:
    #    print(f"Still failed to import 'tools.tools' after path adjustment. Error: {e2}", file=sys.stderr)
    #    sys.exit(1)
    print("Please ensure the script is run from the 'Noodles' directory or that PYTHONPATH is configured correctly.", file=sys.stderr)
    sys.exit(1)


doctor_ids_map = {} 
patient_data_ids_list = []
patient_legacy_ids_list = [] 

def populate_doctors():
    print("\\n--- Creating Doctors ---")
    specialties = [
        "Family Medicine", "Internal Medicine", "Pediatrics", "Obstetrics/Gynecology",
        "Cardiology", "Dermatology", "Psychiatry", "General Surgery",
        "Orthopedics", "Neurology"
    ]
    doctor_first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth"]
    doctor_last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

    for i, specialty in enumerate(specialties):
        first_name = doctor_first_names[i % len(doctor_first_names)]
        # Use a simple scheme for unique last names for dummy data
        unique_last_name = f"{doctor_last_names[i % len(doctor_last_names)]}_{i+1}" 

        result = clinic_tools.create_doctor(first_name=first_name, last_name=unique_last_name, specialty=specialty)
        print(f"Create Doctor ({first_name} {unique_last_name}, {specialty}): {result}")
        if result and result.get("doctor_id"):
            doctor_ids_map[f"{first_name}_{unique_last_name}"] = result["doctor_id"]
        else:
            print(f"Failed to create doctor {first_name} {unique_last_name}. Error: {result.get('message', 'Unknown error')}", file=sys.stderr)
    print(f"Doctor IDs created: {doctor_ids_map}")

def populate_patient_data_entries():
    print("\\n--- Creating Patient Data (patient_data table) ---")
    patients_info = [
        {"first_name": "David", "last_name": "Wilson", "dob": "1985-05-20", "sex": "Male", "phone": "555-0011", "city": "New York"},
        {"first_name": "Sarah", "last_name": "Taylor", "dob": "1992-11-30", "sex": "Female", "phone": "555-0022", "city": "Los Angeles"},
        {"first_name": "Paul", "last_name": "Anderson", "dob": "1978-07-10", "sex": "Male", "phone": "555-0033", "city": "Chicago"},
        {"first_name": "Nancy", "last_name": "Thomas", "dob": "2000-02-15", "sex": "Female", "phone": "555-0044", "city": "Houston"},
        {"first_name": "Mark", "last_name": "Jackson", "dob": "1988-09-05", "sex": "Male", "phone": "555-0055", "city": "Phoenix"}
    ]
    for p_info in patients_info:
        result = clinic_tools.create_patient_data(**p_info)
        print(f"Create Patient Data ({p_info['first_name']} {p_info['last_name']}): {result}")
        if result and result.get("patient_data_id"):
            patient_data_ids_list.append(result["patient_data_id"])
        else:
            print(f"Failed to create patient_data for {p_info['first_name']} {p_info['last_name']}. Error: {result.get('message', 'Unknown error')}", file=sys.stderr)
    print(f"Patient Data IDs created: {patient_data_ids_list}")

def populate_legacy_patient_entries():
    print("\\n--- Creating Legacy Patients (patients table for appointments/history) ---")
    legacy_patients_info = [
        {"first_name": "David", "last_name": "Wilson", "age": 38, "summary": "Legacy record for David Wilson"},
        {"first_name": "Sarah", "last_name": "Taylor", "age": 31, "summary": "Legacy record for Sarah Taylor"},
        {"first_name": "Paul", "last_name": "Anderson", "age": 45, "summary": "Legacy record for Paul Anderson"}
    ]
    for lp_info in legacy_patients_info:
        result = clinic_tools.create_patient(first_name=lp_info["first_name"], last_name=lp_info["last_name"], age=lp_info["age"], conversation_summary=lp_info["summary"])
        print(f"Create Legacy Patient ({lp_info['first_name']} {lp_info['last_name']}): {result}")
        if result and result.get("patient_id"):
            patient_legacy_ids_list.append(result["patient_id"])
        else:
            print(f"Failed to create legacy patient for {lp_info['first_name']} {lp_info['last_name']}. Error: {result.get('message', 'Unknown error')}", file=sys.stderr)
    print(f"Legacy Patient IDs created: {patient_legacy_ids_list}")

def populate_related_data():
    print("\\n--- Creating Appointments and Medical History ---")
    if not patient_legacy_ids_list or not doctor_ids_map:
        print("Cannot create appointments/history: missing patient_legacy_ids_list or doctor_ids_map.", file=sys.stderr)
        return

    doc_ids_available = list(doctor_ids_map.values())
    if not doc_ids_available:
        print("No doctors available to book appointments.", file=sys.stderr)
        return

    # Appointments for the first legacy patient
    pat_id_for_appt = patient_legacy_ids_list[0]
    
    appt_date1 = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    result_appt1 = clinic_tools.book_appointment(patient_id=pat_id_for_appt, doctor_id=doc_ids_available[0], appointment_date=appt_date1, reason="Annual Checkup")
    print(f"Book Appointment for patient {pat_id_for_appt} with doctor {doc_ids_available[0]}: {result_appt1}")

    if len(doc_ids_available) > 1:
        appt_date2 = (datetime.datetime.now() + datetime.timedelta(days=14)).strftime('%Y-%m-%d %H:%M:%S')
        result_appt2 = clinic_tools.book_appointment(patient_id=pat_id_for_appt, doctor_id=doc_ids_available[1], appointment_date=appt_date2, reason="Follow-up Consultation")
        print(f"Book Appointment for patient {pat_id_for_appt} with doctor {doc_ids_available[1]}: {result_appt2}")

    # Medical History for the first legacy patient
    result_hist1 = clinic_tools.create_medical_history(
        patient_id=pat_id_for_appt,
        allergies="Pollen, Peanuts",
        chronic_conditions="Asthma",
        current_medications="Inhaler (Albuterol)",
        past_medical_history="Tonsillectomy (2005)"
    )
    print(f"Create Medical History for patient {pat_id_for_appt}: {result_hist1}")

    # Medical History for the second legacy patient (if exists)
    if len(patient_legacy_ids_list) > 1:
        pat_id_for_hist2 = patient_legacy_ids_list[1]
        result_hist2 = clinic_tools.create_medical_history(
            patient_id=pat_id_for_hist2,
            allergies="None known",
            chronic_conditions="None",
            current_medications="Multivitamins",
            past_medical_history="Appendectomy (2010)"
        )
        print(f"Create Medical History for patient {pat_id_for_hist2}: {result_hist2}")

def main():
    print("Starting database population script...")
    connection_status = clinic_tools.test_connection()
    print(f"Database Connection Test: {connection_status}")
    if not isinstance(connection_status, str) or "successful" not in connection_status.lower():
        print(f"Database connection failed or returned unexpected status: {connection_status}. Aborting population.", file=sys.stderr)
        return

    populate_doctors()
    populate_patient_data_entries()
    populate_legacy_patient_entries() 
    populate_related_data()

    print("\\n--- Listing some data for verification (first 5 records if many) ---")
    all_docs = clinic_tools.list_doctors()
    if all_docs and all_docs.get("doctors"):
        print(f"All Doctors (first 5 of {len(all_docs['doctors'])}): {all_docs['doctors'][:5]}")
    else:
        print(f"List Doctors: {all_docs}")

    all_patient_data = clinic_tools.list_all_patient_data()
    if all_patient_data and all_patient_data.get("patient_data_records"):
         print(f"All Patient Data (first 5 of {len(all_patient_data['patient_data_records'])}): {all_patient_data['patient_data_records'][:5]}")
    else:
        print(f"List All Patient Data: {all_patient_data}")
        
    if patient_legacy_ids_list:
        print(f"Appointments for patient {patient_legacy_ids_list[0]}: {clinic_tools.get_appointment_detail(patient_legacy_ids_list[0])}")


    print("\\nDatabase population script finished.")

if __name__ == "__main__":
    main()

