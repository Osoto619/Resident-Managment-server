from flask import Flask, jsonify
import mysql.connector
from mysql.connector import Error

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

@app.route('/test_db')
def test_db():
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({'message': 'Connection successful! 🎉'}), 200
    else:
        return jsonify({'error': 'Failed to connect to the database'}), 500

if __name__ == '__main__':
    app.run(debug=True)
