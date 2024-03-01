import sqlite3


def initialize_database():
    # Connect to SQLite database
    # The database file will be 'resident_data.db'
    conn = sqlite3.connect('resident_data.db')
    c = conn.cursor()

    # Create residents table
    # CREATE TABLE IF NOT EXISTS users (
    # user_id INT AUTO_INCREMENT PRIMARY KEY,
    # username VARCHAR(255) UNIQUE NOT NULL,
    # password_hash VARCHAR(255) NOT NULL,
    # user_role VARCHAR(255) NOT NULL,
    # initials VARCHAR(255),
    # is_temp_password TINYINT(1) DEFAULT 1
    # )

    # Create table for data backup values
    c.execute('''CREATE TABLE IF NOT EXISTS backup_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_folder TEXT NOT NULL,
    backup_frequency TEXT NOT NULL,
    last_backup_date TEXT)''')

    # Create table for audit_logs
# CREATE TABLE IF NOT EXISTS audit_logs (
#     log_id INT AUTO_INCREMENT PRIMARY KEY,
#     username VARCHAR(255),
#     activity VARCHAR(255),
#     details TEXT,                   # CHANGED FROM DESCRIPTION TO DETAILS
#     log_time DATETIME DEFAULT CURRENT_TIMESTAMP
# )



    # Create table for user settings
    c.execute('''CREATE TABLE IF NOT EXISTS user_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_name TEXT UNIQUE,
        setting_value TEXT)''')

    # Create residents table
    # '''
    #     CREATE TABLE IF NOT EXISTS residents (
    #         id INT AUTO_INCREMENT PRIMARY KEY,
    #         name VARCHAR(255),
    #         date_of_birth DATE,
    #         level_of_care VARCHAR(255)
    #     );
    #     '''

    # Create Time Slots table
    c.execute('''CREATE TABLE IF NOT EXISTS time_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_name TEXT UNIQUE)''')

    # Populate Time Slots table with standard slots
    time_slots = ['Morning', 'Noon', 'Evening', 'Night']
    for slot in time_slots:
        c.execute('INSERT INTO time_slots (slot_name) VALUES (?) ON CONFLICT(slot_name) DO NOTHING', (slot,))

    # Create medications table
    c.execute('''CREATE TABLE IF NOT EXISTS medications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER,
        medication_name TEXT,
        dosage TEXT,
        instructions TEXT,
        medication_type TEXT DEFAULT 'Scheduled',
        medication_form TEXT DEFAULT 'Pill',
        count INTEGER DEFAULT NULL,
        discontinued_date DATE DEFAULT NULL,
        FOREIGN KEY(resident_id) REFERENCES residents(id))''')

    # Create medication_time_slots
    c.execute('''CREATE TABLE IF NOT EXISTS medication_time_slots (
        medication_id INTEGER,
        time_slot_id INTEGER,
        FOREIGN KEY(medication_id) REFERENCES medications(id),
        FOREIGN KEY(time_slot_id) REFERENCES time_slots(id),
        PRIMARY KEY (medication_id, time_slot_id))''')

    # Create Non-Medication Orders Table
    c.execute('''CREATE TABLE IF NOT EXISTS non_medication_orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER,
        order_name TEXT NOT NULL,
        frequency INTEGER,
        specific_days TEXT,
        special_instructions TEXT,
        discontinued_date DATE DEFAULT NULL,
        last_administered_date DATE DEFAULT NULL,
        FOREIGN KEY(resident_id) REFERENCES residents(id))''')

    # Create eMARS Chart Table
    c.execute('''CREATE TABLE IF NOT EXISTS emar_chart (
        chart_id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER,
        medication_id INTEGER,
        date TEXT,
        time_slot TEXT,
        administered TEXT,
        current_count INTEGER DEFAULT NULL,
        notes TEXT DEFAULT '',
        FOREIGN KEY(resident_id) REFERENCES residents(id),
        FOREIGN KEY(medication_id) REFERENCES medications(id),
        UNIQUE(resident_id, medication_id, date, time_slot))''')

    # Create Non-Medication Administrations Table
    c.execute('''CREATE TABLE IF NOT EXISTS non_med_order_administrations (
                administration_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                resident_id INTEGER,
                administration_date DATE,
                notes TEXT DEFAULT '',
                initials TEXT,
                FOREIGN KEY(order_id) REFERENCES non_medication_orders(order_id),
                FOREIGN KEY(resident_id) REFERENCES residents(id))''')
    
    # Create ADL Chart Table
#     create table if not exists adl_chart (
# 	chart_id int auto_increment primary key,
#     resident_id int,
#     chart_date date,
#     first_shift_sp varchar(100),
#     second_shift_sp varchar(100),
#     first_shift_activity1 varchar(100),
#     first_shift_activity2 varchar(100),
#     first_shift_activity3 varchar(100),
#     second_shift_activity4 varchar(100),
#     first_shift_bm varchar(100),
#     second_shift_bm varchar(100),
#     shower varchar(100),
#     shampoo varchar(100),
#     sponge_bath varchar(100),
#     peri_care_am varchar(100),
#     peri_care_pm varchar(100),
#     oral_care_am varchar(100),
#     oral_care_pm varchar(100),
#     nail_care varchar(100),
#     skin_care varchar(100),
#     shave varchar(100),
#     breakfast tinyint,
#     lunch tinyint,
#     dinner tinyint,
#     snack_am tinyint,
#     snack_pm tinyint,
#     water_intake tinyint,
#     foreign key (resident_id) references residents(id),
#     unique (resident_id, chart_date)
# )
# engine=InnoDB;

    conn.commit()
    conn.close()