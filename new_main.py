import PySimpleGUI as sg
import api_functions
import keyring
import resident_management
from datetime import datetime, timedelta, date
from tkinter import font
import sys
import config
import calendar
from pdf import create_menu, create_calendar
import tracker_reminder
import threading
import queue
from progress_bar import show_progress_bar, show_loading_window, show_loading_window_for_meals

API_URL = config.API_URL

# Function to load and apply the user's font and theme settings
def apply_user_settings():
    user_settings = api_functions.get_user_preferences(API_URL)
    config.global_config['theme'] = user_settings['theme']
    config.global_config['font'] = user_settings['font']
    sg.theme(user_settings['theme'])


# Apply user theme at application startup
apply_user_settings()

FONT = config.global_config['font']
FONT_BOLD = 'Arial Bold'

# ----------------- Resident Management Functions -----------------

def enter_resident_info():
    # Calculate the default date (85 years ago from today)
    past = datetime.now() - timedelta(days=85*365)
    
    """ Display GUI for entering resident information. """
    layout = [
    [sg.Text('Please Enter Resident Information', justification='center', expand_x=True, font=(FONT, 18))],
    [sg.Text('Name', size=(15, 1), font=(FONT, 12)), sg.InputText(key='Name', size=(20,1), font=(FONT, 12))],
    [sg.Text('Date of Birth', size=(15, 1), font=(FONT, 12)), 
     sg.InputText(key='Date_of_Birth', size=(20,1), disabled=True, font=(FONT, 12)), 
     sg.CalendarButton('Choose Date', target='Date_of_Birth', 
                       default_date_m_d_y=(past.month, past.day, past.year), 
                       format='%Y-%m-%d', font=(FONT, 12))],
    [sg.Text('Level of Care', justification='center', expand_x=True, font=(FONT, 15))],
    [sg.Radio('Supervisory Care', "RADIO1", default=True, key='Supervisory_Care', size=(15,1), font=(FONT, 12)), 
     sg.Radio('Personal Care', "RADIO1", key='Personal_Care', size=(15,1), font=(FONT, 12)), 
     sg.Radio('Directed Care', "RADIO1", key='Directed_Care', size=(15,1), font=(FONT, 12))],
    [sg.Text('', expand_x=True), sg.Submit(font=(FONT, 12)), sg.Cancel(font=(FONT, 12)), sg.Text('', expand_x=True)]]

    window = sg.Window('Enter Resident Info', layout)

    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):
            break
        elif event == 'Submit':
            name = values['Name'].title()
             # Determine the selected level of care
            level_of_care = 'Supervisory Care' if values['Supervisory_Care'] else 'Personal Care' if values['Personal_Care'] else 'Directed Care'
            api_functions.insert_resident(API_URL, name, values['Date_of_Birth'], level_of_care)
            config.global_config['resident_names'] = api_functions.get_resident_names(API_URL)
            #logged_in_user = config.global_config['logged_in_user']
            # api_functions.log_action(API_URL, logged_in_user, 'Resident Added', f'Resident Added {name}')
            # logged server side
            sg.popup('Resident information saved!')
            window.close()
            return True

    window.close()
    

def enter_resident_removal():
    # Fetch the list of residents for the dropdown
    # Check global config resident_names if none fetch from api
    if config.global_config['resident_names']:
        residents = config.global_config['resident_names']
    else:
        residents = api_functions.get_resident_names(API_URL)
        config.global_config['resident_names'] = residents

    # Define the layout for the removal window
    layout = [
        [sg.Text('Warning: Removing a resident is irreversible.', text_color='red', font=(FONT_BOLD, 16))],
        [sg.Text('Please ensure you have saved any required data before proceeding.', font=(FONT, 12))],
        [sg.Text('Select a resident to remove:', font=(FONT, 12)), sg.Combo(residents, key='-RESIDENT-', font=(FONT, 12))],
        [sg.Button('Remove Resident', font=(FONT, 12)), sg.Button('Cancel', font=(FONT, 12))]
    ]

    # Create the removal window
    window = sg.Window('Remove Resident', layout)

    # Event loop for the removal window
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':
            break
        elif event == 'Remove Resident':
            # Confirm the removal
            resident_to_remove = values['-RESIDENT-']
            if resident_to_remove:  # Proceed only if a resident is selected
                confirm = sg.popup_yes_no('Are you sure you want to remove this resident? This action cannot be undone.')
                if confirm == 'Yes':
                    # Function to be replaced with API call
                    #db_functions.remove_resident(resident_to_remove)
                    show_progress_bar(api_functions.remove_resident, API_URL, resident_to_remove)
                    # Refresh cached resident names
                    config.global_config['resident_names'] = api_functions.get_resident_names(API_URL)
                    sg.popup(f'Resident {resident_to_remove} has been removed.')
                    window.close()
                    break

    window.close()


