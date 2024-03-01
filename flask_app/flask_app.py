from flask import Flask, jsonify, request
import logging
from flask_jwt_extended import create_access_token, JWTManager , jwt_required, get_jwt_identity
import mysql.connector
from mysql.connector import Error
import bcrypt
from encryption_utils import encrypt_data, decrypt_data
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Ensure you have a secret key set for JWT to use
app.config['JWT_SECRET_KEY'] = 'fSdas23#%@adY'  # Change this!

jwt = JWTManager(app)  # Initialize Flask-JWT-Extended with your Flask app


# Internal admin check function
def is_user_admin(username):
    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('SELECT user_role FROM users WHERE username = %s', (username,))
            user_role_result = cursor.fetchone()
            conn.close()
            if user_role_result and user_role_result[0].lower() == 'admin':
                return True
    except Error as e:
        print(f"Error checking user role: {e}")
    return False


# Internal function to get resident ID from resident name
def get_resident_id(resident_name):
    conn = None
    try:
        conn = get_db_connection()
        if conn is not None:
            with conn.cursor() as cursor:
                cursor.execute('SELECT id FROM residents WHERE name = %s', (resident_name,))
                result = cursor.fetchone()
                if result:
                    return result[0]  # Extract the ID from the tuple
    except Error as e:
        print(f"Error getting resident ID: {e}")
    finally:
        if conn:
            conn.close()
    return None


# --------------------------------- Database Connection --------------------------------- #

# TODO: Replace the hard-coded credentials with environment variables
def get_db_connection():
    connection = None
    try:
        # connection = mysql.connector.connect(
        #     user='oscar',
        #     password='Discorama619!',
        #     host='10.0.0.53',
        #     database='resident_data'
        # )
        connection = mysql.connector.connect(
            user='oscar',
            password='rir718hhzrthzr',
            host='34.94.226.95',
            database='resident_data'
        )
    except Error as err:
        print(f"Error: '{err}'")
    return connection

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


