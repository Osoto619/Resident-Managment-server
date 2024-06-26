import sqlite3


def fetch_resident_information(resident_name):
    """Fetch and decrypt a resident's information from the database."""
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, date_of_birth FROM residents WHERE name = ?", (resident_name,))
        result = cursor.fetchone()
        if result:
            name, encrypted_date_of_birth = result
            decrypted_date_of_birth = decrypt_data(encrypted_date_of_birth)  # Assuming decrypt_data is already defined
            return {'name': name, 'date_of_birth': decrypted_date_of_birth}
        else:
            return None


def update_resident_info(old_name, new_name, new_dob):
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE residents SET name = ?, date_of_birth = ? WHERE name = ?", (new_name, new_dob, old_name))
        conn.commit()


def remove_resident(resident_name):
    """ Removes a resident from the database. """
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM residents WHERE name = ?', (resident_name,))
        conn.commit()


def remove_medication(medication_name, resident_name):
    resident_id = get_resident_id(resident_name)
    # Connect to the database
    conn = sqlite3.connect('resident_data.db')
    c = conn.cursor()

    try:
        # Start a transaction
        conn.execute('BEGIN')

        # Get the medication ID
        c.execute('SELECT id FROM medications WHERE medication_name = ? AND resident_id = ?', (medication_name, resident_id))
        medication_id = c.fetchone()
        if medication_id:
            medication_id = medication_id[0]

            # Delete related entries from medication_time_slots
            c.execute('DELETE FROM medication_time_slots WHERE medication_id = ?', (medication_id,))

            # Delete related entries from emar_chart
            c.execute('DELETE FROM emar_chart WHERE medication_id = ?', (medication_id,))

            # Finally, delete the medication itself
            c.execute('DELETE FROM medications WHERE id = ?', (medication_id,))

        # Commit the transaction
        conn.commit()
        log_action(config.global_config['logged_in_user'], 'Medication Deleted', f'{medication_name} removed')
        print(f"Medication '{medication_name}' and all related data successfully removed.")
    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        print(f"Error removing medication: {e}")
    finally:
        # Close the connection
        conn.close()


def fetch_medication_details(medication_name, resident_id):
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT medication_name, dosage, instructions FROM medications WHERE medication_name = ? AND resident_id = ?", (medication_name, resident_id))
        result = cursor.fetchone()
        if result:
            return {'medication_name': result[0], 'dosage': result[1], 'instructions': result[2]}
        else:
            return None


def update_medication_details(old_name, resident_id, new_name, new_dosage, new_instructions):
    with sqlite3.connect('resident_data.db') as conn:
        encrypted_new_dosage = encrypt_data(new_dosage)
        encrypted_new_instructions = encrypt_data(new_instructions)
        cursor = conn.cursor()
        cursor.execute("UPDATE medications SET medication_name = ?, dosage = ?, instructions = ? WHERE medication_name = ? AND resident_id = ?", (new_name, encrypted_new_dosage, encrypted_new_instructions, old_name, resident_id))
        conn.commit()


def get_controlled_medication_count_and_form(resident_name, medication_name):
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()

        # Fetch the resident ID based on the resident's name
        cursor.execute("SELECT id FROM residents WHERE name = ?", (resident_name,))
        resident_id_result = cursor.fetchone()
        if resident_id_result is None:
            return None, None  # Resident not found
        resident_id = resident_id_result[0]

        # Fetch the count and form for the specified controlled medication
        cursor.execute('''
            SELECT count, medication_form FROM medications 
            WHERE resident_id = ? AND medication_name = ? AND medication_type = 'Controlled'
        ''', (resident_id, medication_name))
        result = cursor.fetchone()
        if result is None:
            return None, None  # Medication not found or not a controlled type

        medication_count, medication_form = result
        return medication_count, medication_form  # Return the count and form


