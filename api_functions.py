import requests
import keyring
import urllib.parse
import PySimpleGUI as sg


# ---------------------------- users Table ---------------------------- #

def is_first_time_setup(api_url):
    """
    Check if it's the first time setup by calling the Flask API.

    Args:
        api_url (str): The URL of the Flask API endpoint for checking first-time setup.

    Returns:
        bool: True if it's the first-time setup, False otherwise.
    """
    try:
        response = requests.get(api_url + '/is_first_time_setup')
        if response.status_code == 200:
            data = response.json()
            return data.get('first_time_setup', False)
        else:
            print("Failed to fetch first-time setup status.")
            return False
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return False


def create_admin_account(api_url, username, password, initials):
    """
    Create an admin account by sending a request to the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        username (str): The username for the new admin account.
        password (str): The password for the new admin account.
        initials (str): The initials for the new admin account.
    
    Returns:
        bool: True if the account was created successfully, False otherwise.
    """
    data = {
        'username': username,
        'password': password,
        'initials': initials
    }
    try:
        response = requests.post(f"{api_url}/create_admin_account", json=data)
        if response.status_code == 200:
            print(response.json())  # For debugging
            return True
        else:
            print("Failed to create admin account:", response.json())  # For debugging
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def validate_login(api_url, username, password):
    """
    Validate user login credentials by sending a request to the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        username (str): The username of the user.
        password (str): The password of the user.
    
    Returns:
        bool: True if the credentials are valid, False otherwise.
    """
    data = {
        'username': username,
        'password': password
    }
    try:
        response = requests.post(f"{api_url}/validate_login", json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get('valid', False):
                # store the token using keyring
                token = result.get('token')
                if token:
                    keyring.set_password('CareTechApp', 'access_token', token)
                    return True
            return False
        else:
            print("Failed to validate login credentials:", response.json())  # For debugging
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def create_user(api_url, username, password, user_role='User', is_temp_password=True, initials=''):
    """
    Create a new user by sending a request to the Flask API, using the stored authentication token.

    Args:
        api_url (str): The base URL of the Flask API.
        username (str): The username of the user.
        password (str): The password of the user.
        user_role (str, optional): The role of the user. Defaults to 'User'.
        is_temp_password (bool, optional): Indicates if the password is temporary. Defaults to True.
        initials (str, optional): The initials of the user. Defaults to ''.

    Returns:
        bool: True if the user was successfully created, False otherwise.
    """
    # Retrieve the stored token
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return False

    headers = {'Authorization': f'Bearer {token}'}
    data = {
        'username': username,
        'password': password,
        'user_role': user_role,
        'is_temp_password': is_temp_password,
        'initials': initials
    }

    try:
        response = requests.post(f"{api_url}/create_user", json=data, headers=headers)
        if response.status_code == 201:
            print("User created successfully.")
            return True
        else:
            print(f"Failed to create user: {response.json()}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def needs_password_reset(api_url, username):
    """
    Check if the specified user's password is temporary and needs to be reset.

    Args:
        api_url (str): The base URL of the Flask API.
        username (str): The username of the user to check.

    Returns:
        bool: True if the user's password needs to be reset, False otherwise.
    """
    data = {'username': username}
    try:
        response = requests.post(f"{api_url}/needs_password_reset", json=data)
        if response.status_code == 200:
            result = response.json()
            return result.get('needs_reset', False)
        elif response.status_code == 404:
            print("User not found.")
            return False
        else:
            print(f"Failed to check if password reset is needed: {response.json()}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def update_password(api_url, username, new_password):
    """
    Change the password for the specified user by sending a request to the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        username (str): The username of the user.
        new_password (str): The new password for the user.

    Returns:
        bool: True if the password was changed successfully, False otherwise.
    """
    # Retrieve the stored token
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return False

    headers = {'Authorization': f'Bearer {token}'}
    data = {
        'username': username,
        'new_password': new_password
    }

    try:
        response = requests.post(f"{api_url}/update_password", json=data, headers=headers)
        if response.status_code == 200:
            print("Password changed successfully.")
            return True
        elif response.status_code == 404:
            print("User not found.")
            return False
        else:
            print(f"Failed to change password: {response.json()}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def is_admin(api_url, username):
    """
    Check if the specified user is an admin by sending a request to the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        username (str): The username of the user to check.

    Returns:
        bool: True if the user is an admin, False otherwise, or None if an error occurs.
    """
    data = {'username': username}
    try:
        response = requests.post(f"{api_url}/is_admin", json=data)
        if response.status_code == 200:
            result = response.json()
            return result.get('is_admin', False)
        elif response.status_code == 404:
            print("User not found.")
            return None
        else:
            print("Failed to check admin status:", response.json())
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def get_user_initials(api_url):
    """
    Get the initials of the current user by sending a request to the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.

    Returns:
        str: The initials of the current user, or an empty string on failure.
    """
    # Retrieve the stored token
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return ''

    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(f"{api_url}/get_user_initials", headers=headers)
        if response.status_code == 200:
            result = response.json()
            return result.get('initials', '')
        else:
            print("Failed to fetch user initials:", response.json())
            return ''
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return ''

# ----------------------------- audit_logs Table ----------------------------- #

def log_action(api_url, username, activity, details):
    data = {
        "username": username,
        "activity": activity,
        "details": details
    }
    response = requests.post(f"{api_url}/log_action", json=data)
    if response.status_code == 200:
        print("Action logged successfully")
    else:
        print("Failed to log action")

 # ----------------------------- residents Table ------------------------------ #
        
def get_resident_count(api_url):
    """
    Fetch the number of residents from the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.

    Returns:
        int: The number of residents according to the Flask API, or 0 on failure.
    """
    try:
        response = requests.get(f"{api_url}/get_resident_count")
        if response.status_code == 200:
            result = response.json()
            return result.get('count', 0)
        else:
            print("Failed to fetch resident count:", response.json())  # For debugging
            return 0
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")  # For debugging
        return 0


def get_resident_care_level(api_url):
    """
    Fetch the care level of residents from the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.

    Returns:
        list: A list of care levels, or an empty list on failure.
    """
    # Retrieve the stored token
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return False

    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(f"{api_url}/get_resident_care_level", headers=headers)
        if response.status_code == 200:
            result = response.json()
            return result.get('residents', [])
        else:
            print("Failed to fetch resident care levels:", response.json())  # For debugging
            return []
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")  # For debugging
        return []


def get_resident_names(api_url):
    """
    Fetch the names of all residents from the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.

    Returns:
        list: A list of resident names, or an empty list on failure.
        
    """
    # Retrieve the stored token
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return False

    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(f"{api_url}/get_resident_names", headers=headers)
        if response.status_code == 200:
            # Assuming the JSON structure includes a "names" key
            names = response.json().get('names', [])
            return names
        else:
            print("Failed to fetch resident names:", response.json())  # For debugging
            return []
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")  # For debugging
        return []


def insert_resident(api_url, name, date_of_birth, level_of_care):
    """
    Insert a new resident into the database using the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        name (str): The name of the resident.
        date_of_birth (str): The date of birth of the resident in 'YYYY-MM-DD' format.
        level_of_care (str): The level of care required by the resident.

    Returns:
        bool: True if the resident was inserted successfully, False otherwise.
    """
    # Retrieve the stored token
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return False

    headers = {'Authorization': f'Bearer {token}'}
    data = {
        "name": name,
        "date_of_birth": date_of_birth,
        "level_of_care": level_of_care
    }
    try:
        response = requests.post(f"{api_url}/insert_resident", json=data, headers=headers)
        if response.status_code == 201:
            print("Resident inserted successfully.")
            return True
        else:
            print("Failed to insert resident:", response.json())
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


# -------------------------- adl_chart Table ------------------------------ #
    
def fetch_adl_data_for_resident(api_url, resident_name):
    """
    Fetch ADL data for a specific resident for the current day from the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): The name of the resident to fetch data for.

    Returns:
        dict: ADL data for the resident, or an empty dict on failure.
    """
    # Retrieve the stored token
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return {}

    headers = {'Authorization': f'Bearer {token}'}
    encoded_resident_name = urllib.parse.quote(resident_name)  # URL-encode the resident name
    url = f"{api_url}/fetch_adl_data_for_resident/{encoded_resident_name}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print("Failed to fetch ADL data:", response.json())
            return {}
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {}


def fetch_adl_chart_data_for_month(api_url, resident_name, year_month):
    """
    Fetch ADL data for a specific resident for a specific month from the Flask API.
    """
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return []

    headers = {'Authorization': f'Bearer {token}'}
    encoded_resident_name = urllib.parse.quote(resident_name)
    # Updated to send year_month as a query parameter
    url = f"{api_url}/fetch_adl_chart_data_for_month/{encoded_resident_name}?year_month={year_month}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print("Failed to fetch ADL chart data:", response.json())
            return []
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []


def save_adl_data_from_management_window(api_url, resident_name, adl_data, audit_description):
    """
    Save ADL data for a specific resident from the management window to the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): The name of the resident to save data for.
        adl_data (dict): The ADL data to save for the resident.

    Returns:
        bool: True if the data was saved successfully, False otherwise.
    """
    # Retrieve the stored token
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return False

    headers = {'Authorization': f'Bearer {token}'}
    data = {
        "resident_name": resident_name,
        "adl_data": adl_data,
        "audit_description": audit_description
    }
    try:
        response = requests.post(f"{api_url}/save_adl_data_from_management_window", json=data, headers=headers)
        if response.status_code == 200:
            print("ADL data saved successfully.")
            sg.popup("Data saved successfully!")
            return True
        else:
            print("Failed to save ADL data:", response.json())
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


# ------------------------------- medications Table ------------------------------- #

def insert_medication(api_url, resident_name, medication_name, dosage, instructions, medication_type, selected_time_slots, medication_form=None, medication_count=None):
    """
    Insert medication details for a resident via the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): Name of the resident.
        medication_name (str): Name of the medication.
        dosage (str): Dosage of the medication.
        instructions (str): Instructions for the medication.
        medication_type (str): Type of the medication (e.g., 'Scheduled', 'As Needed (PRN)', 'Controlled').
        selected_time_slots (list): List of selected time slots for the medication.
        medication_form (str, optional): Form of the medication (e.g., 'Pill', 'Liquid'). Default is None.
        medication_count (int, optional): Count of the medication for 'Controlled' type. Default is None.

    Returns:
        bool: True if the medication was inserted successfully, False otherwise.
    """
    # Retrieve the stored token
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return False

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {
        "resident_name": resident_name,
        "medication_name": medication_name,
        "dosage": dosage,
        "instructions": instructions,
        "medication_type": medication_type,
        "selected_time_slots": selected_time_slots,
        "medication_form": medication_form,
        "count": medication_count
    }

    try:
        response = requests.post(f"{api_url}/insert_medication", json=payload, headers=headers)
        if response.status_code == 200:
            print("Medication inserted successfully.")
            return True
        else:
            print(f"Failed to insert medication: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def fetch_medications_for_resident(api_url, resident_name):
    """
    Fetch medications for a specific resident from the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): The name of the resident whose medications are to be fetched.

    Returns:
        dict: Medication data for the resident, or an empty dict on failure.
    """
    # Retrieve the stored token
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return {}

    headers = {'Authorization': f'Bearer {token}'}
    # URL-encode the resident name to handle spaces and special characters
    encoded_resident_name = requests.utils.quote(resident_name)
    full_url = f"{api_url}/fetch_medications_for_resident/{encoded_resident_name}"

    try:
        response = requests.get(full_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to fetch medications:", response.text)
            return {}
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {}


def fetch_discontinued_medications(api_url, resident_name):
    """
    Fetch discontinued medications for a specific resident from the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): The name of the resident.

    Returns:
        dict: Discontinued medication names and dates, or an empty dict on failure.
    """
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return {}

    headers = {'Authorization': f'Bearer {token}'}
    url = f"{api_url}/fetch_discontinued_medications/{requests.utils.quote(resident_name)}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to fetch discontinued medications:", response.text)
            return {}
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {}


def filter_active_medications(api_url, resident_name, medication_names):
    """
    Filter active medications for a specific resident from the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): The name of the resident whose medications are to be filtered.
        medication_names (list): A list of medication names to filter.

    Returns:
        list: A list of active medication names for the resident, or an empty list on failure.
    """
    # Retrieve the stored token
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return []

    headers = {'Authorization': f'Bearer {token}'}
    data = {
        "resident_name": resident_name,
        "medication_names": medication_names
    }
    
    full_url = f"{api_url}/filter_active_medications"

    try:
        response = requests.post(full_url, json=data, headers=headers)
        if response.status_code == 200:
            # Expecting the server to return a list of active medication names
            return response.json().get('active_medications', [])
        else:
            print("Failed to filter medications:", response.text)
            return []
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []


# ------------------------------- non_medication_orders Table ------------------------------- #

def save_non_medication_order(api_url, resident_name, order_data):
    """
    Send a non-medication order for a specific resident to the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): The name of the resident for whom the order is being added.
        order_data (dict): The order data to be sent to the server.
    """
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return

    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(f"{api_url}/add_non_medication_order/{resident_name}", json=order_data, headers=headers)

    if response.status_code == 200:
        print("Non-medication order added successfully.")
    else:
        print(f"Failed to add non-medication order: {response.text}")


def fetch_all_non_medication_orders(api_url, resident_name):
    """
    Fetch all non-medication orders for a specific resident from the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): The name of the resident whose non-medication orders are to be fetched.

    Returns:
        A list of non-medication orders for the resident, or an error message.
    """
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return []

    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{api_url}/fetch_non_medication_orders/{resident_name}", headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch non-medication orders: {response.text}")
        return []

# --------------------------------- emar_chart Table ----------------------------------------- #

def fetch_emar_data_for_resident(api_url, resident_name):
    """
    Fetches eMAR data for a specific resident for the current day from a Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): The name of the resident whose eMAR data is being requested.

    Returns:
        dict: A dictionary containing eMAR data organized by medication name and time slot,
              or an empty dictionary if no data is found or an error occurs.
    """
    # Retrieve the stored token
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return {}

    headers = {'Authorization': f'Bearer {token}'}
    # URL-encode the resident name to handle spaces and special characters
    encoded_resident_name = requests.utils.quote(resident_name)
    full_url = f"{api_url}/fetch_emar_data_for_resident/{encoded_resident_name}"

    try:
        response = requests.get(full_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to fetch eMAR data:", response.text)
            return {}
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {}


def fetch_emar_data_for_month(api_url, resident_name, year_month):
    """
    Fetch eMAR data for a specific resident for a specific month from the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): The name of the resident to fetch data for.
        year_month (str): The year and month to fetch data for in 'YYYY-MM' format.

    Returns:
        list: A list of dictionaries containing eMAR data for the resident, or an empty list on failure.
    """
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return []

    headers = {'Authorization': f'Bearer {token}'}
    url = f"{api_url}/fetch_emar_data_for_month/{resident_name}?year_month={year_month}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            emar_data = response.json()
            return emar_data
        else:
            print("Failed to fetch eMAR data:", response.json())
            return []
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []


def save_emar_data_from_management_window(api_url, emar_data, audit_description):
    """
    Sends EMAR data and audit description to the Flask API to be saved and logged.

    Args:
        api_url (str): The base URL of the Flask API.
        emar_data (list): A list of dictionaries containing EMAR data.
        audit_description (str): Description of the audit for logging.

    Returns:
        Response from the API.
    """
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return False

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {"emar_data": emar_data, "audit_description": audit_description}

    try:
        response = requests.post(f"{api_url}/save_emar_data", json=payload, headers=headers)
        if response.status_code in [200, 201]:
            print("EMAR data saved successfully.")
            return response.json()
        else:
            print(f"Failed to save EMAR data: {response.text}")
            return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {}

# API_URL = 'http://127.0.0.1:5000'

# emar = fetch_emar_data_for_resident(API_URL, 'Dirty Diana')
# print(emar)