# Endpoint used in the initial setup to create the first admin account TODO: Remove this endpoint after initial setup or secure it
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
    user_role = data.get('role', 'user')  # Default to 'User' if not provided
    is_temp_password = data.get('is_temp_password', True)
    initials = data.get('initials', '')

    admin_check = is_user_admin(current_user_identity)
    if not admin_check:
        return jsonify({'error': 'Unauthorized - Admin role required'}), 403

    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()

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
        # Log the error for debugging purposes
        print(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/validate_login', methods=['POST'])
def validate_login():
    data = request.json
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


@app.route('/get_user_initials', methods=['GET'])
@jwt_required()
def get_user_initials():
    username = get_jwt_identity()
    conn = None
    try:
        conn = get_db_connection()
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute('SELECT initials FROM users WHERE username = %s', (username,))
            result = cursor.fetchone()
            if result is None:
                return jsonify({'error': 'User not found'}), 404
            return jsonify({'initials': result[0]}), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

# --------------------------------- audit_logs Table --------------------------------- #

def log_action(username, activity, details):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            encrypted_details = encrypt_data(details)
            cursor.execute("INSERT INTO audit_logs (username, activity, details, log_time) VALUES (%s, %s, %s, %s)", 
                           (username, activity, encrypted_details, current_time))
            conn.commit()
            conn.close()
            return True
        else:
            return False
    except Error as e:
        print(f"Database error: {e}")
        return False


@app.route('/log_action', methods=['POST'])
def handle_log_action():
    data = request.json
    username = data.get('username')
    activity = data.get('activity')
    details = data.get('details')
    
    if log_action(username, activity, details):
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


@app.route('/get_resident_names', methods=['GET'])
@jwt_required()
def get_resident_names():
    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM residents')
            names = [row[0] for row in cursor.fetchall()]
            conn.close()
            return jsonify({'names': names}), 200
        else:
            return jsonify({'error': 'Failed to connect to the database'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_resident_care_level', methods=['GET'])
@jwt_required()
def get_resident_care_level():
    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('SELECT name, level_of_care FROM residents')
            results = cursor.fetchall()
            decrypted_results = []
            for row in results:
                try:
                    decrypted_care_level = decrypt_data(row[1])
                except Exception as decrypt_error:
                    print(f"Error decrypting care level for {row[0]}: {decrypt_error}")
                    decrypted_care_level = "Error"  # or use a default value or skip
                decrypted_results.append({'name': row[0], 'level_of_care': decrypted_care_level})
            return jsonify({'residents': decrypted_results}), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()



@app.route('/insert_resident', methods=['POST'])
@jwt_required()
def insert_resident():
    data = request.json
    username = get_jwt_identity()
    name = data.get('name')
    date_of_birth = data.get('date_of_birth')
    level_of_care = data.get('level_of_care')

    admin_check = is_user_admin(username)
    if not admin_check:
        return jsonify({'error': 'Unauthorized - Admin role required'}), 403
    
    encrypted_dob = encrypt_data(date_of_birth)
    encrypted_level_of_care = encrypt_data(level_of_care)

    try :
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO residents (name, date_of_birth, level_of_care) VALUES (%s, %s, %s)', (name, encrypted_dob, encrypted_level_of_care))
            conn.commit()
            conn.close()
            log_action(username, 'Resident Added', f'Resident Added {name}')
            return jsonify({'message': 'Resident added successfully'}), 201
        else:
            return jsonify({'error': 'Failed to connect to the database'}), 500
    except Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500


# --------------------------------- adl_chart Table --------------------------------- #

@app.route('/fetch_adl_data_for_resident/<resident_name>', methods=['GET'])
@jwt_required()
def fetch_adl_data_for_resident(resident_name):
    today = datetime.now().strftime("%Y-%m-%d")
    resident_id = get_resident_id(resident_name)

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT * FROM adl_chart
                WHERE resident_id = %s AND chart_date = %s
            ''', (resident_id, today))
            result = cursor.fetchone()
            if result:
                columns = [col[0] for col in cursor.description]
                adl_data = {columns[i]: result[i] for i in range(3, len(columns))}
                return jsonify(adl_data), 200
            else:
                # Instead of returning an error, return an empty dictionary
                return jsonify({}), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500


@app.route('/fetch_adl_chart_data_for_month/<resident_name>', methods=['GET'])
@jwt_required()
def fetch_adl_chart_data_for_month(resident_name):
    # Extract 'year_month' from query parameters
    year_month = request.args.get('year_month', '')
    # Validate 'year_month' format
    try:
        datetime.strptime(year_month, "%Y-%m")
    except ValueError:
        return jsonify({'error': 'Invalid year_month format. Use YYYY-MM.'}), 400

    resident_id = get_resident_id(resident_name)
    if not resident_id:
        return jsonify({'error': 'Resident not found'}), 404

    print('resident_id:', resident_id, 'year_month:', year_month)

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Adjust SQL query for MySQL and use LIKE for partial date matching
            cursor.execute('''
                SELECT * FROM adl_chart
                WHERE resident_id = %s AND DATE_FORMAT(chart_date, '%Y-%m') = %s
                ORDER BY chart_date
            ''', (resident_id, year_month))
            results = cursor.fetchall()
            if results:
                columns = [col[0] for col in cursor.description]
                # Convert each row into a dictionary
                adl_data = [{columns[i]: row[i] for i in range(len(columns))} for row in results]
                return jsonify(adl_data), 200
            else:
                return jsonify([]), 200  # Return an empty list if no data found
    except Error as e:
        return jsonify({'error': str(e)}), 500


# @app.route('/fetch_adl_chart_data_for_month/<resident_name>', methods=['GET'])
# @jwt_required()
# def fetch_adl_chart_data_for_month(resident_name):
#     year_month = request.args.get('year_month', '')

#     # Validate 'year_month' format
#     try:
#         datetime.strptime(year_month, "%Y-%m")
#     except ValueError:
#         return jsonify({'error': 'Invalid year_month format. Use YYYY-MM.'}), 400

#     resident_id = get_resident_id(resident_name)
#     if not resident_id:
#         return jsonify({'error': 'Resident not found'}), 404

#     # Log the parameters to debug the execution
#     logging.debug("Querying ADL chart data for resident_id: %s, year_month: %s", resident_id, year_month)

#     try:
#         conn = get_db_connection()
#         query = """
#             SELECT * FROM adl_chart
#             WHERE resident_id = %s AND DATE_FORMAT(chart_date, '%Y-%m') = %s
#             ORDER BY chart_date
#         """
#         # Log the exact query being sent to MySQL
#         logging.debug("Executing query: %s with parameters: resident_id=%s, year_month=%s", query, resident_id, year_month)
        
#         with conn.cursor() as cursor:
#             cursor.execute(query, (resident_id, year_month))
#             results = cursor.fetchall()

#             if results:
#                 columns = [col[0] for col in cursor.description]
#                 adl_data = [{columns[i]: row[i] for i in range(len(columns))} for row in results]
#                 return jsonify(adl_data), 200
#             else:
#                 # Log if no data found
#                 logging.debug("No ADL chart data found for resident_id: %s, year_month: %s", resident_id, year_month)
#                 return jsonify([]), 200
#     except Exception as e:
#         logging.error("Error fetching ADL chart data: %s", str(e))
#         return jsonify({'error': str(e)}), 500


@app.route('/save_adl_data_from_management_window', methods=['POST'])
@jwt_required()
def save_adl_data_from_management_window():
    # Assuming you're receiving JSON data including the resident_name and adl_data
    request_data = request.get_json()
    resident_name = request_data['resident_name']
    adl_data = request_data['adl_data']
    audit_description = request_data['audit_description']
    
    # Convert empty strings to None (or a default value) for integer fields
    integer_fields = ['breakfast', 'lunch', 'dinner', 'snack_am', 'snack_pm', 'water_intake']
    for field in integer_fields:
        if adl_data.get(field, '') == '':
            adl_data[field] = None  # or use a default value like 0


    resident_id = get_resident_id(resident_name)
    today = datetime.now().strftime("%Y-%m-%d")

    if resident_id is None:
        return jsonify({'error': 'Resident not found'}), 404

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            
            sql = '''
                INSERT INTO adl_chart (resident_id, chart_date, first_shift_sp, second_shift_sp, 
                first_shift_activity1, first_shift_activity2, first_shift_activity3, second_shift_activity4, 
                first_shift_bm, second_shift_bm, shower, shampoo, sponge_bath, peri_care_am, 
                peri_care_pm, oral_care_am, oral_care_pm, nail_care, skin_care, shave, 
                breakfast, lunch, dinner, snack_am, snack_pm, water_intake)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                first_shift_sp = VALUES(first_shift_sp), second_shift_sp = VALUES(second_shift_sp), 
                first_shift_activity1 = VALUES(first_shift_activity1), first_shift_activity2 = VALUES(first_shift_activity2),
                first_shift_activity3 = VALUES(first_shift_activity3), second_shift_activity4 = VALUES(second_shift_activity4),
                first_shift_bm = VALUES(first_shift_bm), second_shift_bm = VALUES(second_shift_bm), shower = VALUES(shower),
                shampoo = VALUES(shampoo), sponge_bath = VALUES(sponge_bath), peri_care_am = VALUES(peri_care_am), 
                peri_care_pm = VALUES(peri_care_pm), oral_care_am = VALUES(oral_care_am), oral_care_pm = VALUES(oral_care_pm),
                nail_care = VALUES(nail_care), skin_care = VALUES(skin_care), shave = VALUES(shave), breakfast = VALUES(breakfast),
                lunch = VALUES(lunch), dinner = VALUES(dinner), snack_am = VALUES(snack_am), snack_pm = VALUES(snack_pm),
                water_intake = VALUES(water_intake)
            '''

            data_tuple = (
                resident_id, 
                today,
                adl_data.get('first_shift_sp', ''),
                adl_data.get('second_shift_sp', ''),
                adl_data.get('first_shift_activity1', ''),
                adl_data.get('first_shift_activity2', ''),
                adl_data.get('first_shift_activity3', ''),
                adl_data.get('second_shift_activity4', ''),
                adl_data.get('first_shift_bm', ''),
                adl_data.get('second_shift_bm', ''),
                adl_data.get('shower', ''),
                adl_data.get('shampoo', ''),
                adl_data.get('sponge_bath', ''),
                adl_data.get('peri_care_am', ''),
                adl_data.get('peri_care_pm', ''),
                adl_data.get('oral_care_am', ''),
                adl_data.get('oral_care_pm', ''),
                adl_data.get('nail_care', ''),
                adl_data.get('skin_care', ''),
                adl_data.get('shave', ''),
                adl_data.get('breakfast', ''),
                adl_data.get('lunch', ''),
                adl_data.get('dinner', ''),
                adl_data.get('snack_am', ''),
                adl_data.get('snack_pm', ''),
                adl_data.get('water_intake', '')
            )
            cursor.execute(sql, data_tuple)
            conn.commit()
            log_action(get_jwt_identity(), 'ADL Data Saved', audit_description)
            return jsonify({'message': 'ADL data saved successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# --------------------------------- Test Endpoints --------------------------------- #

@app.route('/test_fetch_adl_chart_data', methods=['GET'])
def test_fetch_adl_chart_data():
    try:
        conn = get_db_connection()  # Ensure this uses your existing DB connection function
        with conn.cursor(dictionary=True) as cursor:  # Using dictionary=True for convenience
            # Hard-coded query for testing
            query = '''
                SELECT * FROM adl_chart
                WHERE resident_id = 1 AND DATE_FORMAT(chart_date, '%Y-%m') = '2024-02'
                ORDER BY chart_date
            '''
            cursor.execute(query)
            results = cursor.fetchall()

            if results:
                return jsonify(results), 200
            else:
                return jsonify([]), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