def save_controlled_administration_data(resident_name, medication_name, admin_data, new_count):
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()

        # Retrieve resident ID and medication ID
        cursor.execute("SELECT id FROM residents WHERE name = ?", (resident_name,))
        resident_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM medications WHERE medication_name = ? AND resident_id = ?", (medication_name, resident_id))
        medication_id = cursor.fetchone()[0]

        # Insert administration data into emar_chart, including the new count
        cursor.execute('''
            INSERT INTO emar_chart (resident_id, medication_id, date, administered, notes, current_count)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (resident_id, medication_id, admin_data['datetime'], admin_data['initials'], admin_data['notes'], new_count))

        # Update medication count in medications table
        cursor.execute('''
            UPDATE medications
            SET count = ?
            WHERE id = ?
        ''', (new_count, medication_id))

        conn.commit()


def discontinue_medication(resident_name, medication_name, discontinued_date):
    # Get the resident's ID
    resident_id = get_resident_id(resident_name)
    if resident_id is not None:
        with sqlite3.connect('resident_data.db') as conn:
            cursor = conn.cursor()

            # Update the medication record with the discontinued date
            cursor.execute('''
                UPDATE medications 
                SET discontinued_date = ? 
                WHERE resident_id = ? AND medication_name = ? AND (discontinued_date IS NULL OR discontinued_date = '')
            ''', (discontinued_date, resident_id, medication_name))
            
            conn.commit()


def filter_active_medications(medication_names, resident_name):
    active_medications = []

    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()

        for med_name in medication_names:
            cursor.execute('''
                SELECT discontinued_date FROM medications
                JOIN residents ON medications.resident_id = residents.id
                WHERE residents.name = ? AND medications.medication_name = ?
            ''', (resident_name, med_name))
            result = cursor.fetchone()

            # Check if the medication is discontinued and if the discontinuation date is past the current date
            if result is None or (result[0] is None or datetime.now().date() < datetime.strptime(result[0], '%Y-%m-%d').date()):
                active_medications.append(med_name)

    return active_medications


def fetch_discontinued_medications(resident_name):
    """
    Fetches the names and discontinuation dates of discontinued medications for a given resident.

    :param resident_name: Name of the resident.
    :return: A dictionary with medication names as keys and discontinuation dates as values.
    """
    discontinued_medications = {}

    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()

        # Fetch the resident's ID
        cursor.execute("SELECT id FROM residents WHERE name = ?", (resident_name,))
        resident_id_result = cursor.fetchone()
        if resident_id_result is None:
            return discontinued_medications  # Resident not found
        resident_id = resident_id_result[0]

        # Fetch discontinued medications
        cursor.execute('''
            SELECT medication_name, discontinued_date FROM medications 
            WHERE resident_id = ? AND discontinued_date IS NOT NULL
        ''', (resident_id,))

        for medication_name, discontinued_date in cursor.fetchall():
            decrypted_medication_name = decrypt_data(medication_name) if medication_name else medication_name
            if discontinued_date:  # Ensure there is a discontinuation date
                discontinued_medications[decrypted_medication_name] = discontinued_date

    return discontinued_medications


def save_non_medication_order(resident_id, order_name, frequency, specific_days, special_instructions):
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()
        
        # Prepare the frequency and specific_days values for insertion
        # If specific_days is not empty, set frequency to None
        if specific_days:  # Assuming specific_days is a comma-separated string like 'Mon,Wed,Fri'
            frequency_value = None  # No frequency because specific days are provided
        else:
            frequency_value = frequency  # Use the frequency as provided
            specific_days = None  # No specific days because frequency is used

        # Insert the non-medication order into the database
        cursor.execute('''
            INSERT INTO non_medication_orders (resident_id, order_name, frequency, specific_days, special_instructions)
            VALUES (?, ?, ?, ?, ?)
        ''', (resident_id, order_name, frequency_value, specific_days, special_instructions))

        conn.commit()


def update_non_med_order_details(order_name, resident_id, new_order_name, new_instructions):
    """
    Updates the details of a non-medication order for a specific resident.
    
    Parameters:
        order_name (str): The current name of the order.
        resident_id (int): The ID of the resident to whom the order belongs.
        new_order_name (str): The new name for the order.
        new_instructions (str): The new special instructions for the order.
    """
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()

        # Prepare the SQL statement for updating the order details.
        # This statement updates the order's name and special instructions
        # only if the new values are provided (not empty).
        sql = """
        UPDATE non_medication_orders
        SET order_name = COALESCE(NULLIF(?, ''), order_name),
            special_instructions = COALESCE(NULLIF(?, ''), special_instructions)
        WHERE order_name = ? AND resident_id = ?
        """

        # Execute the SQL statement with the new values and the original order name and resident ID.
        cursor.execute(sql, (new_order_name, new_instructions, order_name, resident_id))
        
        # Commit the transaction to save changes.
        conn.commit()
        
        if cursor.rowcount == 0:
            # If no rows were updated, it could mean the order name/resident ID didn't match.
            print("No order was updated. Please check the order name and resident ID.")
        else:
            log_action(config.global_config['logged_in_user'], 'Non-Medication Order Updated', f'{order_name} updated for {resident_id}')


def remove_non_med_order(order_name, resident_name):
    """
    Removes a non-medication order for a specific resident.
    
    Parameters:
        order_name (str): The name of the non-medication order to be removed.
        resident_name (str): The name of the resident from whom the order is to be removed.
    """
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()

        # First, get the resident ID for the given resident name to ensure accuracy
        cursor.execute("SELECT id FROM residents WHERE name = ?", (resident_name,))
        resident_result = cursor.fetchone()
        
        if resident_result is None:
            print(f"No resident found with the name {resident_name}.")
            return

        resident_id = resident_result[0]

        # Prepare the SQL statement for deleting the non-medication order
        sql = """
        DELETE FROM non_medication_orders
        WHERE order_name = ? AND resident_id = ?
        """

        # Execute the SQL statement with the order name and resident ID
        cursor.execute(sql, (order_name, resident_id))
        
        # Commit the transaction to save changes
        conn.commit()
        
        if cursor.rowcount == 0:
            # If no rows were deleted, it means the order name/resident ID didn't match any record
            print("No non-medication order was removed. Please check the order name and resident name.")
        else:
            log_action(config.global_config['logged_in_user'], 'Non-Medication Order Removed', f'{order_name} removed for {resident_name}')


def fetch_administrations_for_order(order_id, month, year):
    # Connect to the SQLite database
    conn = sqlite3.connect('resident_data.db')
    cursor = conn.cursor()

    # Update the query to include the initials field
    query = """
    SELECT administration_date, notes, initials
    FROM non_med_order_administrations
    WHERE order_id = ? AND strftime('%m', administration_date) = ? AND strftime('%Y', administration_date) = ?
    ORDER BY administration_date ASC
    """

    # Execute the query
    cursor.execute(query, (order_id, month.zfill(2), year))

    # Fetch and format the results, now including initials
    results = cursor.fetchall()
    formatted_results = [[datetime.strptime(row[0], '%Y-%m-%d').strftime('%b %d, %Y'), row[1], row[2]] for row in results]

    # Close the database connection
    conn.close()

    return formatted_results


def record_non_med_order_performance(order_name, resident_id, notes, user_initials):
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()

        # Step 1: Look up the order_id
        cursor.execute('''
            SELECT order_id FROM non_medication_orders
            WHERE order_name = ? AND resident_id = ?
        ''', (order_name, resident_id))
        order_result = cursor.fetchone()
        if not order_result:
            print("Order not found.")
            return
        order_id = order_result[0]

        # Step 2: Insert a new record into the non_med_order_administrations table with initials
        current_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO non_med_order_administrations (order_id, resident_id, administration_date, notes, initials)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, resident_id, current_date, notes, user_initials))

        # Step 3: Update the last_administered_date for the order
        cursor.execute('''
            UPDATE non_medication_orders
            SET last_administered_date = ?
            WHERE order_id = ?
        ''', (current_date, order_id))

        conn.commit()
        log_action(config.global_config['logged_in_user'], 'Non-Medication Order Administered', f'{order_name} administered for {resident_id}')


ADL_KEYS = [
                "first_shift_sp", "second_shift_sp", "first_shift_activity1", "first_shift_activity2",
                "first_shift_activity3", "second_shift_activity4", "first_shift_bm", "second_shift_bm",
                "shower", "shampoo", "sponge_bath", "peri_care_am", "peri_care_pm", "oral_care_am", "oral_care_pm",
                "nail_care", "skin_care", "shave", "breakfast", "lunch", "dinner", "snack_am",
                "snack_pm", "water_intake"]



def fetch_adl_chart_data_for_month(resident_name, year_month):
    # year_month should be in the format 'YYYY-MM'
    resident_id = get_resident_id(resident_name)
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM adl_chart
            WHERE resident_id = ? AND strftime('%Y-%m', date) = ?
            ORDER BY date
        ''', (resident_id, year_month))
        return cursor.fetchall()