def change_theme_window():
    global FONT
    # Define the theme options available
    theme_options = sg.theme_list()

    # Define the font options available
    symbol_fonts = [
    'Webdings', 'Wingdings', 'Wingdings 2', 'Wingdings 3', 'Symbol', 
    'MS Outlook', 'Bookshelf Symbol 7', 'MT Extra', 
    'HoloLens MDL2 Assets', 'Segoe MDL2 Assets', 'Segoe UI Emoji', 
    'Segoe UI Symbol', 'Marlett', 'Cambria Math', 'Terminal'
    # Exclusion List
    ]

    font_options = [f for f in font.families() if f not in symbol_fonts]
    
    layout = [
        [sg.Text(text= 'Select Theme Colors:', font=(FONT, 20))],
        [sg.Combo(theme_options, default_value=sg.theme(), key='-THEME-', readonly=True, font=(FONT, 12))],
        [sg.Text(text='Select Font:', font=(FONT,20))],
        [sg.Combo(font_options, key='-FONT_CHOICE-', default_value=FONT, font=(FONT, 12))],
        [sg.Text(text='', expand_x=True), sg.Button(button_text= 'Ok', font=(FONT, 15), pad= ((10,10), (12,0))), 
         sg.Button(button_text='Cancel', font=(FONT, 15), pad= ((10,10), (12,0))),
         sg.Text(text='', expand_x=True)]
    ]

    # Create the theme selection window
    theme_window = sg.Window('Change Theme', layout)

    # Event loop for the theme window
    while True:
        event, values = theme_window.read()
        if event in (None, 'Cancel'):
            theme_window.close()
            break
        elif event == 'Ok':
            selected_theme = values['-THEME-']
            sg.theme(values['-THEME-'])

            selected_font = values['-FONT_CHOICE-']
            api_functions.save_user_preferences(API_URL, selected_theme, selected_font)
            

            theme_window.close()
            break

    theme_window.close()


# def enter_resident_edit():
#     # Fetch list of residents
#     resident_names = db_functions.get_resident_names()

#     layout = [
#         [sg.Text('Select Resident:'), sg.Combo(resident_names, key='-RESIDENT-', readonly=True)],
#         [sg.Text('New Name:'), sg.InputText(key='-NEW_NAME-')],
#         [sg.Text('New Date of Birth:(YYYY-MM-DD)'), sg.InputText(key='-NEW_DOB-')],
#         [sg.Button('Update'), sg.Button('Cancel')]
#     ]

#     window = sg.Window('Edit Resident Information', layout)

#     while True:
#         event, values = window.read()
#         if event in (sg.WIN_CLOSED, 'Cancel'):
#             break
#         elif event == 'Update':
#             # Fetch current information
#             current_info = db_functions.fetch_resident_information(values['-RESIDENT-'])
#             resident_name = values['-RESIDENT-']
#             if current_info:
#                 # Update information
#                 db_functions.update_resident_info(values['-RESIDENT-'], values['-NEW_NAME-'].strip(), values['-NEW_DOB-'].strip())
#                 db_functions.log_action(config.global_config['logged_in_user'], 'Fixed Resident Typo(s)', f'fixed typos for {resident_name}')
#                 sg.popup('Resident information updated')
#             else:
#                 sg.popup('Resident not found')
#             break

#     window.close()

# --------------------------------- User Management Functions ------------------------------------------------

