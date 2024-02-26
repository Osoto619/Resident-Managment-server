import requests
import keyring

# ----------------- users Table ----------------- #

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


# ----------------- audit_logs Table ----------------- #

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

 # ----------------- residents Table ----------------- #
        
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