def save_adl_data_from_chart_window(resident_name, year_month, window_values):
    resident_id = get_resident_id(resident_name)
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()
        # Define the number of days
        num_days = 31

        # Loop over each day of the month
        for day in range(1, num_days + 1):
            # Extract values for each ADL key for the day
            adl_data = [window_values[f'-{key}-{day}-'] for key in ADL_KEYS]
            
            # Construct the date string for the specific day
            date_str = f"{year_month}-{str(day).zfill(2)}"
            
            # Prepare the SQL statement
            sql = '''
                INSERT INTO adl_chart (resident_id, date, first_shift_sp, second_shift_sp, 
                first_shift_activity1, first_shift_activity2, first_shift_activity3, second_shift_activity4, 
                first_shift_bm, second_shift_bm, shower, shampoo, sponge_bath, peri_care_am, 
                peri_care_pm, oral_care_am, oral_care_pm, nail_care, skin_care, shave, 
                breakfast, lunch, dinner, snack_am, snack_pm, water_intake)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(resident_id, date) DO UPDATE SET
                first_shift_sp = excluded.first_shift_sp, second_shift_sp = excluded.second_shift_sp, 
                first_shift_activity1 = excluded.first_shift_activity1, first_shift_activity2 = excluded.first_shift_activity2,
                first_shift_activity3 = excluded.first_shift_activity3, second_shift_activity4 = excluded.second_shift_activity4,
                first_shift_bm = excluded.first_shift_bm, second_shift_bm = excluded.second_shift_bm, shower = excluded.shower,
                shampoo = excluded.shampoo,sponge_bath = excluded.sponge_bath, peri_care_am = excluded.peri_care_am, 
                peri_care_pm = excluded.peri_care_pm, oral_care_am = excluded.oral_care_am, oral_care_pm = excluded.oral_care_pm,
                nail_care = excluded.nail_care, skin_care = excluded.skin_care, shave = excluded.shave, breakfast = excluded.breakfast,
                lunch = excluded.lunch, dinner = excluded.dinner, snack_am = excluded.snack_am, snack_pm = excluded.snack_pm,
                water_intake = excluded.water_intake
            '''
            
            # Execute the SQL statement
            cursor.execute(sql, (resident_id, date_str, *adl_data))
            
        # Commit the changes to the database
        conn.commit()


