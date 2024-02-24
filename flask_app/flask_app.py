from flask import Flask, jsonify, request
import mysql.connector
from mysql.connector import Error
import bcrypt
from encryption_utils import encrypt_data
from datetime import datetime

app = Flask(__name__)

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


# def log_action(username, activity, description):
#     current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
#     try:
#         conn = get_db_connection()
#         if conn is not None:
#             cursor = conn.cursor()
#             encrypted_description = encrypt_data(description)
#             cursor.execute("INSERT INTO audit_logs (username, activity, description, log_time) VALUES (%s, %s, %s, %s)", 
#                            (username, activity, encrypted_description, current_time))
#             conn.commit()
#             conn.close()
#             return True
#         else:
#             return False
#     except Error as e:
#         print(f"Database error: {e}")
#         return False

    
@app.route('/is_first_time_setup')
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
                return jsonify({'valid': True}), 200
            else:
                return jsonify({'valid': False}), 200
        else:
            return jsonify({'error': 'Failed to connect to the database'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500


# @app.route('/log_action', methods=['POST'])
# def handle_log_action():
#     data = request.json
#     username = data.get('username')
#     activity = data.get('activity')
#     description = data.get('description')
    
#     if log_action(username, activity, description):
#         return jsonify({"message": "Action logged successfully"}), 200
#     else:
#         return jsonify({"error": "Failed to log action"}), 500


if __name__ == '__main__':
    app.run(debug=True)
