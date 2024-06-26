import PySimpleGUI as sg
import api_functions
from datetime import datetime
from adl_chart import show_adl_chart
import db_functions
import config

API_URL = config.API_URL

FONT = config.global_config['font']
FONT_BOLD = 'Arial Bold' 

def get_adl_tab_layout(resident_name, existing_adl_data, resident_care_levels):
    #existing_data = api_functions.fetch_adl_data_for_resident(API_URL, resident_name)
    existing_data = existing_adl_data
    #resident_care_levels = api_functions.get_resident_care_level(API_URL)
    is_supervisory_care = any(resident['name'] == resident_name and resident['level_of_care'] == 'Supervisory Care' for resident in resident_care_levels)
    user_initials = config.global_config['user_initials']
    
    bm_record_choices = ['SM', 'M', 'L', 'XL', 'D', 'N/A', 'S']  # Add user initials dynamically
    adl_choices = [user_initials, 'H', 'S']
    activities_choices = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']

    # Fields to auto-populate for self-care residents
    auto_self_fields = [
        'first_shift_bm', 'second_shift_bm', 'shower', 'shampoo',
        'sponge_bath', 'peri_care_am', 'peri_care_pm', 'oral_care_am',
        'oral_care_pm', 'nail_care', 'skin_care', 'shave']

    # Build the default texts for input fields
    input_fields_defaults = {field: existing_data.get(field, '') for field in auto_self_fields}

    # Auto-populate 'Self' for self-care residents in the existing fields
    if is_supervisory_care:
        for field in auto_self_fields:
            input_fields_defaults[field] = 'S'
    #input_fields_defaults['first_shift_bm']
    tab_layout = [
            [sg.Text(f'Service Plan Followed (Initials)', font=(FONT_BOLD, 14))],
            [sg.Text('1st Shift Service Plan', font=(FONT, 12)), sg.Checkbox('', key=f'CHECK_{resident_name}_first_shift_sp', enable_events=True, tooltip='Check to initial', disabled= True if existing_data.get('first_shift_sp', '') != '' else False, default=True if existing_data.get('second_shift_sp', '') != '' else False), sg.InputText(size=4, default_text=existing_data.get('first_shift_sp', ''), key=f'{resident_name}_first_shift_sp', readonly=False),
             sg.Text('2nd Shift Service Plan', font=(FONT, 12)), sg.Checkbox('', key=f'CHECK_{resident_name}_second_shift_sp', enable_events=True, tooltip='Check to initial', disabled= True if existing_data.get('second_shift_sp', '') != '' else False, default=True if existing_data.get('second_shift_sp', '') != '' else False), sg.InputText(size=4, default_text=existing_data.get('second_shift_sp', ''), key=f'{resident_name}_second_shift_sp', readonly=False)],
            [sg.Text("Activities (Use Activities Legend Below)", font=(FONT_BOLD, 14))],
            [sg.Text('1st Shift 1st Activity', font=(FONT, 12)), sg.Combo(activities_choices, default_value=existing_data.get('first_shift_activity1', ''), key=f'{resident_name}_first_shift_activity1', size=(4,1), readonly=True),
             sg.Text('1st Shift 2nd Activity', font=(FONT, 12)), sg.Combo(activities_choices, default_value=existing_data.get('first_shift_activity2', ''), key=f'{resident_name}_first_shift_activity2', size=(4,1), readonly=True)],
            [sg.Text('1st Shift 3rd Activity', font=(FONT, 12)), sg.Combo(activities_choices, default_value=existing_data.get('first_shift_activity3', ''), key=f'{resident_name}_first_shift_activity3', size=(4,1), readonly=True),
             sg.Text('2nd Shift 4th Activity', font=(FONT, 12)), sg.Combo(activities_choices, default_value=existing_data.get('second_shift_activity4', ''), key=f'{resident_name}_second_shift_activity4', size=(4,1), readonly=True)],
             [sg.Text("BM Record Size (SM, M, L, XL, or D for Diarrhea, S for Self)", font=(FONT_BOLD, 14))],
            [sg.Text('1st Shift Bowel Movement', font=(FONT, 12)),  sg.Combo(bm_record_choices, default_value=input_fields_defaults['first_shift_bm'], key=f'{resident_name}_first_shift_bm', size=(4,1), readonly=True),
             sg.Text('2nd Shift Bowel Movement', font=(FONT, 12)), sg.Combo(bm_record_choices, default_value=input_fields_defaults['second_shift_bm'], key=f'{resident_name}_second_shift_bm', size=(4,1), readonly=True)],
            [sg.Text("ADL's (Initial or S for Self, H for Hospice)", font=(FONT_BOLD, 14))],
            [sg.Text('Shower', font=(FONT, 12)), sg.Combo(adl_choices, default_value=input_fields_defaults['shower'], key=f'{resident_name}_shower', size=(4,1), readonly=True),
             sg.Text('Shampoo', font=(FONT, 12)), sg.Combo(adl_choices, default_value=input_fields_defaults['shampoo'], key=f'{resident_name}_shampoo', size=(4,1), readonly=True),
             sg.Text('Sponge Bath', font=(FONT, 12)), sg.Combo(adl_choices, default_value=input_fields_defaults['sponge_bath'], key=f'{resident_name}_sponge_bath', size=(4,1), readonly=True),
             sg.Text('Peri Care AM', font=(FONT, 12)), sg.Combo(adl_choices, default_value=input_fields_defaults['peri_care_am'], key=f'{resident_name}_peri_care_am', size=(4,1), readonly=True),
             sg.Text('Peri Care PM', font=(FONT, 12)), sg.Combo(adl_choices, default_value=input_fields_defaults['peri_care_pm'], key=f'{resident_name}_peri_care_pm', size=(4,1), readonly=True)],
            [sg.Text('Oral Care AM', font=(FONT, 12)), sg.Combo(adl_choices, default_value=input_fields_defaults['oral_care_am'], key=f'{resident_name}_oral_care_am', size=(4,1), readonly=True),
             sg.Text('Oral Care PM', font=(FONT, 12)), sg.Combo(adl_choices, default_value=input_fields_defaults['oral_care_pm'], key=f'{resident_name}_oral_care_pm', size=(4,1), readonly=True),
             sg.Text('Nail Care', font=(FONT, 12)), sg.Combo(adl_choices, default_value=input_fields_defaults['nail_care'], key=f'{resident_name}_nail_care', size=(4,1), readonly=True),
             sg.Text('Skin Care', font=(FONT, 12)), sg.Combo(adl_choices, default_value=input_fields_defaults['skin_care'], key=f'{resident_name}_skin_care', size=(4,1), readonly=True),
             sg.Text('Shave', font=(FONT, 12)), sg.Combo(adl_choices, default_value=input_fields_defaults['shave'], key=f'{resident_name}_shave', size=(4,1), readonly=True)],
            [sg.Text('Meals (Record Percentage of Meal Eaten 0-100)', font=(FONT_BOLD, 14))],
            [sg.Text('Breakfast', font=(FONT, 12)), sg.InputText(size=4, default_text=existing_data.get('breakfast', ''), key=f'{resident_name}_breakfast'),
             sg.Text('Lunch', font=(FONT, 12)), sg.InputText(size=4, default_text=existing_data.get('lunch', ''), key=f'{resident_name}_lunch'),
             sg.Text('Dinner', font=(FONT, 12)), sg.InputText(size=4, default_text=existing_data.get('dinner', ''), key=f'{resident_name}_dinner'),
             sg.Text('Snack AM', font=(FONT, 12)), sg.InputText(size=4, default_text=existing_data.get('snack_am', ''), key=f'{resident_name}_snack_am'),
             sg.Text('Snack PM', font=(FONT, 12)), sg.InputText(size=4, default_text=existing_data.get('snack_pm', ''), key=f'{resident_name}_snack_pm'),
             sg.Text('Water In-Take', font=(FONT, 12)), sg.InputText(size=4, default_text=existing_data.get('water_intake', ''), key=f'{resident_name}_water_intake')],
             [sg.Text('', expand_x=True), sg.Button('Save', key=('-ADL_SAVE-'), font=(FONT, 12), pad=((10, 10),(12,10))), sg.Button('View/Edit Current Month ADL Chart', key=('-CURRENT_ADL_CHART-'), font=(FONT, 12), pad=((10, 10),(12,10))),
             sg.Text('', expand_x=True)], [sg.Text('', expand_x=True), sg.Text('Or Search by Month and Year:', font=(FONT, 12)), sg.Text('',expand_x=True)], 
             [sg.Text(text="", expand_x=True),sg.Text(text="Enter Month: (MM)", font=(FONT, 12)), sg.InputText(size=4, key="-ADL_MONTH-") , sg.Text("Enter Year: (YYYY)", font=(FONT, 12)), sg.InputText(size=5, key='-ADL_YEAR-'), 
             sg.Button("Search", key='-ADL_SEARCH-', font=(FONT, 12)), sg.Text(text="", expand_x=True)]
        ]
    
    # Create the activities frame
    activities_frame = create_activities_frame()

    # Append the activities frame to the tab layout
    tab_layout.append([sg.Text(text='', expand_x=True), activities_frame, sg.Text(text='', expand_x=True)])

    # Create a scrollable container for the layout
    scrollable_layout = sg.Column(tab_layout, size=(750,695)) # Adjust the size as needed


    # return tab_layout
    # Return the layout wrapped in a scrollable container
    return [[scrollable_layout]]