def save_prn_administration_data(resident_name, medication_name, admin_data):
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()

        # Retrieve resident ID and medication ID
        cursor.execute("SELECT id FROM residents WHERE name = ?", (resident_name,))
        resident_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM medications WHERE medication_name = ? AND resident_id = ?", (medication_name, resident_id))
        medication_id = cursor.fetchone()[0]

        # Insert administration data into emar_chart
        cursor.execute('''
            INSERT INTO emar_chart (resident_id, medication_id, date, administered, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (resident_id, medication_id, admin_data['datetime'], admin_data['initials'], admin_data['notes']))

        conn.commit()


def save_emar_data_from_chart_window(resident_name, year_month, window_values):
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()
        num_days = 31

        for day in range(1, num_days + 1):
            date_str = f"{year_month}-{str(day).zfill(2)}"
            
            for key, value in window_values.items():
                if key.startswith('-') and key.endswith(f'-{day}-'):
                    # Extract medication name and time slot from the key
                    parts = key.strip('-').split('_')
                    medication_name = '_'.join(parts[:-1])  # Rejoin all parts except the last one
                    time_slot = parts[-1].split('-')[0]

                    sql = '''
                        INSERT INTO emar_chart (resident_id, medication_id, date, time_slot, administered)
                        SELECT residents.id, medications.id, ?, ?, ?
                        FROM residents, medications
                        WHERE residents.name = ? AND medications.medication_name = ?
                        ON CONFLICT(resident_id, medication_id, date, time_slot) DO UPDATE SET
                        administered = excluded.administered
                    '''
                    cursor.execute(sql, (date_str, time_slot, value, resident_name, medication_name))

        conn.commit()


def fetch_current_emar_data_for_resident_date(resident_name, date):
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT m.medication_name, ec.time_slot, ec.administered, ec.date
                          FROM emar_chart ec
                          JOIN residents r ON ec.resident_id = r.id
                          JOIN medications m ON ec.medication_id = m.id
                          WHERE r.name = ? AND ec.date = ?''', (resident_name, date))
        rows = cursor.fetchall()
        return [{'resident_name': resident_name, 'medication_name': row[0], 'time_slot': row[1], 'administered': row[2], 'date': row[3]} for row in rows]


