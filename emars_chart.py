import PySimpleGUI as sg
import calendar
from datetime import datetime
import db_functions
import api_functions
import config
from progress_bar import show_progress_bar

API_URL = config.API_URL

FONT = config.global_config['font']

# Define the width of the label cell and regular cells
label_cell_width = 12  # This may need to be adjusted to align perfectly
regular_cell_width = 5  # This may need to be adjusted to align perfectly

# Define the spacer width to align with the table header
spacer_width = 3  # Adjust as needed

# Define the number of days
num_days = 31


def create_horizontal_bar(text):
    return [sg.Text(f'{text}', justification='center', expand_x=True, relief=sg.RELIEF_SUNKEN)]


def create_row_label(text):
    return [sg.Text(f'{text}', size=(label_cell_width+7, 1), pad=(0,0), justification='center')]


def create_row_label_noninput(text):
    return [sg.Text(f'{text}', size=(label_cell_width+8, 1), pad=(0,0), justification='center')]


def create_input_text(key):
    return [sg.InputText(size=(regular_cell_width, 1), pad=(3, 3), justification='center', key=f'-{key}-{i}-') for i in range(1, num_days + 1)]


def create_prn_controlled_input_text(key):
    return [sg.InputText(size=(regular_cell_width, 1), 
                         pad=(3, 3), 
                         justification='center', 
                         key=f'-{key}-{i}-', 
                         readonly=True,
                         text_color='blue',
                         font = ('Helvetica', 10, 'bold'), 
                         enable_events=True) for i in range(1, num_days + 1)]


def create_medication_section(medication_name, medication_info):
    section_layout = []
    section_layout.append(create_row_label_noninput(medication_name))
    section_layout.append(create_row_label_noninput(f"{medication_info['dosage']}"))
    section_layout.append(create_row_label_noninput(f"{medication_info['instructions']}"))

    for time_slot in medication_info['time_slots']:
        row = create_row_label(time_slot)  + [sg.Text('      ')] + create_input_text(f"{medication_name}_{time_slot}")
        section_layout.append(row)

    section_layout.append(create_horizontal_bar(''))  # End with a horizontal bar
    return section_layout


def create_prn_controlled_medication_section(medication_name, medication_info, type='PRN'):
    section_layout = []
    section_layout.append(create_row_label_noninput(medication_name))
    section_layout.append(create_row_label_noninput(f"{medication_info['dosage']}"))
    section_layout.append(create_row_label_noninput(f"{medication_info['instructions']}"))

    # Adding a label to indicate that this is a PRN medication
    # section_layout.append(create_row_label("As Needed (PRN)"))
    row = create_row_label("As Needed (PRN)" if type=='PRN' else "Controlled Medication") + [sg.Text('      ')] + create_prn_controlled_input_text(f"{type}_{medication_name}")
    section_layout.append(row)
    table_view_button = [sg.Text('     '),sg.Button('Table View', key=f'-TABLE_VIEW_{type}_{medication_name}-')]
    section_layout.append(table_view_button)
    section_layout.append(create_horizontal_bar(''))  # End with a horizontal bar
    return section_layout


# def create_prn_details_window(event_key, resident_name, year_month, medication_name):
#     _, med_name, day, _ = event_key.split('-')
#     parts = med_name.split('_')
#     med_name = parts[1] 
#     day = day.zfill(2)  # Ensure day is two digits
#     prn_data = api_functions.fetch_prn_data_for_day(API_URL, resident_name, med_name, year_month, day)

#     # Check if prn_data is not empty to avoid KeyError
#     if not prn_data:
#         sg.popup_error("No PRN data found for the selected day.")
#         return

#     # Adjusted to access dictionary keys directly
#     date_str = prn_data[0]['date']  # Access the 'date' key in the first dictionary
#     date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S GMT')  # Adjusted for the given date format
#     formatted_date = date_obj.strftime('%m-%d-%Y')  # Format it as MM-DD-YYYY

#     # Transform data for the table, adjusted for dictionary access
#     table_data = [[entry['date'], entry['administered'], entry['notes']] for entry in prn_data]

