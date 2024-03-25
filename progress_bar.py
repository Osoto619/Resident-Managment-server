import threading
import queue
import PySimpleGUI as sg
import api_functions
import config

# Heroku API URL
# API_URL = 'https://resident-mgmt-flask-651cd3003add.herokuapp.com'

# Local API URL
API_URL = 'http://127.0.0.1:5000'


def show_progress_bar(target_function, *args, **kwargs):
    """
    Shows an indeterminate progress bar while executing a target function in a separate thread.
    :param target_function: The function to execute in a thread.
    :param args: Positional arguments to pass to the target function.
    :param kwargs: Keyword arguments to pass to the target function.
    """
    # Queue to hold the function's result
    result_queue = queue.Queue()

    # Wrapper to execute the target function and store the result in the queue
    def thread_wrapper(func, queue, *args, **kwargs):
        result = func(*args, **kwargs)
        queue.put(result)

    # Progress Bar GUI Setup
    progress_max = 100  # Maximum progress bar value
    progress_layout = [
        [sg.Text('Loading...')],
        [sg.ProgressBar(progress_max, orientation='h', size=(20, 20), key='-PROGRESS-')]
    ]
    progress_window = sg.Window('Working...', progress_layout, modal=True, keep_on_top=True, finalize=True)
    progress_bar = progress_window['-PROGRESS-']

    # Start the target function in a separate thread
    worker_thread = threading.Thread(target=thread_wrapper, args=(target_function, result_queue) + args, kwargs=kwargs, daemon=True)
    worker_thread.start()

    # Update the progress bar with a fill-and-reset loop while the thread is alive
    while worker_thread.is_alive():
        for i in range(progress_max + 1):
            event, values = progress_window.read(timeout=10)  # Short timeout for quick updates
            if event == sg.WIN_CLOSED:
                break
            progress_bar.UpdateBar(i)
        if event == sg.WIN_CLOSED:  # Check if the loop was exited due to window close event
            break

    progress_window.close()

    # Return the result from the target function
    return result_queue.get()


def load_resident_management_data(api_url):
    """
    Load data required for the resident management section by making multiple API calls.
    This function runs in a separate thread and uses a queue to return data to the main thread.
    """
    result_queue = queue.Queue()

    def worker():
        try:
            # Pre-existing calls
            resident_names = api_functions.get_resident_names(api_url)
            user_initials = api_functions.get_user_initials(api_url) if config.global_config['user_initials'] is None else config.global_config['user_initials']
            config.global_config['user_initials'] = user_initials

            selected_resident_name = resident_names[0] if resident_names else None

            # Fetching ADL data
            existing_adl_data = api_functions.fetch_adl_data_for_resident(api_url, selected_resident_name)
            resident_care_levels = api_functions.get_resident_care_level(api_url)
            

            # Fetching EMAR data
            all_medications_data = api_functions.fetch_medications_for_resident(api_url, selected_resident_name)

            # Extracting medication names and removing duplicates
            scheduled_meds = [med_name for time_slot in all_medications_data['Scheduled'].values() for med_name in time_slot]
            prn_meds = list(all_medications_data['PRN'].keys())
            controlled_meds = list(all_medications_data['Controlled'].keys())
            all_meds = list(set(scheduled_meds + prn_meds + controlled_meds))

            active_medications = api_functions.filter_active_medications(api_url, selected_resident_name, all_meds)
            non_medication_orders = api_functions.fetch_all_non_medication_orders(api_url, selected_resident_name)
            existing_emar_data = api_functions.fetch_emar_data_for_resident(api_url, selected_resident_name)
            

            # Package the results
            results = (resident_names, user_initials, existing_adl_data, resident_care_levels, all_medications_data, active_medications, non_medication_orders, existing_emar_data)
            result_queue.put(results)
        except Exception as e:
            sg.popup_error(f"Failed to load data: {e}", title="Loading Error")
            result_queue.put(None)

    threading.Thread(target=worker, daemon=True).start()
    return result_queue



def show_loading_window(api_url):
    """
    Show a loading window while the resident management data is being loaded.
    """
    progress_max = 100  # Define maximum progress bar value for quick fill
    progress_layout = [
        [sg.Text('Loading Resident Management Data...')],
        [sg.ProgressBar(progress_max, orientation='h', size=(20, 20), key='-PROGRESS-')]
    ]
    progress_window = sg.Window('Please Wait', progress_layout, modal=True, finalize=True)
    progress_bar = progress_window['-PROGRESS-']

    result_queue = load_resident_management_data(api_url)

    while True:
        event, values = progress_window.read(timeout=10)  # Short timeout for rapid update
        if event == sg.WIN_CLOSED:
            break

        # Rapidly update progress bar from 0 to max
        for i in range(progress_max + 1):
            progress_bar.UpdateBar(i)
            # Check for window close event inside the loop
            event, values = progress_window.read(timeout=10)
            if event == sg.WIN_CLOSED or not result_queue.empty():
                break

        if not result_queue.empty():
            results = result_queue.get()
            progress_window.close()
            return results if results else None

    progress_window.close()
    return None