def save_emar_data_from_management_window(emar_data):
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()

        for entry in emar_data:
            # Fetch the resident_id
            cursor.execute("SELECT id FROM residents WHERE name = ?", (entry['resident_name'],))
            resident_id_result = cursor.fetchone()
            if resident_id_result is None:
                continue  # Skip if resident not found
            resident_id = resident_id_result[0]

            # Fetch medication_id based on resident_id and unencrypted medication_name
            cursor.execute("SELECT id FROM medications WHERE resident_id = ? AND medication_name = ?", (resident_id, entry['medication_name']))
            medication_id_result = cursor.fetchone()
            if medication_id_result is None:
                continue  # Skip if medication not found
            medication_id = medication_id_result[0]

            # Insert or update emar_chart data
            cursor.execute('''
                INSERT INTO emar_chart (resident_id, medication_id, date, time_slot, administered)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(resident_id, medication_id, date, time_slot) 
                DO UPDATE SET administered = excluded.administered
            ''', (resident_id, medication_id, entry['date'], entry['time_slot'], entry['administered']))

        conn.commit()


def fetch_emar_data_for_month(resident_name, year_month):
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()
        # Query to fetch eMAR data for the given month and resident
        cursor.execute('''
            SELECT m.medication_name, e.date, e.time_slot, e.administered
            FROM emar_chart e
            JOIN residents r ON e.resident_id = r.id
            JOIN medications m ON e.medication_id = m.id
            WHERE r.name = ? AND strftime('%Y-%m', e.date) = ?
        ''', (resident_name, year_month))
        return cursor.fetchall()


def fetch_prn_data_for_day(event_key, resident_name, year_month):
    _, med_name, day, _ = event_key.split('-')
    parts = med_name.split('_')
    med_name = parts[1] 
    day = day.zfill(2)  # Ensure day is two digits
    date_query = f'{year_month}-{day}'

    # Debugging: Print the values
    # print(f"Medication Name: {med_name}, Date Query: {date_query}")

    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()
        query = '''
            SELECT e.date, e.administered, e.notes
            FROM emar_chart e
            JOIN residents r ON e.resident_id = r.id
            JOIN medications m ON e.medication_id = m.id
            WHERE r.name = ? AND m.medication_name = ? AND e.date LIKE ?
        '''
        cursor.execute(query, (resident_name, med_name, date_query + '%'))
        result = cursor.fetchall()
    
        return result


def fetch_controlled_data_for_day(event_key, resident_name, year_month):
    _, med_name, day, _ = event_key.split('-')
    parts = med_name.split('_')
    med_name = parts[1] 
    day = day.zfill(2)  # Ensure day is two digits
    date_query = f'{year_month}-{day}'

    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.date, e.administered, e.notes, e.current_count
            FROM emar_chart e
            JOIN residents r ON e.resident_id = r.id
            JOIN medications m ON e.medication_id = m.id
            WHERE r.name = ? AND m.medication_name = ? AND e.date LIKE ? AND m.medication_type = 'Controlled'
        ''', (resident_name, med_name, date_query + '%'))
        return cursor.fetchall()


def fetch_monthly_medication_data(resident_name, medication_name, year_month, medication_type):
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()

        resident_id = get_resident_id(resident_name)

        # Fetch medication ID
        cursor.execute("SELECT id FROM medications WHERE medication_name = ? AND resident_id = ?", (medication_name, resident_id))
        medication_id_result = cursor.fetchone()
        if not medication_id_result:
            return []  # Medication not found
        medication_id = medication_id_result[0]

        # Query for the entire month
        year, month = year_month.split('-')
        start_date = f"{year}-{month}-01"
        end_date = f"{year}-{month}-{calendar.monthrange(int(year), int(month))[1]}"

        if medication_type == 'Control':
            # For Controlled medications, include count information
            cursor.execute('''
                SELECT date, administered, notes, current_count
                FROM emar_chart
                WHERE resident_id = ? AND medication_id = ? AND date BETWEEN ? AND ?
                ORDER BY date
            ''', (resident_id, medication_id, start_date, end_date))
        else:
            # For PRN medications
            cursor.execute('''
                SELECT date, administered, notes
                FROM emar_chart
                WHERE resident_id = ? AND medication_id = ? AND date BETWEEN ? AND ?
                ORDER BY date
            ''', (resident_id, medication_id, start_date, end_date))

        return cursor.fetchall()


def does_emars_chart_data_exist(resident_name, year_month):
    with sqlite3.connect('resident_data.db') as conn:
        cursor = conn.cursor()
        # Query to check if there is any eMAR chart data for the resident in the given month
        cursor.execute('''
            SELECT EXISTS(
                SELECT 1 FROM emar_chart
                JOIN residents ON emar_chart.resident_id = residents.id
                WHERE residents.name = ? AND strftime('%Y-%m', emar_chart.date) = ?
            )
        ''', (resident_name, year_month))
        return cursor.fetchone()[0] == 1