def create_initial_admin_account_window():

    layout = [
        [sg.Text('', expand_x=True), sg.Text("Welcome to CareTech Resident Management", font=(FONT, 18)), sg.Text('', expand_x=True)],
        [sg.Text('', expand_x=True), sg.Text("Please set up the Administrator account", font=(FONT, 16)), sg.Text('', expand_x=True)],
        [sg.Text('', expand_x=True), sg.Text("Username:", font=(FONT, 14)), sg.InputText(key='username', size=16, font=(FONT, 14)), sg.Text('', expand_x=True)],
        [sg.Text('', expand_x=True), sg.Text("Password:", font=(FONT, 16)), sg.InputText(key='password', password_char='*', size=16, font=(FONT, 14)), sg.Text('', expand_x=True)],
        [sg.Text('', expand_x=True), sg.Text("Initials:", font=(FONT, 16)), sg.InputText(key='initials', size=4, font=(FONT, 14)), sg.Text('', expand_x=True)],
        [sg.Text('', expand_x=True), sg.Button("Create Admin Account", font=(FONT, 12)), sg.Button("Exit", font=(FONT, 12)), sg.Text('', expand_x=True)]
    ]

    window = sg.Window("Admin Account Setup", layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "Exit":
            sys.exit(0)
        elif event == "Create Admin Account":
            username = values['username']
            password = values['password']
            initials = values['initials'].strip().upper()
            if not username or not password:
                sg.popup("Username and password are required.", title="Error")
                continue

            # No longer need to collect db_passphrase as it's automatically set
            try:
                
                api_functions.create_admin_account(API_URL, username, password, initials)
                sg.popup("Admin account created successfully. Please ensure the passphrase is securely stored and set as an environment variable.", title="Success")
                break
            except Exception as e:
                sg.popup(f"Error creating admin account: {e}", title="Error")

    window.close()


def new_user_setup_window(username):
    layout = [
        [sg.Text(f"Welcome {username}, please set your new password.")],
        [sg.Text("New Password:"), sg.InputText(key='new_password', password_char='*')],
        [sg.Button("Set Password"), sg.Button("Cancel")]
    ]

    window = sg.Window("Password Reset", layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Cancel"):
            break
        elif event == "Set Password":
            new_password = values['new_password']

            # Validate new password and initials
            if new_password:
                api_functions.update_password(API_URL, username, new_password)
                sg.popup("Password updated successfully.")
                break
            else:
                sg.popup("Please enter a new password and initials.", title="Error")

    window.close()


def add_user_window():
    logged_in_user = config.global_config['logged_in_user']
    layout = [
        [sg.Text("Add New User")],
        [sg.Text("Username:"), sg.InputText(key='username')],
        [sg.Text("Temporary Password:"), sg.InputText(key='temp_password', password_char='*')],
        [sg.Text("Role:"), sg.Combo(['User', 'Admin'], default_value='User', key='role', readonly=True)],
        [sg.Text("Initials:"), sg.InputText(key='initials')],  # Added field for initials
        [sg.Button("Add User"), sg.Button("Cancel")]
    ]

    window = sg.Window("Add User", layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Cancel"):
            break
        elif event == "Add User":
            username = values['username']
            temp_password = values['temp_password']
            role = values['role']
            initials = values['initials']  # Retrieve the initials from the input field

            # Validate input (e.g., non-empty, username uniqueness, etc.)
            if not username or not temp_password or not initials:
                sg.popup("username, initials and temporary password are required.", title="Error")
                continue

            # Add the new user
            try:
                success = api_functions.create_user(API_URL, username, temp_password, role, True, initials)  # Pass initials to the API function
                if success:
                    sg.popup("User added successfully.")
                    break
                else:
                    sg.popup("Failed to add user. Please try again.", title="Error")
            except Exception as e:
                sg.popup(f"Error adding user: {e}", title="Error")

    window.close()


def remove_user_window():
    # Fetch usernames for the dropdown
    usernames = api_functions.get_all_users(API_URL)

    layout = [
        [sg.Text("Select User:"), sg.Combo(usernames, key='-USERNAME-')],
        [sg.Text("Reason for Removal:"), sg.InputText(key='-REASON-')],
        [sg.Button("Remove User"), sg.Button("Cancel")]
    ]

    window = sg.Window("Remove User", layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "Cancel":
            break
        elif event == "Remove User":
            username = values['-USERNAME-']
            reason = values['-REASON-'].strip()

            if not username or not reason:
                sg.popup_error("Both username and reason for removal are required.")
                continue
            
            # Confirmation popup
            confirm = sg.popup_yes_no(f"Are you sure you want to remove '{username}'?", title="Confirm Removal")
            if confirm == "Yes":
                try:

                    if api_functions.remove_user(API_URL, username):
                        api_functions.log_action(API_URL, config.global_config['logged_in_user'], 'User Removal', f"User '{username}' removed. Reason: {reason}")
                        sg.popup(f"User '{username}' has been removed successfully.")
                        break
                except Exception as e:
                    sg.popup_error(f"Error removing user: {e}")
            else:
                sg.popup("User removal cancelled.")
    window.close()


def login_window():
    layout = [
        [sg.Text("CareTech Facility Management", font=(FONT, 15), pad=10)],
        [sg.Text("Username:", font=(FONT, 15), size=9, pad=(0,12)), sg.InputText(key='username', size=14, font=(FONT,15))],
        [sg.Text("Password:", font=(FONT,15), size=9, pad=(0,12)), sg.InputText(key='password', password_char='*', size=14, font=(FONT,15))],
        [sg.Text('', expand_x=True), sg.Button(key='Login', size=14, image_filename='login.png', pad=(15), bind_return_key=True), sg.Button(key='Exit', size=14, image_filename='exit.png', pad=(15)), sg.Text('', expand_x=True)]
    ]

    window = sg.Window("Login", layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            sys.exit(0)
        elif event == "Login":
            username = values['username']
            password = values['password']
            
            # Wrap the validate_login function call with show_progress_bar
            login_success = show_progress_bar(api_functions.validate_login, API_URL, username, password)
            
            if login_success:
                # Log the successful login action
                config.global_config['logged_in_user'] = username
                
                # Checking if a password reset is needed
                password_reset_needed = show_progress_bar(api_functions.needs_password_reset, API_URL, username)
                
                if password_reset_needed:
                    window.close()
                    new_user_setup_window(username)
                    resident_count = show_progress_bar(api_functions.get_resident_count, API_URL)
                    display_welcome_window(resident_count, show_login=False)
                else:
                    # Proceed to main application
                    sg.popup("Login Successful!", title="Success")
                    window.close()
                    break
            else:
                sg.popup("Invalid username or password.", title="Error")

    window.close()


def logout():
    """
    Logs the user out by clearing the saved token and showing the login window.
    """
    # Clear saved token
    keyring.set_password('CareTechApp', 'access_token', None)
    
    # Show login window
    display_welcome_window(api_functions.get_resident_count(API_URL), show_login=True, show_time_out=True)


def audit_logs_window():
    col_widths = [20, 15, 20, 70]  # Adjusted for readability
    # Define the layout for the audit logs window
    layout = [
        [sg.Text('', expand_x=True), sg.Text('Admin Audit Logs', font=(FONT, 23)), sg.Text('', expand_x=True)],
        [sg.Text("Filter by Username:"), sg.InputText(key='-USERNAME_FILTER-', size=14)],
        [sg.Text("Filter by Action:"), sg.Combo(['Resident Added', 'User Created', 'Medication Added', 'Add Non-Medication Order', 'Non-Medication Order Administered'], key='-ACTION_FILTER-', readonly=True)],
        [sg.Text("Filter by Date (YYYY-MM-DD):"), sg.InputText(key='-DATE_FILTER-', enable_events=True, size=10), sg.CalendarButton("Choose Date", target='-DATE_FILTER-', close_when_date_chosen=True, format='%Y-%m-%d')],
        [sg.Button("Apply Filters"), sg.Button("Reset Filters")],
        [sg.Table(headings=['Date', 'Username', 'Action', 'Description'], values=[], key='-AUDIT_LOGS_TABLE-', auto_size_columns=False, display_row_numbers=True, num_rows=20, col_widths=col_widths, enable_click_events=True, select_mode=sg.TABLE_SELECT_MODE_BROWSE)],
        [sg.Button("Close")]
    ]

    window = sg.Window("Audit Logs", layout, finalize=True)

    # Function to load audit logs
    def load_audit_logs(username_filter='', action_filter='', date_filter=''):
        logs = api_functions.fetch_audit_logs(API_URL, last_10_days=True, username=username_filter, action=action_filter, date=date_filter)
        table_data = [[log['date'], log['username'], log['action'], log['description']] for log in logs]
        window['-AUDIT_LOGS_TABLE-'].update(values=[[log['date'], log['username'], log['action'], log['description']] for log in logs])
        return table_data

    original_table_data = load_audit_logs()  # Initial loading of logs

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == "Close":
            break
        elif event[0] == '-AUDIT_LOGS_TABLE-' and event[1] == '+CLICKED+':
            row_index = event[2][0]  # Get the row index from the event tuple.
            # Access the clicked row's data using the row_index from your original dataset.
            clicked_row_data = original_table_data[row_index]
            description = clicked_row_data[3]  # Assuming the description is in the fourth column.
            sg.popup_scrolled(description, title='Detailed Description', size=(50, 10))
        elif event == "Apply Filters":
            original_table_data = load_audit_logs(username_filter=values['-USERNAME_FILTER-'], action_filter=values['-ACTION_FILTER-'], date_filter=values['-DATE_FILTER-'])
        elif event == "Reset Filters":
            window['-USERNAME_FILTER-'].update('')
            window['-ACTION_FILTER-'].update('')
            window['-DATE_FILTER-'].update('')
            original_table_data = load_audit_logs()  # Reload logs without filters

    window.close()

# ------------------------------------------------------- menu & activity tables -------------------------------------------------------

def activities_data_window(activities_list):
    layout = [
        [sg.Text('Activities Data', font=('Helvetica', 16))],
        [sg.Listbox(values=sorted(activities_list), size=(40, 10), key='-ACTIVITIES LIST-', enable_events=True)],
        [sg.Text('Add New Activity:'), sg.InputText(key='-NEW ACTIVITY-')],
        [sg.Button('Add Activity', key='-ADD ACTIVITY-', font=(FONT, 13)), sg.Button('Remove Selected Activity', key='-REMOVE ACTIVITY-', font=(FONT, 13))],
        [sg.Button('Exit', font=(FONT, 13))]
    ]

    window = sg.Window('View/Edit Activities Data', layout, modal=True)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == 'Exit':
            break
        # elif event == '-ADD ACTIVITY-':
        #     new_activity = values['-NEW ACTIVITY-'].strip().title()
        #     if new_activity:
        #         # Call the function to add a new activity
        #         success = api_functions.add_activity(API_URL, new_activity)
        #         if success:
        #             updated_activities = api_functions.fetch_activities(API_URL)
        #             window['-ACTIVITIES LIST-'].update(values=sorted(updated_activities))
        #             sg.popup(f'Successfully added activity: {new_activity}')
        #         else:
        #             sg.popup_error(f'Failed to add activity: {new_activity}')

        # elif event == '-ADD ACTIVITY-':
        #     new_activity = values['-NEW ACTIVITY-'].strip().title()
        #     if new_activity:
        #         # Initialize Progress Bar Window
        #         progress_layout = [[sg.Text('Adding new activity...')],
        #                         [sg.ProgressBar(1000, orientation='h', size=(20, 20), key='-PROGRESS-')]]
        #         progress_window = sg.Window('Progress', progress_layout, modal=True, finalize=True)
        #         progress_bar = progress_window['-PROGRESS-']
                
        #         # Simulate progress (for actual progress, you'd update this within your operation loop)
        #         for i in range(500):
        #             event, values = progress_window.read(timeout=10)
        #             if event == sg.WIN_CLOSED:
        #                 break
        #             progress_bar.UpdateBar(i + 1)
                
        #         # Simulate an HTTP request or long operation
        #         success = api_functions.add_activity(API_URL, new_activity)
        #         progress_window.close()  # Close the progress bar window
                
        #         if success:
        #             updated_activities = api_functions.fetch_activities(API_URL)
        #             window['-ACTIVITIES LIST-'].update(values=sorted(updated_activities))
        #             sg.popup(f'Successfully added activity: {new_activity}')
        #         else:
        #             sg.popup_error(f'Failed to add activity: {new_activity}')
        
        # elif event == '-ADD ACTIVITY-':
        #     new_activity = values['-NEW ACTIVITY-'].strip().title()
        #     if new_activity:
        #         # Queue to hold the success status
        #         success_queue = queue.Queue()

        #         # Define the target function for threading to include queue
        #         def add_activity_thread(queue, api_url, activity):
        #             success = api_functions.add_activity(api_url, activity)
        #             queue.put(success)  # Put the success status into the queue

        #         # Initialize Progress Bar Window for indeterminate progress
        #         progress_layout = [[sg.Text('Processing...')],
        #                         [sg.ProgressBar(100, orientation='h', size=(20, 20), key='-PROGRESS-')]]
        #         progress_window = sg.Window('Please Wait', progress_layout, modal=True, keep_on_top=True, finalize=True)
        #         progress_bar = progress_window['-PROGRESS-']

        #         # Start the add_activity function in a thread
        #         progress_thread = threading.Thread(target=add_activity_thread, args=(success_queue, API_URL, new_activity), daemon=True)
        #         progress_thread.start()

        #         while progress_thread.is_alive():
        #             for i in range(100):
        #                 event, values = progress_window.read(timeout=10)
        #                 if event == sg.WIN_CLOSED:
        #                     break
        #                 progress_bar.update(i + 1)
        #             progress_bar.update(0)  # Reset the bar for a continuous loop effect
                
        #         progress_window.close()

        #         # Check the operation's success status from the queue
        #         success = success_queue.get()  # Retrieve the success status

        #         if success:
        #             updated_activities = api_functions.fetch_activities(API_URL)
        #             window['-ACTIVITIES LIST-'].update(values=sorted(updated_activities))
        #             # Reset the input field after successful addition
        #             window['-NEW ACTIVITY-'].update('')
        #             sg.popup(f'Successfully added activity: {new_activity}')
        #         else:
        #             sg.popup_error(f'Failed to add activity: {new_activity}')

        elif event == '-ADD ACTIVITY-':
            new_activity = values['-NEW ACTIVITY-'].strip().title()
            if new_activity:
                # Use the show_progress_bar function for the add_activity operation
                success = show_progress_bar(api_functions.add_activity, API_URL, new_activity)
                
                if success:
                    updated_activities = api_functions.fetch_activities(API_URL)
                    window['-ACTIVITIES LIST-'].update(values=sorted(updated_activities))
                    sg.popup(f'Successfully added activity: {new_activity}')
                else:
                    sg.popup_error(f'Failed to add activity: {new_activity}')



        elif event == '-REMOVE ACTIVITY-':
            selected_activity = values['-ACTIVITIES LIST-']
            if selected_activity:
                confirm = sg.popup_yes_no(f'Are you sure you want to remove {selected_activity[0]}?')
                if confirm == 'Yes':
                    success = api_functions.remove_activity(API_URL, selected_activity[0])
                    if success:
                        updated_activities = api_functions.fetch_activities(API_URL)
                        window['-ACTIVITIES LIST-'].update(values=sorted(updated_activities))
                        sg.popup(f'Successfully removed activity: {selected_activity[0]}')
                    else:
                        sg.popup_error(f'Failed to remove activity: {selected_activity[0]}')
            else:
                sg.popup_error('Please select an activity to remove')

    window.close()


def meal_data_window(breakfast_list, lunch_list, dinner_list):
    
    layout = [
        [sg.Text('', expand_x=True), sg.Text('Meal Data Management', font=(FONT, 20)), sg.Text('', expand_x=True)],
        [
            sg.Column([
                [sg.Text('Breakfast', font=(FONT, 18))],
                [sg.Listbox(values=sorted(breakfast_list), size=(60, 25), key='-BREAKFAST LIST-', enable_events=True)],
                [sg.Text('Line 1:'), sg.InputText(key='-NEW BREAKFAST1-'), ],
                [sg.Text('Line 2:'), sg.InputText(key='-NEW BREAKFAST2-')],
                [sg.Text('Breakfast Drink Option:'), sg.InputText(key='-NEW BREAKFAST DEFAULT DRINK-', default_text='Juice/Milk/Coffee')],
                [sg.Button('Add Breakfast', key='-ADD BREAKFAST-'), sg.Button('Remove Selected Breakfast', key='-REMOVE BREAKFAST-')]
            ]),
            sg.VSeparator(),
            sg.Column([
                [sg.Text('Lunch', font=(FONT, 18))],
                [sg.Listbox(values=sorted(lunch_list), size=(60, 25), key='-LUNCH LIST-', enable_events=True)],
                [sg.Text('Line 1:'), sg.InputText(key='-NEW LUNCH1-')],
                [sg.Text('Line 2:'), sg.InputText(key='-NEW LUNCH2-')],
                [sg.Text('Dessert:'), sg.InputText(key='-NEW LUNCH DESSERT-')],
                [sg.Button('Add Lunch', key='-ADD LUNCH-'), sg.Button('Remove Selected Lunch', key='-REMOVE LUNCH-')]
            ]),
            sg.VSeparator(),
            sg.Column([
                [sg.Text('Dinner', font=(FONT, 18))],
                [sg.Listbox(values=sorted(dinner_list), size=(60 , 25), key='-DINNER LIST-', enable_events=True)],
                [sg.Text('Line 1:'), sg.InputText(key='-NEW DINNER1-')],
                [sg.Text('Line 2:'), sg.InputText(key='-NEW DINNER2-')],
                [sg.Text('Dessert:'), sg.InputText(key='-NEW DINNER DESSERT-')],
                [sg.Button('Add Dinner', key='-ADD DINNER-'), sg.Button('Remove Selected Dinner', key='-REMOVE DINNER-')]
            ])
        ],
        [sg.Button('Exit')]
    ]

    window = sg.Window('Meal Data Management', layout, modal=True)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == 'Exit':
            break
        elif event.startswith('-ADD'):
            if event.startswith('-ADD BREAKFAST'):
                new_breakfast1 = values['-NEW BREAKFAST1-'].strip().title()
                new_breakfast2 = values['-NEW BREAKFAST2-'].strip().title()
                new_breakfast_drink = values['-NEW BREAKFAST DEFAULT DRINK-'].strip().title()
                if new_breakfast1 or new_breakfast2:
                    # Concatenate the new breakfast lines with semicolons
                    new_breakfast = new_breakfast1 + '; ' + new_breakfast2 + ';'
                    success = api_functions.add_meal(API_URL, 'breakfast', new_breakfast, new_breakfast_drink)
                    if success:
                        updated_breakfast = api_functions.fetch_raw_meal_data(API_URL, 'breakfast')
                        window['-BREAKFAST LIST-'].update(values=sorted(updated_breakfast))
                        sg.popup('Breakfast added successfully!')
                    else:
                        sg.popup_error('Failed to add breakfast')
            elif event.startswith('-ADD LUNCH'):
                new_lunch1 = values['-NEW LUNCH1-'].strip().title()
                new_lunch2 = values['-NEW LUNCH2-'].strip().title()
                new_lunch_dessert = values['-NEW LUNCH DESSERT-'].strip().title()
                if new_lunch1 or new_lunch2:
                    # Concatenate the new lunch lines plus dessert with semicolons
                    new_lunch = new_lunch1 + '; ' + new_lunch2 + ';' + new_lunch_dessert + ';'
                    success = api_functions.add_meal(API_URL, 'lunch', new_lunch, default_drink=None)
                    if success:
                        updated_lunch = api_functions.fetch_raw_meal_data(API_URL, 'lunch')
                        window['-LUNCH LIST-'].update(values=sorted(updated_lunch))
                        sg.popup('Lunch added successfully!')
                    else:
                        sg.popup_error('Failed to add lunch')
            elif event.startswith('-ADD DINNER'):
                new_dinner1 = values['-NEW DINNER1-'].strip().title()
                new_dinner2 = values['-NEW DINNER2-'].strip().title()
                new_dinner_dessert = values['-NEW DINNER DESSERT-'].strip().title()
                if new_dinner1 or new_dinner2:
                    # Concatenate the new dinner lines plus dessert with semicolons
                    new_dinner = new_dinner1 + '; ' + new_dinner2 + ';' + new_dinner_dessert + ';'
                    success = api_functions.add_meal(API_URL, 'dinner', new_dinner, default_drink=None)
                    if success:
                        updated_dinner = api_functions.fetch_raw_meal_data(API_URL, 'dinner')
                        window['-DINNER LIST-'].update(values=sorted(updated_dinner))
                        sg.popup('Dinner added successfully!')
                    else:
                        sg.popup_error('Failed to add dinner')
        elif event.startswith('-REMOVE'):
            if event.startswith('-REMOVE BREAKFAST'):
                selected_breakfast = values['-BREAKFAST LIST-']
                if selected_breakfast:
                    # Splitting the breakfast string at semicolons, excluding the last element (default_drink)
                    breakfast_components = selected_breakfast[0].split(';')[:-1]
                    # Rejoining the remaining elements to match the meal_option format in the database
                    meal_option_without_drink = ';'.join(breakfast_components) + ';'
                    success = api_functions.remove_meal(API_URL, 'breakfast', meal_option_without_drink)
                    if success:
                        updated_breakfast = api_functions.fetch_raw_meal_data(API_URL, 'breakfast')
                        window['-BREAKFAST LIST-'].update(values=sorted(updated_breakfast))
                        sg.popup('Breakfast removed successfully!')
            elif event.startswith('-REMOVE LUNCH'):
                selected_lunch = values['-LUNCH LIST-']
                if selected_lunch:
                    # Splitting the lunch string at semicolons
                    lunch_components = selected_lunch[0].split(';')
                    # Rejoining the remaining elements to match the meal_option format in the database
                    meal_option = ';'.join(lunch_components)
                    success = api_functions.remove_meal(API_URL, 'lunch', meal_option)
                    if success:
                        updated_lunch = api_functions.fetch_raw_meal_data(API_URL, 'lunch')
                        window['-LUNCH LIST-'].update(values=sorted(updated_lunch))
                        sg.popup('Lunch removed successfully!')
            elif event.startswith('-REMOVE DINNER'):
                selected_dinner = values['-DINNER LIST-']
                if selected_dinner:
                    # Splitting the dinner string at semicolons
                    dinner_components = selected_dinner[0].split(';')
                    # Rejoining the remaining elements to match the meal_option format in the database
                    meal_option = ';'.join(dinner_components)
                    success = api_functions.remove_meal(API_URL, 'dinner', meal_option)
                    if success:
                        updated_dinner = api_functions.fetch_raw_meal_data(API_URL, 'dinner')
                        window['-DINNER LIST-'].update(values=sorted(updated_dinner))
                        sg.popup('Dinner removed successfully!')
            
    window.close()


def generate_calendar_window():
    layout = [
        [sg.Text('Year:', size=7, font=(FONT, 14)), sg.InputText(datetime.now().year, key='-YEAR-', size=(10, 1), font=(FONT, 14))],
        [sg.Text('Month:', size=7, font=(FONT, 14)), sg.Combo([calendar.month_name[i] for i in range(1, 13)], key='-MONTH-', size=(15, 1), font=(FONT, 14))],
        [sg.Button('Generate Menu Calendar', pad=((10,10),(8,8)), font=(FONT, 13)), sg.Button('Generate Activities Calendar', pad=((10,10),(15,15)), font=(FONT, 13))],
        [sg.Button('View/Edit Meals Data', pad=((10,10),(5,8)), font=(FONT, 13)), sg.Button('View/Edit Activities Data', pad=((10,10),(5,8)), font=(FONT, 13))],
        [sg.Button('Exit', pad=((10,10),(8,8)), font=(FONT, 13))]
    ]

    window = sg.Window('Generate Calendar', layout)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == 'Exit':
            break
        elif event == 'Generate Menu Calendar':
            year = int(values['-YEAR-'])
            month = list(calendar.month_name).index(values['-MONTH-'])
            if month == 0:
                sg.popup_error('Please select a valid month')
                continue
            file_name = create_menu(year, month)
            sg.popup('Menu Calendar Generated:', file_name)
        elif event == 'Generate Activities Calendar':
            year = int(values['-YEAR-'])
            month = list(calendar.month_name).index(values['-MONTH-'])
            if month == 0:
                sg.popup_error('Please select a valid month')
                continue
            file_name = create_calendar(year, month)
            sg.popup('Activities Calendar Generated:', file_name)
        elif event == 'View/Edit Activities Data':
            window.hide()
            activities = api_functions.fetch_activities(API_URL)
            activities_data_window(activities)
            window.un_hide()
        # elif event == 'View/Edit Meals Data':
        #     window.hide()
        #     breakfast = api_functions.fetch_raw_meal_data(API_URL, 'breakfast')
        #     lunch = api_functions.fetch_raw_meal_data(API_URL, 'lunch')
        #     dinner = api_functions.fetch_raw_meal_data(API_URL, 'dinner')
        #     meal_data_window(breakfast, lunch, dinner)
        #     window.un_hide()
        elif event == 'View/Edit Meals Data':
            meal_data = show_loading_window_for_meals(API_URL)
            if meal_data:
                breakfast, lunch, dinner = meal_data
                window.hide()
                meal_data_window(breakfast, lunch, dinner)
                window.un_hide()



    window.close()

# -------------------------------------------------------- main window ---------------------------------------------------------

def display_welcome_window(num_of_residents_local, show_login=False, show_time_out=False):
    if config.global_config['is_first_time_setup'] is None:
        config.global_config['is_first_time_setup'] = api_functions.is_first_time_setup(API_URL)
        
        if config.global_config['is_first_time_setup']:
            create_initial_admin_account_window()
            sys.exit(0)
        else:
            pass

    if config.global_config['is_first_time_setup'] is True:
        create_initial_admin_account_window()
        sys.exit(0)
    
    if show_time_out:
        sg.popup_error('Session timed out. Please log in again.', title='Session Timeout')
        
    if show_login:
        login_window()

    logged_in_user = config.global_config['logged_in_user']

    if config.global_config['is_admin'] is None:
        config.global_config['is_admin'] = api_functions.is_admin(API_URL, logged_in_user)
     

    """ Display a welcome window with the number of residents. """
    image_path = 'ct-logo.png'

    # Define the admin panel frame
    admin_panel_layout = [
        [sg.Button('Add Resident', pad=(6, 3), font=(FONT, 12)),
        sg.Button('Remove Resident', pad=(6, 3), font=(FONT, 12)),
        sg.Button('Edit Resident', pad=(6, 3), font=(FONT, 12))],
        [sg.Text('', expand_x=True), sg.Button('Add User', pad=(6, 3), font=(FONT, 12)),
        sg.Button('Remove User', pad=(6, 3), font=(FONT, 12)), sg.Text('', expand_x=True), 
        sg.Button('View Audit Logs', font=(FONT, 12)), sg.Text('', expand_x=True)]
    ]
    
    admin_panel = sg.Frame('Admin Panel', admin_panel_layout, font=(FONT, 14), visible=config.global_config['is_admin'])

    layout = [
        [sg.Text(f'CareTech Facility Management', font=(FONT, 20), justification='center', pad=(20,20))],
        [sg.Image(image_path)],
        [sg.Text(f'Your Facility Currently has {num_of_residents_local} Resident(s)',font=(FONT, 16), justification='center', pad=(10,10))],
        [sg.Text(text='', expand_x=True), sg.Button(key='Enter Resident Management', pad=((25,25),(10,10)), image_filename='adl_emar_button.png'),
         sg.Button(key="Change Theme", pad=((25,25),(10,10)), image_filename='style.png'), sg.Text(text='', expand_x=True)],
         [sg.Button(key='Calendar Generators', pad=((25,25),(10,10)), image_filename='calendar_button.png'), sg.Button(key='Reminder', pad=((25,25),(10,10)), image_filename='reminder_button.png'),],
        [admin_panel]
    ]

    window = sg.Window('CareTech Facility Management', layout, element_justification='c')

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == 'Add User':
             print('testing add user')
             window.close()
             add_user_window()
             display_welcome_window(num_of_residents_local)
        elif event == 'Add Resident':
            window.close()
            enter_resident_info()
            display_welcome_window(api_functions.get_resident_count(API_URL))
        elif event == 'Remove Resident':
            window.close()
            enter_resident_removal()
            display_welcome_window(api_functions.get_resident_count(API_URL))
        elif event == 'Enter Resident Management':
            if num_of_residents_local == 0:
                sg.popup("Your Facility Has No Residents. Please Click 'Add Resident'.", font=("Helvetica", 12), title='Error - No Residents')
            else:
                results = show_loading_window(API_URL)
                if results == 'token_expired':
                    logout()
                elif results:
                    # Unpack the results directly if you are sure all will always be returned successfully
                    resident_names, user_initials, existing_adl_data, resident_care_levels, all_medications_data, active_medications, non_medication_orders, existing_emar_data = results
                    window.hide()
                    resident_management.main(resident_names, user_initials, existing_adl_data, resident_care_levels, all_medications_data, active_medications, non_medication_orders, existing_emar_data)
                    window.un_hide()
                else:
                    sg.popup_error("Failed to load resident management data.")
        elif event == 'Change Theme':
            window.close()
            change_theme_window()
            display_welcome_window(num_of_residents_local)
        # elif event == 'Edit Resident':
        #     window.close()
        #     enter_resident_edit()
        #     display_welcome_window(db_functions.get_resident_count())
        elif event == 'Remove User':
            window.hide
            remove_user_window()
            window.un_hide()
        elif event == 'View Audit Logs':
            window.hide()
            audit_logs_window()
            window.un_hide()
        elif event == 'Calendar Generators':
            window.hide()
            generate_calendar_window()
            window.un_hide()
        elif event == 'Reminder':
            window.hide()
            tracker_reminder.create_dashboard_window()
            window.un_hide()
            
    #api_functions.log_action(logged_in_user, 'Logout', f'{logged_in_user} logout')
    config.global_config['logged_in_user'] = None
    window.close()


if __name__ == "__main__":
    display_welcome_window(api_functions.get_resident_count(API_URL), show_login=True)
