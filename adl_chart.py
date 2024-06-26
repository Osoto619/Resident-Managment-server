import PySimpleGUI as sg
from datetime import datetime
import calendar
import db_functions
import pdf
import api_functions
import config

API_URL = config.API_URL


# Define the width of the label cell and regular cells
label_cell_width = 12  # This may need to be adjusted to align perfectly
regular_cell_width = 5  # This may need to be adjusted to align perfectly

# Define the number of days
num_days = 31

ADL_KEYS = [
                "first_shift_sp", "second_shift_sp", "first_shift_activity1", "first_shift_activity2",
                "first_shift_activity3", "second_shift_activity4", "first_shift_bm", "second_shift_bm",
                "shower", "shampoo", "sponge_bath", "peri_care_am", "peri_care_pm", "oral_care_am", "oral_care_pm",
                "nail_care", "skin_care", "shave", "breakfast", "lunch", "dinner", "snack_am",
                "snack_pm", "water_intake"]


def create_horizontal_bar(text):
    return [sg.Text(f'{text}', justification='center', expand_x=True, relief=sg.RELIEF_SUNKEN)]


def create_row_label(text):
    return [sg.Text(f'{text}', size=(label_cell_width+1, 1), pad=(0,0), justification='center')]


def create_input_text(key):
    return [sg.InputText(size=(regular_cell_width, 1), pad=(3, 3), justification='center', key=f'-{key}-{i}-') for i in range(1, num_days + 1)]


def show_adl_chart(resident_name, year_month):
    # Define the number of days
    num_days = 31

    # Define the width of the label cell and regular cells
    label_cell_width = 12  # This may need to be adjusted to align perfectly
    regular_cell_width = 5  # This may need to be adjusted to align perfectly

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
        "15. Social Media"]

    # Divide activities into three columns
    column1 = [[sg.Text(activities[i])] for i in range(0, len(activities), 3)]
    column2 = [[sg.Text(activities[i])] for i in range(1, len(activities), 3)]
    column3 = [[sg.Text(activities[i])] for i in range(2, len(activities), 3)]

    # Create a frame with three columns
    activities_frame = sg.Frame('Activities', layout=[
        [sg.Column(column1), sg.Column(column2), sg.Column(column3)]
    ], relief=sg.RELIEF_SUNKEN)

    # Empty row for the table to just show headers
    data = [[]]  # No data rows, only headers

    # Parse the year and month
    year, month_number = year_month.split('-')
    month_name = calendar.month_name[int(month_number)]

    # Define the layout of the window
    layout = [
        [sg.Text('CareTech Monthly ADL Chart', font=('Helvetica', 16), justification='center', expand_x=True)],
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
        create_horizontal_bar("Service Plan (Initial when completed)"),
        create_row_label("1st Shift") +
        create_input_text("first_shift_sp"),
        create_row_label("2nd Shift") +
        create_input_text("second_shift_sp"),
        create_horizontal_bar("Activity Record Number (see legend at bottom)"),
        create_row_label("1st Activity") +
        create_input_text("first_shift_activity1"),
        create_row_label("2nd Activity") +
        create_input_text("first_shift_activity2"),
        create_row_label("3rd Activity") +
        create_input_text("first_shift_activity3"),
        create_row_label("4th Activity") +
        create_input_text("second_shift_activity4"),
        create_horizontal_bar("Bowel Movement Record size of BM and how many if more than one (Example: SM, M, L, XL, or D for diarrhea, S for self)"),
        create_row_label("1st Shift") +
        create_input_text("first_shift_bm"),
        create_row_label("2nd Shift") +
        create_input_text("second_shift_bm"),
        create_horizontal_bar("ADL's (Initials or S for Self, H for Hospice)"),
        create_row_label("SHOWER") +
        create_input_text("shower"),
        create_row_label("SHAMPOO") +
        create_input_text("shampoo"),
        create_row_label("SPONGE BATH") +
        create_input_text("sponge_bath"),
        create_row_label("PERI CARE AM") +
        create_input_text("peri_care_am"),
        create_row_label("PERI CARE PM") +
        create_input_text("peri_care_pm"),
        create_row_label("ORAL CARE AM") +
        create_input_text("oral_care_am"),
        create_row_label("ORAL CARE PM") +
        create_input_text("oral_care_pm"),
        create_row_label("NAIL CARE") +
        create_input_text("nail_care"),
        create_row_label("SKIN CARE") +
        create_input_text("skin_care"),
        create_row_label("SHAVE") +
        create_input_text("shave"),
        create_horizontal_bar("Meals (Record Percentage of Meal Eaten)"),
        create_row_label("BREAKFAST") +
        create_input_text("breakfast"),
        create_row_label("LUNCH") +
        create_input_text("lunch"),
        create_row_label("DINNER") +
        create_input_text("dinner"),
        create_row_label("SNACK AM") +
        create_input_text("snack_am"),
        create_row_label("SNACK PM") +
        create_input_text("snack_pm"),
        create_row_label("WATER IN-TAKE") +
        create_input_text("water_intake"),
        [sg.Text(text='', expand_x=True), [sg.Button('Save Changes Made'), sg.Button('Generate PDF'), sg.Button('Hide Buttons')], activities_frame, sg.Text(text='', expand_x=True)]
        #sg.Button('Save Changes Made')
    ]

    # Create the window
    window = sg.Window(' CareTech Monthly ADLs', layout, finalize=True, resizable=True)


    adl_data = api_functions.fetch_adl_chart_data_for_month(API_URL, resident_name, year_month)
    
    if adl_data:
        for entry in adl_data:
            chart_date_str = entry.get("chart_date")
            # Example: 'Tue, 27 Feb 2024 00:00:00 GMT' -> '27 Feb 2024'
            date_part = ' '.join(chart_date_str.split(' ')[1:4])
            # Parse '27 Feb 2024' into a datetime object
            chart_date = datetime.strptime(date_part, "%d %b %Y")
            day_number = chart_date.day  # Extract the day of the month

            for adl_key in ADL_KEYS:
                value = entry.get(adl_key, "")
                if value:  # Check if there is a value to update
                    window[f'-{adl_key}-{day_number}-'].update(value)


    # Event Loop
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == 'Hide Buttons':
            window['Save Changes Made'].update(visible=False)
            window['Generate PDF'].update(visible=False)
            window['Hide Buttons'].update(visible=False)
        elif event == 'Save Changes Made':
            adl_data = []
            for day in range(1, 32):  # Assuming a maximum of 31 days in a month
                day_data = {key.split('-')[1]: values[key] for key in values if key.endswith(f'-{day}-') and values[key].strip()}
                if day_data:  # If there's data for this day, add it to the list
                    adl_data.append({'chart_date': f'{year_month}-{day:02d}', 'data': day_data})

            if adl_data:
                response = api_functions.save_adl_data_from_chart_window(API_URL, resident_name, year_month, adl_data)
                if response == 'token_expired':
                    from new_main import logout
                    logout()
                elif response:
                    sg.popup("ADL data saved successfully.")
                else:
                    sg.popup_error("Failed to save ADL data.")

        elif event == 'Generate PDF':
            pdf.generate_adl_chart_pdf(resident_name, year_month, adl_data)

    window.close()


if __name__ == "__main__":
    show_adl_chart("Rosa Soto", "2023-12")
