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

# ----------------------------------------------------- user_settings Table ---------------------------------------- #

def save_user_preferences(api_url, theme, font):
    """
    Saves the user's theme and font choice to the server.

    Args:
        api_url (str): The base URL of the Flask API.
        theme (str): The name of the theme to save.
        font (str): The name of the font to save.

    Returns:
        bool: True if the preferences were saved successfully, False otherwise.
    """
    headers = {'Content-Type': 'application/json'}
    data = {'theme': theme, 'font': font}
    try:
        response = requests.post(f"{api_url}/save_user_preferences", json=data, headers=headers)
        if response.status_code == 200:
            print("User preferences saved successfully.")
            return True
        else:
            print(f"Failed to save user preferences: {response.json().get('error', 'Unknown error')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def get_user_preferences(api_url):
    """
    Fetches the user's theme and font preferences from the server without needing authentication.

    Args:
        api_url (str): The base URL of the Flask API.

    Returns:
        dict: A dictionary containing the user's theme and font preferences.
    """
    try:
        response = requests.get(f"{api_url}/get_user_preferences")
        if response.status_code == 200:
            preferences = response.json()
            #print("User preferences fetched successfully:", preferences)
            return preferences
        else:
            print(f"Failed to fetch user preferences: {response.text}")
            return {'theme': 'Reddit', 'font': 'Helvetica'}  # Default values in case of failure
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {'theme': 'Reddit', 'font': 'Helvetica'}


# ------------------------------------------------------------------------------ audit_logs Table ---------------------------------------------------- #

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
    

def fetch_audit_logs(api_url, last_10_days=False, username='', action='', date=''):
    """
    Fetches audit logs based on filters from the server.

    Args:
        api_url (str): The base URL of the Flask API.
        last_10_days (bool): Whether to filter logs from the last 10 days.
        username (str): Filter logs by username.
        action (str): Filter logs by action.
        date (str): Filter logs by specific date (YYYY-MM-DD).

    Returns:
        list: A list of audit log entries or an empty list on failure.
    """
    
    # Retrieve the stored token
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        'last_10_days': last_10_days,
        'username': username,
        'action': action,
        'date': date
    }

    try:
        response = requests.get(f"{api_url}/fetch_audit_logs", headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to fetch audit logs:", response.text)
            return []
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []


 # ----------------------------------------------------------------- residents Table ------------------------------------------------------------- #
        
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


def remove_resident(api_url, resident_name):
    """
    Remove a resident from the database using the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): The name of the resident to remove.

    Returns:
        bool: True if the resident was removed successfully, False otherwise.
    """
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return False

    headers = {'Authorization': f'Bearer {token}'}
    data = {"resident_name": resident_name}
    try:
        response = requests.post(f"{api_url}/remove_resident", json=data, headers=headers)
        if response.status_code == 200:
            print("Resident removed successfully.")
            return True
        elif response.status_code == 403:
            print("Unauthorized to remove resident.")
            return False
        elif response.status_code == 404:
            print("Resident not found.")
            return False
        else:
            print("Failed to remove resident:", response.json())
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


# ------------------------------------------------- adl_chart Table -------------------------------------------------------------- #
    
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
            return True
        else:
            print("Failed to save ADL data:", response.json())
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def does_adl_chart_exist(api_url, resident_name, year_month):
    """
    Checks if ADL chart data exists for a specific resident and month.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (int): The Name of the resident.
        year_month (str): The year and month in 'YYYY-MM' format.

    Returns:
        bool: True if the ADL chart data exists, False otherwise.
    """
    url = f"{api_url}/does_adl_chart_exist/{resident_name}/{year_month}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            return result.get('exists', False)
        else:
            print(f"Failed to check ADL chart existence: {response.json()}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False

# -------------------------------------------------- medications Table ------------------------------------------------ #

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

# ------------------------------------------------- emar_chart Table --------------------------------------------------------- #

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


def fetch_emar_data_for_resident_audit_log(api_url, resident_name):
    """
    Fetch eMAR data for a specific resident for today's date from the Flask API. This data is intended for creating audit logs.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): The name of the resident to fetch eMAR data for.

    Returns:
        list: A list of dictionaries, each containing eMAR data for the resident for today's date. Returns an empty list on failure.
    """
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return []

    headers = {'Authorization': f'Bearer {token}'}
    url = f"{api_url}/fetch_emar_data_for_resident_audit_log/{resident_name}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            emar_data = response.json()
            return emar_data
        else:
            print(f"Failed to fetch eMAR data for {resident_name}:", response.json())
            return []
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []


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


def does_emar_chart_exist(api_url, resident_name, year_month):
    """
    Checks if eMARs chart data exists for a specific resident and month by resident name.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): The name of the resident.
        year_month (str): The year and month in 'YYYY-MM' format.

    Returns:
        bool: True if the eMARs chart data exists, False otherwise.
    """
    url = f"{api_url}/does_emars_chart_exist/{resident_name}/{year_month}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            return result.get('exists', False)
        else:
            print(f"Failed to check eMARs chart existence for resident {resident_name}: {response.json()}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def save_prn_administration_data(api_url, resident_name, medication_name, admin_data):
    """
    Saves PRN administration data for a resident and medication.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): The name of the resident.
        medication_name (str): The name of the medication.
        admin_data (dict): Administration data including datetime, administered status, and notes.

    Returns:
        bool: True if the data was saved successfully, False otherwise.
    """
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return False

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {
        'resident_name': resident_name,
        'medication_name': medication_name,
        'admin_data': admin_data
    }

    try:
        response = requests.post(f"{api_url}/save_prn_administration", json=payload, headers=headers)
        if response.status_code == 201:
            print("Administration data saved successfully.")
            return True
        else:
            print(f"Failed to save administration data: {response.json()}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def fetch_prn_data_for_day(api_url, resident_name, medication_name, year_month, day):
    """
    Fetches PRN data for a specific day, resident, and medication.

    Args:
        api_url (str): The base URL of the Flask API.
        resident_name (str): The name of the resident.
        medication_name (str): The name of the medication.
        year_month (str): The year and month in 'YYYY-MM' format.
        day (str): The day of the month, as a string.

    Returns:
        list: A list of dictionaries containing PRN data for the specified criteria, or None on failure.
    """
    token = keyring.get_password('CareTechApp', 'access_token')
    if not token:
        print("No authentication token found. Please log in.")
        return None

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    url = f"{api_url}/fetch_prn_data_for_day/{resident_name}/{medication_name}/{year_month}/{day}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            prn_data = response.json()
            return prn_data
        else:
            print(f"Failed to fetch PRN data: {response.json()}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

# --------------------------------- activities Table ----------------------------------------- #

def fetch_activities(api_url):
    """
    Fetches activities from the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.

    Returns:
        list: A list of activities, or an empty list on failure.
    """
    try:
        response = requests.get(f"{api_url}/fetch_activities")
        if response.status_code == 200:
            activities_data = response.json()
            return activities_data.get('activities', [])
        else:
            print("Failed to fetch activities:", response.text)
            return []
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []


def add_activity(api_url, activity_name):
    """
    Adds a new activity to the database via the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        activity_name (str): The name of the activity to add.

    Returns:
        bool: True if the activity was added successfully, False otherwise.
    """
    full_url = f"{api_url}/add_activity"
    data = {'activity_name': activity_name}

    try:
        response = requests.post(full_url, json=data)
        if response.status_code == 201:
            print("Activity added successfully.")
            return True
        else:
            print(f"Failed to add activity: {response.json().get('error', 'Unknown error')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def remove_activity(api_url, activity_name):
    """
    Calls the API to remove an activity.

    Args:
        api_url (str): The base URL of the Flask API.
        activity_name (str): The name of the activity to remove.

    Returns:
        bool: True if the activity was successfully removed, False otherwise.
    """
    data = {'activity_name': activity_name}
    try:
        response = requests.post(f"{api_url}/remove_activity", json=data)
        if response.status_code == 200:
            print(f"Successfully removed activity: {activity_name}")
            return True
        else:
            print(f"Failed to remove activity: {response.json().get('error', 'Unknown error')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False

# --------------------------------- meals Table --------------------------------------------- #
    
def fetch_meal_data(api_url, meal_type):
    """
    Fetches meal data for a specific meal type from the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        meal_type (str): The type of meal to fetch data for ('breakfast', 'lunch', or 'dinner').

    Returns:
        list: A list of meals for the specified type, each meal as a list resembling the original tuple format, or an empty list on failure.
    """
    try:
        # Construct the URL with the meal type parameter
        full_url = f"{api_url}/fetch_meal_data/{meal_type}"
        response = requests.get(full_url)
        if response.status_code == 200:
            meal_data = response.json()['meals']
            # Process the meal data if any additional client-side processing is required
            return meal_data
        else:
            print(f"Failed to fetch {meal_type} data: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []


def fetch_raw_meal_data(api_url, meal_type):
    """
    Fetches raw meal data for a specific meal type from the Flask API, 
    including semicolons and, for breakfast, the default drink.

    Args:
        api_url (str): The base URL of the Flask API.
        meal_type (str): The type of meal to fetch data for ('breakfast', 'lunch', or 'dinner').

    Returns:
        list: A list of raw meal strings for the specified type, 
              with default drink included for breakfast, or an empty list on failure.
    """
    full_url = f"{api_url}/fetch_raw_meal_data/{meal_type}"
    try:
        response = requests.get(full_url)
        if response.status_code == 200:
            meal_data = response.json()['meals']
            return meal_data
        else:
            print(f"Failed to fetch raw {meal_type} data: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []


def add_meal(api_url, meal_type, meal_option, default_drink):
    """
    Adds a new meal option to the database via the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        meal_type (str): The type of meal to add the option to ('breakfast', 'lunch', or 'dinner').
        meal_option (str): The meal items.
        default_drink (str): The default drink option for the meal.

    Returns:
        bool: True if the meal option was added successfully, False otherwise.
    """
    full_url = f"{api_url}/add_meal"
    data = {'meal_type': meal_type, 'meal_option': meal_option, 'default_drink': default_drink}

    try:
        response = requests.post(full_url, json=data)
        if response.status_code == 201:
            print(f"Meal option added successfully: {meal_option}")
            return True
        else:
            print(f"Failed to add meal option: {response.json().get('error', 'Unknown error')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def remove_meal(api_url, meal_type, meal_option):
    """
    Removes a meal from the database via the Flask API.

    Args:
        api_url (str): The base URL of the Flask API.
        meal_type (str): The type of the meal (e.g., 'breakfast', 'lunch', 'dinner').
        meal_option (str): The exact option string of the meal to be removed.

    Returns:
        bool: True if the meal was successfully removed, False otherwise.
    """
    try:
        # Construct the URL with the meal type
        full_url = f"{api_url}/remove_meal/{meal_type}"
        headers = {'Content-Type': 'application/json'}
        data = {'meal_option': meal_option}
        
        response = requests.post(full_url, json=data, headers=headers)
        
        if response.status_code == 200:
            print("Meal removed successfully.")
            return True
        else:
            print(f"Failed to remove meal: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False