#     # Define table headers
#     headers = ["Date/Time Administered", "Administered By", "Notes"]

#     # Define the layout with the table
#     layout = [
#         [sg.Text('', expand_x=True), sg.Text(f"{medication_name} {formatted_date}", font=('Helvetica', 17)), sg.Text("", expand_x=True)],
#         [sg.Table(values=table_data, headings=headers, max_col_width=25, auto_size_columns=True, justification='left', num_rows=min(10, len(table_data)))]
#     ]
#     layout.append([sg.Text("", expand_x=True), sg.Button("Close", key="-CLOSE-", font=('Helvetica', 14)), sg.Text("", expand_x=True)])

#     window = sg.Window("PRN Details", layout, modal=True)
    
#     while True:
#         event, values = window.read()
#         if event == sg.WIN_CLOSED or event == "-CLOSE-":
#             break

#     window.close()


def create_prn_details_window(event_key, resident_name, year_month, medication_name):
    _, med_name, day, _ = event_key.split('-')
    parts = med_name.split('_')
    med_name = parts[1]
    day = day.zfill(2)  # Ensure day is two digits
    prn_data = api_functions.fetch_prn_data_for_day(API_URL, resident_name, med_name, year_month, day)

    if not prn_data:
        sg.popup_error("No PRN data found for the selected day.")
        return

    # Adjust parsing logic to accommodate potential absence of time component
    for entry in prn_data:
        # Attempt to parse with time component
        try:
            entry_date = datetime.strptime(entry['date'].strip(), '%Y-%m-%d %H:%M')
        except ValueError:
            # If parsing fails, fall back to date only
            entry_date = datetime.strptime(entry['date'].strip(), '%Y-%m-%d')
        # Reformat entry['date'] to ensure consistency
        entry['date'] = entry_date.strftime('%Y-%m-%d %H:%M')

    formatted_date = prn_data[0]['date'].split(' ')[0]  # Use the date part for the window title, formatted as YYYY-MM-DD
    formatted_date = datetime.strptime(formatted_date, '%Y-%m-%d').strftime('%m-%d-%Y')  # Convert to MM-DD-YYYY format

    table_data = [[entry['date'], entry['administered'], entry['notes']] for entry in prn_data]

    headers = ["Date/Time Administered", "Administered By", "Notes"]

    layout = [
        [sg.Text('', expand_x=True), sg.Text(f"{medication_name} {formatted_date}", font=('Helvetica', 17)), sg.Text("", expand_x=True)],
        [sg.Table(values=table_data, headings=headers, max_col_width=25, auto_size_columns=True, justification='left', num_rows=min(10, len(table_data)))]
    ]
    layout.append([sg.Text("", expand_x=True), sg.Button("Close", key="-CLOSE-", font=('Helvetica', 14)), sg.Text("", expand_x=True)])

    window = sg.Window("PRN Details", layout, modal=True)
    
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "-CLOSE-":
            break

    window.close()


def create_controlled_details_window(event_key, resident_name, year_month, medication_name):
    controlled_data = db_functions.fetch_controlled_data_for_day(event_key, resident_name, year_month)
    
     # Extract the date from the first entry in controlled_data (assuming it's always in the same format)
    date_str = controlled_data[0][0]  # Get the date string from the first entry
    date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M')  # Parse it as a datetime object
    formatted_date = date_obj.strftime('%m-%d-%Y')  # Format it as DD-MM-YYYY

    # Transform data for the table
    table_data = [[entry[0], entry[1], entry[2], entry[3]] for entry in controlled_data]

    # Define table headers
    headers = ["Date/Time Administered", "Administered By", "Notes", "Count After Administration"]

    # Define the layout with the table
    layout = [
        [sg.Text('', expand_x=True), sg.Text(f"{medication_name}  {formatted_date}", font=('Any', 17)), sg.Text("", expand_x=True)],
        [sg.Table(values=table_data, headings=headers, max_col_width=25, auto_size_columns=True, justification='left', num_rows=min(10, len(table_data)))]
    ]
    layout.append([sg.Text("", expand_x=True), sg.Button("Close", key="-CLOSE-", font=('Any', 14)), sg.Text("", expand_x=True)])

    window = sg.Window("Controlled Medication Details", layout, modal=True)
    
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "-CLOSE-":
            break

    window.close()


