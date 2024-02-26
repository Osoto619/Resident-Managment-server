from flask import Flask, jsonify, request
from flask_jwt_extended import create_access_token, JWTManager , jwt_required, get_jwt_identity
import mysql.connector
from mysql.connector import Error
import bcrypt
from encryption_utils import encrypt_data, decrypt_data
from datetime import datetime

app = Flask(__name__)

# Ensure you have a secret key set for JWT to use
app.config['JWT_SECRET_KEY'] = 'fSdas23#%@adY'  # Change this!

jwt = JWTManager(app)  # Initialize Flask-JWT-Extended with your Flask app

def get_db_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            user='oscar',
            password='Discorama619!',
            host='10.0.0.53',
            database='resident_data'
        )
    except Error as err:
        print(f"Error: '{err}'")
    return connection


def log_action(username, activity, description):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            encrypted_description = encrypt_data(description)
            cursor.execute("INSERT INTO audit_logs (username, activity, description, log_time) VALUES (%s, %s, %s, %s)", 
                           (username, activity, encrypted_description, current_time))
            conn.commit()
            conn.close()
            return True
        else:
            return False
    except Error as e:
        print(f"Database error: {e}")
        return False


# --------------------------------- users Table --------------------------------- #

@app.route('/is_first_time_setup', methods=['GET'])
def is_first_time_setup():
    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM users")
            user_count = cursor.fetchone()[0]
            conn.close()
            return jsonify({'first_time_setup': user_count == 0}), 200
        else:
            return jsonify({'error': 'Failed to connect to the database'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500


@app.route('/create_admin_account', methods=['POST'])
def create_admin_account():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    initials = data.get('initials')
    
    # Hash the password for secure storage
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            # Use placeholders (%s) for inserting data safely to avoid SQL injection
            cursor.execute("INSERT INTO users (username, password_hash, user_role, initials, is_temp_password) VALUES (%s, %s, 'admin', %s, 0)", (username, hashed_password, initials))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Admin account created successfully!'}), 200
        else:
            return jsonify({'error': 'Failed to connect to the database'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500


@app.route('/create_user', methods=['POST'])
@jwt_required()
def create_user():
    current_user_identity = get_jwt_identity()
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user_role = data.get('role', 'User')  # Default to 'User' if not provided
    is_temp_password = data.get('is_temp_password', True)
    initials = data.get('initials', '')

    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()

            # Directly check if the current user is an admin
            cursor.execute('SELECT user_role FROM users WHERE username = %s', (current_user_identity,))
            user_role_result = cursor.fetchone()
            if not user_role_result or user_role_result[0].lower() != 'admin':
                return jsonify({'error': 'Unauthorized - Admin role required'}), 403

            # Check for username uniqueness
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Username already exists'}), 400
            
            # Create the new user
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('INSERT INTO users (username, password_hash, user_role, is_temp_password, initials) VALUES (%s, %s, %s, %s, %s)',
                           (username, hashed_password, user_role, is_temp_password, initials))
            conn.commit()
            conn.close()
            return jsonify({'message': 'User added successfully'}), 201
        else:
            return jsonify({'error': 'Failed to connect to the database'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500


@app.route('/update_password', methods=['POST'])
@jwt_required()
def update_password():
    data = request.json
    username = data.get('username')
    new_password = data.get('new_password')

    # Hash the new password
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users
                SET password_hash = %s, is_temp_password = 0
                WHERE username = %s
            ''', (hashed_password, username))
            conn.commit()
            conn.close()
            
            if cursor.rowcount == 0:
                # If no rows were updated, the user does not exist
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify({'message': 'Password updated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to connect to the database'}), 500
    except Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/is_admin', methods=['POST'])
def is_admin():
    data = request.json
    username = data.get('username')

    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            # Ensure the query is correctly parameterized to prevent SQL injection
            cursor.execute('SELECT user_role FROM users WHERE username = %s', (username,))
            result = cursor.fetchone()
            conn.close()
            if result is None:
                return jsonify({'error': 'User not found'}), 404
            # Ensure case-insensitive comparison for 'admin' role
            is_admin = result[0].lower() == 'admin'
            return jsonify({'is_admin': is_admin}), 200
        else:
            return jsonify({'error': 'Failed to connect to the database'}), 500
    except Error as e:
        # It's good practice to log the error for debugging purposes
        print(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/validate_login', methods=['POST'])
def validate_login():
    data = request.json  # Get data from POST request
    username = data.get('username')
    password = data.get('password')

    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()

            if user is None:
                return jsonify({'valid': False}), 200

            hashed_password = user[0]
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                # Create a token to return upon successful authentication
                access_token = create_access_token(identity=username)
                return jsonify({'valid': True, 'token': access_token}), 200
            else:
                return jsonify({'valid': False}), 200
        else:
            return jsonify({'error': 'Failed to connect to the database'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500


@app.route('/needs_password_reset', methods=['POST'])
def needs_password_reset():
    data = request.json
    username = data.get('username')
    
    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('SELECT is_temp_password FROM users WHERE username = %s', (username,))
            result = cursor.fetchone()
            conn.close()
            if result is None:
                return jsonify({'error': 'User not found'}), 404  # User not found
            is_temp_password = result[0]
            return jsonify({'needs_reset': bool(is_temp_password)}), 200
        else:
            return jsonify({'error': 'Failed to connect to the database'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500

# --------------------------------- audit_logs Table --------------------------------- #

@app.route('/log_action', methods=['POST'])
def handle_log_action():
    data = request.json
    username = data.get('username')
    activity = data.get('activity')
    description = data.get('description')
    
    if log_action(username, activity, description):
        return jsonify({"message": "Action logged successfully"}), 200
    else:
        return jsonify({"error": "Failed to log action"}), 500


# --------------------------------- residents Table --------------------------------- #

@app.route('/get_resident_count', methods=['GET'])
def get_resident_count():
    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM residents')
            count = cursor.fetchone()[0]
            conn.close()
            return jsonify({'count': count}), 200
        else:
            return jsonify({'error': 'Failed to connect to the database'}), 500
    except Error as e:
        print(f"Database error: {e}") # Log the error for debugging purposes
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
