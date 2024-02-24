import requests

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
            return result.get('valid', False)
        else:
            print("Failed to validate login credentials:", response.json())  # For debugging
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def log_action(api_url, username, activity, description):
    data = {
        "username": username,
        "activity": activity,
        "description": description
    }
    response = requests.post(f"{api_url}/log_action", json=data)
    if response.status_code == 200:
        print("Action logged successfully")
    else:
        print("Failed to log action")