def is_after_discontinuation(year_month, discontinue_date):
    """
    Check if the year_month is after the discontinue_date.
    year_month format: 'YYYY-MM'
    discontinue_date format: 'YYYY-MM-DD'
    """
    year_month_dt = datetime.strptime(year_month, "%Y-%m")
    discontinue_date_dt = datetime.strptime(discontinue_date, "%Y-%m-%d")
    return year_month_dt > discontinue_date_dt


# def create_monthly_details_window(resident_name, medication_name, year_month, medication_type):
#     monthly_data = api_functions.fetch_monthly_medication_data(API_URL, resident_name, medication_name, year_month, medication_type)
#     if not monthly_data:
#         sg.popup_error("No monthly data found for the selected medication.")
#         return

#     # Define table headers based on medication type
#     if medication_type == 'Control':
#         headers = ["Date Administered", "Administered By", "Notes", "Count After Administration"]
#     else:  # PRN medication
#         headers = ["Date Administered", "Administered By", "Notes"]

#     # Transform data for the table
#     table_data = [list(row) for row in monthly_data]

#     # Define the layout with the table
#     layout = [
#         [sg.Text(f"Monthly Log for {medication_name}", font=("Helvetica", 16), justification='center')],
#         [sg.Table(values=table_data, headings=headers, max_col_width=25, auto_size_columns=True, justification='left', num_rows=min(10, len(table_data)))]
#     ]
#     layout.append([sg.Button("Close", key="-CLOSE-", font=("Helvetica", 11))])

#     # Create and show the window
#     window = sg.Window(f"Monthly Details for {medication_name}", layout, modal=True)

#     while True:
#         event, values = window.read()
#         if event in (sg.WIN_CLOSED, "-CLOSE-"):
#             break

#     window.close()
def create_monthly_details_window(resident_name, medication_name, year_month, medication_type):
    monthly_data = api_functions.fetch_monthly_medication_data(API_URL, resident_name, medication_name, year_month, medication_type)

    if not monthly_data:
        sg.popup_error("No data found for the selected month.")
        return

    # No need to append time to date since 'date' already includes the time component
    formatted_month_year = datetime.strptime(year_month, '%Y-%m').strftime('%B %Y')

    # Define table headers based on medication type
    if medication_type == 'Control':
        headers = ["Date/Time Administered", "Administered By", "Notes", "Count After Administration"]
        table_data = [[entry['date'], entry['administered'], entry['notes'], entry.get('current_count', '')] for entry in monthly_data]
    else:
        headers = ["Date/Time Administered", "Administered By", "Notes"]
        table_data = [[entry['date'], entry['administered'], entry['notes']] for entry in monthly_data]

    layout = [
        [sg.Text('', expand_x=True), sg.Text(f"{medication_name} Details for {formatted_month_year}", font=('Helvetica', 17)), sg.Text("", expand_x=True)],
        [sg.Table(values=table_data, headings=headers, max_col_width=25, auto_size_columns=True, justification='left', num_rows=min(10, len(table_data)))]
    ]
    layout.append([sg.Text("", expand_x=True), sg.Button("Close", key="-CLOSE-", font=('Helvetica', 14)), sg.Text("", expand_x=True)])

    window = sg.Window("Monthly Medication Details", layout, modal=True)
    
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "-CLOSE-":
            break

    window.close()


