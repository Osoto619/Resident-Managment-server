import PySimpleGUI as sg
from datetime import datetime, timedelta


def create_dashboard_window():
    layout = [
        [sg.Text('Facility Management Expiration Tracker Dashboard', font=('Helvetica', 16), justification='center', pad=(0, 20))],  # Header
        [sg.Text('Renewals Coming Up:', font=('Helvetica', 12)), sg.Text('2 items need renewal in the next 30 days', font=('Helvetica', 12))],  # Upcoming renewals
        [sg.Text('Immediate Action Required:', font=('Helvetica', 12), text_color='red'), sg.Text('1 item due for renewal today', font=('Helvetica', 12), text_color='red')],  # Immediate actions
        [sg.Button('Employees', size=(20, 2)), sg.Button('Residents', size=(20, 2))],  # Navigation buttons
        [sg.Button('Facility', size=(20, 2)), sg.Button('Regulations Repository', size=(20, 2))],  # More navigation
        [sg.Frame('Alerts', [[sg.Text('• CPR Certification expiring for 2 employees', text_color='red')]], pad=(0,20))],  # Alerts section
        [sg.Button('Exit', size=(10, 1))]
    ]
    
    # Create the window
    window = sg.Window('Expiration Tracker Dashboard', layout, default_element_size=(20, 1), element_justification='c')
    
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        elif event == 'Employees':
            window.hide()
            employee_docs_window()
            window.un_hide()
    
    window.close()


def employee_docs_window():
    # Sample data: Employee Name, Certification Date, Expiration Date, Status
    # Normally, you'd fetch this data from your server
    today = datetime.today()
    two_years_ago = today - timedelta(days=730)
    # Sample data adjusted to include the certificate name
    data = [
        ['John Doe', 'CPR/First Aid', two_years_ago.strftime('%Y-%m-%d'), (two_years_ago + timedelta(days=730)).strftime('%Y-%m-%d'), 'Valid'],
        ['Jane Smith', 'CPR/First Aid', (two_years_ago - timedelta(days=100)).strftime('%Y-%m-%d'), (two_years_ago - timedelta(days=100) + timedelta(days=730)).strftime('%Y-%m-%d'), 'Expired'],
        # Add more entries as needed
    ]
    
    # Define the table layout
    headings = ['Employee Name', 'Certificate/Document Name', 'Certification Date', 'Expiration Date', 'Status']
    layout = [
    [sg.Text('Employee Compliance Tracking', font=('Helvetica', 16), justification='center')],
    [sg.Table(values=data, headings=headings, max_col_width=25,
              auto_size_columns=True, display_row_numbers=True,
              justification='left', num_rows=10, key='-TABLE-',
              row_height=25, tooltip='Employee Compliance Data')],
    [sg.Button('Add New'), sg.Button('Edit'), sg.Button('Renew'), sg.Button('Back')],
      ]

    # Create the window
    window = sg.Window('Employees', layout, element_justification='c')
    
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Back':
            break
        elif event == 'Add New':
            window.hide()
            add_new_employee_doc_window()
            # Refresh the table data after adding a new document
            window.un_hide()

    window.close()


def add_new_employee_doc_window():
    # Placeholder for fetching document names from the database
    document_names = ['CPR/First Aid', 'Fingerprint Clearance', 'Manager License', 'Custom']
    document_intervals = {'CPR/First Aid': '730', 'Fingerprint Clearance': '365', 'Manager License': '1095', 'Custom': ''}
    
    layout = [
        [sg.Text('Add New Document for Tracking', font=('Helvetica', 16), justification='center')],
        [sg.Text('Employee Name:'), sg.InputText()],
        [sg.Text('Document:'), sg.Combo(document_names, default_value=document_names[0], key='-DOCUMENT-', enable_events=True)],
        [sg.Text('Expiration Interval (days):'), sg.InputText(document_intervals[document_names[0]], key='-INTERVAL-')],
        [sg.Text('Custom Document Name:'), sg.InputText(key='-CUSTOM-NAME-', visible=False)],
        [sg.Text('Certification Date:'), sg.InputText('', key='CertDate'), sg.CalendarButton('Choose Date', target='CertDate', format='%Y-%m-%d')],
        [sg.Text('Reminder Days Before Expiration:'), sg.InputText('30')],
        [sg.Submit(), sg.Cancel()]
    ]
    
    window =  sg.Window('Add New Tracked Item', layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':
            break
        elif event == 'Submit':
            print(values)
            # Add the new document to the database
            pass
        # Update expiration interval and custom name visibility based on document selection
        if event == '-DOCUMENT-':
            if values['-DOCUMENT-'] == 'Custom':
                window['-INTERVAL-'].update('')
                window['-CUSTOM-NAME-'].update(visible=True)
            else:
                window['-INTERVAL-'].update(document_intervals[values['-DOCUMENT-']])
                window['-CUSTOM-NAME-'].update(visible=False)
        

    window.close()