def create_activities_frame():
    # Define activities
    activities = [
        "1. Movie & Snack or TV",
        "2. Exercise/Walking",
        "3. Games/Puzzles",
        "4. Outside/Patio",
        "5. Arts & Crafts",
        "6. Music Therapy",
        "7. Gardening",
        "8. Listen to Music",
        "9. Social Hour",
        "10. Cooking/Baking",
        "11. Birdwatching",
        "12. Outing/Excursion",
        "13. Hospice Visit",
        "14. Other as Listed on the Service Plan",
        "15. Social Media"
        ]

    # Divide activities into three columns
    column1 = [[sg.Text(activities[i], font=(FONT, 11))] for i in range(0, len(activities), 3)]
    column2 = [[sg.Text(activities[i], font=(FONT, 11))] for i in range(1, len(activities), 3)]
    column3 = [[sg.Text(activities[i], font=(FONT, 11))] for i in range(2, len(activities), 3)]
    # Create a frame with three columns
    return sg.Frame('Activities', layout=[
        [sg.Column(column1), sg.Column(column2), sg.Column(column3)]
    ], relief=sg.RELIEF_SUNKEN, font=(FONT, 12), pad=13)


def update_clock(window):
    current_time = datetime.now().strftime("%H:%M:%S")  # Get current time
    window['-TIME-'].update(current_time)