def show_emar_chart(resident_name, year_month, emar_data, discontinued_medications, original_structure):
    # Define the number of days
    num_days = 31

    # Define the width of the label cell and regular cells
    label_cell_width = 22  # This may need to be adjusted to align perfectly
    regular_cell_width = 5  # This may need to be adjusted to align perfectly

    # Empty row for the table to just show headers
    data = [[]]  # No data rows, only headers

    # Parse the year and month
    year, month_number = year_month.split('-')
    month_name = calendar.month_name[int(month_number)]

    # Fetch eMAR data for the month
    #emar_data = api_functions.fetch_emar_data_for_month(API_URL, resident_name, year_month)

    # print(f'RESIDENT NAME: {resident_name}')
    # print(f'YEAR MONTH: {year_month}')
    # print(f'EMAR DATA: {emar_data}')

    # Fetch discontinued medications with their discontinuation dates
    #discontinued_medications = api_functions.fetch_discontinued_medications(API_URL, resident_name)
    # print('testing dc meds')
    # print(discontinued_medications)

    #original_structure = api_functions.fetch_medications_for_resident(API_URL, resident_name)
    
    # Process Scheduled Medications
    new_structure = {}
    for time_slot, medications in original_structure['Scheduled'].items():
        for medication_name, details in medications.items():
            if medication_name not in new_structure:
                new_structure[medication_name] = {
                    'dosage': details['dosage'], 
                    'instructions': details['instructions'],
                    'time_slots': [time_slot],
                    'type': 'Scheduled'
            }
            else:
                new_structure[medication_name]['time_slots'].append(time_slot)
    
    # Process PRN Medications
    prn_structure = {}
    for medication_name, details in original_structure['PRN'].items():
        prn_structure[medication_name] = {
            'dosage': details['dosage'],
            'instructions': details['instructions'],
            'type': 'PRN'
    }
    
    # Process Controlled Medications
    controlled_structure = {}
    for medication_name, details in original_structure['Controlled'].items():
        controlled_structure[medication_name] = {
            'dosage': details['dosage'],
            'instructions': details['instructions'],
            'form' : details['form'],
            'count': details['count'],
            'type': 'Controlled'
        }

    # Filter out discontinued medications for future months
    filtered_new_structure = {}
    for med_name, med_info in new_structure.items():
        if med_name in discontinued_medications:
            if is_after_discontinuation(year_month, discontinued_medications[med_name]):
                continue  # Skip this medication as it's discontinued for this month
        filtered_new_structure[med_name] = med_info

    filtered_prn_structure = {}
    for med_name, med_info in prn_structure.items():
        if med_name in discontinued_medications:
            if is_after_discontinuation(year_month, discontinued_medications[med_name]):
                continue  # Skip this medication as it's discontinued for this month
        filtered_prn_structure[med_name] = med_info

    filtered_control_structure = {}
    for med_name, med_info, in controlled_structure.items():
        if med_name in discontinued_medications:
            if is_after_discontinuation(year_month, discontinued_medications[med_name]):
                continue
        filtered_control_structure[med_name] = med_info
    # print('testing controlled structure')
    # print(controlled_structure)
    # print('testing filtered control structure')
    # print(filtered_control_structure)

    # Use filtered_new_structure and filtered_prn_structure for creating the layout

    # Medication layout
    medication_layout = []
    for med_name, med_info in filtered_new_structure.items():
        medication_layout.extend(create_medication_section(med_name, med_info))
    for med_name, med_info in filtered_prn_structure.items():
        medication_layout.extend(create_prn_controlled_medication_section(med_name, med_info))
    for med_name, med_info in filtered_control_structure.items():
        medication_layout.extend(create_prn_controlled_medication_section(med_name, med_info, type='Control'))

    # Define the layout of the window
    layout = [
        [sg.Text('CareTech Monthly eMAR Chart', font=('Helvetica', 16), justification='center', expand_x=True)],
        [sg.Text('RESIDENT:', size=(10, 1)), sg.Text(f'{resident_name}', key='-RESIDENT-', size=(20, 1)),
        sg.Text('MONTH:', size=(10, 1)), sg.Text(f'{month_name} {year}', key='-MONTH-', size=(20, 1))],
        # Table as a header row of cells
        [sg.Table(values=data,
              headings=[''] + [str(i) for i in range(1, num_days + 1)],
              max_col_width=regular_cell_width,
              auto_size_columns=False,
              col_widths=[label_cell_width] + [regular_cell_width]*num_days,
              display_row_numbers=False,
              justification='center',
              num_rows=0,
              key='-TABLE-',
              row_height=25,
              pad=(0,0),
              hide_vertical_scroll=True)],
        create_horizontal_bar(text=''),
        [sg.Column(medication_layout, scrollable=True, vertical_scroll_only=True, size=(1600, 750))]
    ]

    instruction_text = (
    "Instructions for Viewing PRN and Controlled Medication Details:\n"
    "1. Select the PRN or Controlled Medication Day: Click on the input box for the day you wish to view.\n"
    "2. Press Any Alphanumeric Key (A-Z or 0-9) to view the detailed administration records for that day.\n"
    )
    legend_text = ("Legend:\n"
    "- 'ADM' indicates the medication was administered on that day.\n"
    "- 'DC' indicates the medication was discontinued on or after that day.")

    layout.append([sg.Text(instruction_text, key='-INSTRUCTIONS-', font=(FONT, 11)), sg.Text('', expand_x=True), sg.Text(legend_text, key='-LEGEND-')])
    layout.append([sg.Button('Save Changes Made'), sg.Button('Hide Buttons/Instructions')])
    # Create the window
    window = sg.Window(' CareTech Monthly eMARS', layout, finalize=True, resizable=True)

    # # Convert the eMAR data into a more convenient structure
    # emar_data_dict = {}
    
    # for med_name, date, time_slot, administered in emar_data:
    #     if med_name not in emar_data_dict:
    #         emar_data_dict[med_name] = {}
    #     if date not in emar_data_dict[med_name]:
    #         emar_data_dict[med_name][date] = {}
    #     emar_data_dict[med_name][date][time_slot] = administered

    # Correctly restructuring the eMAR data for GUI update
    emar_data_dict = {}

    for entry in emar_data:  # Directly using the list of dictionaries from emar_data
        med_name = entry['medication_name']
        date = entry['chart_date']
        time_slot = entry['time_slot']
        administered = entry['administered']

        if med_name not in emar_data_dict:
            emar_data_dict[med_name] = {}
        if date not in emar_data_dict[med_name]:
            emar_data_dict[med_name][date] = {}
        emar_data_dict[med_name][date][time_slot] = administered
    
    # # print(original_structure)
    
    # print(prn_structure)
    # print('-----------------------')
    # print(new_structure)

    # print(f'EMAR DATA DICT: {emar_data_dict}')

    # # If data is found, update the layout fields accordingly
    # for med_name, med_info in filtered_new_structure.items():
    #     if med_info['type'] == 'Scheduled':
    #         # Handle scheduled medications
    #         for date, slots in emar_data_dict.get(med_name, {}).items():
    #             day = int(date.split('-')[2])  # Extract the day from 'YYYY-MM-DD'
    #             for time_slot, administered in slots.items():
    #                 key = f'-{med_name}_{time_slot}-{day}-'
    #                 if window[key]:
    #                     window[key].update(administered)

    for med_name, dates_info in emar_data_dict.items():
        for date, slots in dates_info.items():
            day = int(date.split('-')[2])  # Extract the day from 'YYYY-MM-DD'
            for time_slot, administered in slots.items():
                key = f'-{med_name}_{time_slot}-{day}-'
                if key in window.AllKeysDict:  # Check if key exists
                    window[key].update(administered)
                else:
                    print(f"Key not found in window: {key}")


        # Update layout for PRN medications
    for med_name in filtered_prn_structure.keys():
        for datetime_string, slots in emar_data_dict.get(med_name, {}).items():
            # Split the date and time, and then extract the day
            date_part = datetime_string.split()[0]  # Get the 'YYYY-MM-DD' part
            day = int(date_part.split('-')[2])  # Extract the day

            control_key = f'-PRN_{med_name}-{day}-'
            # Check if there is any administration data for the day
            if any(slots.values()):
                administered_text = 'ADM'  # Indicating at least one administration
                if window[control_key]:
                    window[control_key].update(administered_text)

    # Update layout for Controlled medications
    for med_name in filtered_control_structure.keys():
        for datetime_string, slots in emar_data_dict.get(med_name, {}).items():
            # Split the date and time, and then extract the day
            date_part = datetime_string.split()[0]  # Get the 'YYYY-MM-DD' part
            day = int(date_part.split('-')[2])  # Extract the day

            control_key = f'-Control_{med_name}-{day}-'
            # Check if there is any administration data for the day
            if any(slots.values()):
                administered_text = 'ADM'  # Indicating at least one administration
                if window[control_key]:
                    window[control_key].update(administered_text)

    # Update layout for scheduled and PRN medications
    for med_name, med_info in filtered_new_structure.items():
        # Check if the medication is discontinued
        if med_name in discontinued_medications:
            discontinue_date = discontinued_medications[med_name]
            # Calculate the day of the month to start showing 'DC'
            discontinue_day = int(discontinue_date.split('-')[2])

            # Update the cells from the discontinuation date forward
            for day in range(discontinue_day, num_days + 1):
                for time_slot in med_info['time_slots']:
                    key = f'-{med_name}_{time_slot}-{day}-'
                    if window[key]:
                        window[key].update('DC')

        # Update layout for PRN medications
    for med_name in filtered_prn_structure.keys():
        # Check if the medication is discontinued
        if med_name in discontinued_medications:
            discontinue_date = discontinued_medications[med_name]
            # Calculate the day of the month to start showing 'DC'
            discontinue_day = int(discontinue_date.split('-')[2])

            # Update the cells from the discontinuation date forward
            for day in range(discontinue_day, num_days + 1):
                key = f'-PRN_{med_name}-{day}-'
                if window[key]:
                    window[key].update('DC')
    
     # Update layout for Controlled medications
    for med_name in filtered_control_structure.keys():
        # Check if the medication is discontinued
        if med_name in discontinued_medications:
            discontinue_date = discontinued_medications[med_name]
            # Calculate the day of the month to start showing 'DC'
            discontinue_day = int(discontinue_date.split('-')[2])

            # Update the cells from the discontinuation date forward
            for day in range(discontinue_day, num_days + 1):
                key = f'-Control_{med_name}-{day}-'
                if window[key]:
                    window[key].update('DC')
                    
    # Event Loop
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == 'Hide Buttons/Instructions':
            window['Save Changes Made'].update(visible=False)
            window['Hide Buttons/Instructions'].update(visible=False)
            window['-INSTRUCTIONS-'].update(visible=False)
            window['-LEGEND-'].update(visible=False)
        elif event == 'Save Changes Made':
            #print(f'VALUES: {values}')
            success = api_functions.save_emar_data_from_chart_window(API_URL, resident_name, year_month, values)
            #show_progress_bar(api_functions.save_adl_data_from_chart_window, API_URL, resident_name, year_month, values)
            if success:
                sg.popup("Data saved successfully.")
            else:
                sg.popup_error("Failed to save data.")
        elif event.startswith('-PRN'):
            _, med_name, _, _ = event.split('-')
            parts = med_name.split('_')
            med_name = parts[1]
            year_month = f'{year}-{month_number.zfill(2)}'
            if values[event]:
                create_prn_details_window(event, resident_name, year_month, med_name)
        elif event.startswith('-Control'):
            _, med_name, _, _ = event.split('-')
            parts = med_name.split('_')
            med_name = parts[1]
            print(event)
            if values[event] and values[event] != 'DC':
                create_controlled_details_window(event,resident_name,year_month, med_name)
        elif event.startswith('-TABLE_VIEW_PRN_') or event.startswith('-TABLE_VIEW_Control'):
            # Splitting the event string and extracting necessary parts
            parts = event.strip('-').split('_')
            med_type = parts[2]  # Either 'PRN' or 'Controlled'
            med_name = '_'.join(parts[3:])  # Rejoining in case the name itself contains underscores
            create_monthly_details_window(resident_name, med_name, year_month, med_type)


    window.close()


if __name__ == "__main__":
    show_emar_chart("Snoop Dawg", "2023-12")