def retrieve_adl_data_from_window(window, resident_name):
    # Define the keys as they appear in the window and database
    adl_keys = [
        'first_shift_sp', 'second_shift_sp', 'first_shift_activity1',
        'first_shift_activity2', 'first_shift_activity3',
        'second_shift_activity4',
        'first_shift_bm', 'second_shift_bm', 'shower', 'shampoo',
        'sponge_bath', 'peri_care_am', 'peri_care_pm', 'oral_care_am',
        'oral_care_pm', 'nail_care', 'skin_care', 'shave', 'breakfast',
        'lunch', 'dinner', 'snack_am', 'snack_pm', 'water_intake'
    ]

    # Initialize a dictionary to store the ADL data
    adl_data = {}

    # Get the current values from the window for the specified resident
    values = window.read(timeout=10)[
        1]  # We use a timeout to read from the window non-blocking

    # Extract the data using the keys
    for key in adl_keys:
        # The keys in the window are prefixed with the resident's name
        window_key = f'{resident_name}_{key}'
        adl_data[key] = values.get(window_key,'').upper()  # Use .get() to handle missing keys

    return adl_data


def generate_adl_audit_description(adl_data, existing_adl_data):
    """
    Generates a description of the changes made to ADL data. It omits entries that were changed from a value
    to an empty string or None, focusing instead on meaningful updates.

    Args:
        adl_data (dict): The updated ADL data from the window.
        existing_adl_data (dict): The existing ADL data from the database.

    Returns:
        str: A description of the changes made, excluding changes to empty values.
    """
    changes = []
    for key in adl_data:
        # Check if the value has changed and the new value is neither None nor an empty string
        new_value = adl_data[key]
        old_value = existing_adl_data.get(key, '')
        if new_value != old_value and new_value not in [None, '']:
            # Record the change, converting None values to a readable string for old values
            old_value_display = 'None' if old_value in [None, ''] else old_value
            changes.append(f"{key} changed from '{old_value_display}' to '{new_value}'")

    # Format the list of changes into a string
    if changes:
        description = "ADL Changes: " + "; ".join(changes)
    else:
        description = "No changes made to ADL data."

    return description

