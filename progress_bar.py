import threading
import queue
import PySimpleGUI as sg
import api_functions
import config

API_URL = config.API_URL

# --------------------------------- General Purpose Single Function Progress Bar -----------------------------------
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


# --------------------------------- Resident Management Data Loading -----------------------------------
def load_resident_management_data(api_url, selected_resident=None):
    """
    Load data required for the resident management section by making multiple API calls.
    This function runs in a separate thread and uses a queue to return data to the main thread.
    """
    result_queue = queue.Queue()

    def worker():
        try:
            # Pre-existing calls
            #resident_names = api_functions.get_resident_names(api_url)
            resident_names = api_functions.get_resident_names(api_url) if config.global_config['resident_names'] is None else config.global_config['resident_names']
            if resident_names == 'token_expired':
                result_queue.put('token_expired')
                return
            resident_names = sorted(resident_names)
            config.global_config['resident_names'] = resident_names
            
            user_initials = api_functions.get_user_initials(api_url) if config.global_config['user_initials'] is None else config.global_config['user_initials']
            if user_initials == 'token_expired':
                result_queue.put('token_expired')
                return
            config.global_config['user_initials'] = user_initials

            #selected_resident_name = resident_names[0]
            if selected_resident is None:
                selected_resident_name = resident_names[0]
            else:
                selected_resident_name = selected_resident


            # Fetching ADL data
            existing_adl_data = api_functions.fetch_adl_data_for_resident(api_url, selected_resident_name)
            if existing_adl_data == 'token_expired':
                result_queue.put('token_expired')
                return
            
            resident_care_levels = api_functions.get_resident_care_level(api_url) if config.global_config['resident_care_levels'] is None else config.global_config['resident_care_levels']
            if resident_care_levels == 'token_expired':
                result_queue.put('token_expired')
                return
            config.global_config['resident_care_levels'] = resident_care_levels
            

            # Fetching EMAR data
            all_medications_data = api_functions.fetch_medications_for_resident(api_url, selected_resident_name)
            if all_medications_data == 'token_expired':
                result_queue.put('token_expired')
                return

            # Extracting medication names and removing duplicates
            scheduled_meds = [med_name for time_slot in all_medications_data['Scheduled'].values() for med_name in time_slot]
            prn_meds = list(all_medications_data['PRN'].keys())
            controlled_meds = list(all_medications_data['Controlled'].keys())
            all_meds = list(set(scheduled_meds + prn_meds + controlled_meds))

            active_medications = api_functions.filter_active_medications(api_url, selected_resident_name, all_meds)
            if active_medications == 'token_expired':
                result_queue.put('token_expired')
                return
            
            non_medication_orders = api_functions.fetch_all_non_medication_orders(api_url, selected_resident_name)
            if non_medication_orders == 'token_expired':
                result_queue.put('token_expired')
                return
            
            existing_emar_data = api_functions.fetch_emar_data_for_resident(api_url, selected_resident_name)
            if existing_emar_data == 'token_expired':
                result_queue.put('token_expired')
                return
            
            # Package the results
            results = (resident_names, user_initials, existing_adl_data, resident_care_levels, all_medications_data, active_medications, non_medication_orders, existing_emar_data)
            result_queue.put(results)
        except Exception as e:
            sg.popup_error(f"Failed to load data: {e}", title="Loading Error")
            result_queue.put(None)

    threading.Thread(target=worker, daemon=True).start()
    return result_queue


def show_loading_window(api_url, selected_resident=None):
    """
    Show a loading window while the resident management data is being loaded.
    
    :param api_url: The URL of the API to load the resident management data from.
    :param selected_resident: Optional parameter to specify a specific resident to load.
    
    :return: The loaded resident management data, or None if there was an error.
    """
    progress_max = 100  # Define maximum progress bar value for quick fill
    progress_layout = [
        [sg.Text('Loading Resident Management Data...')],
        [sg.ProgressBar(progress_max, orientation='h', size=(20, 20), key='-PROGRESS-')]
    ]
    progress_window = sg.Window('Please Wait', progress_layout, modal=True, finalize=True)
    progress_bar = progress_window['-PROGRESS-']

    result_queue = load_resident_management_data(api_url, selected_resident)

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


#---------------------------------- eMar Data Loading -------------------------------

def load_emar_data(api_url, resident_name, year_month):
    """
    Load eMAR data required for showing the eMAR chart by making multiple API calls.
    This function runs in a separate thread and uses a queue to return data to the main thread.
    """
    result_queue = queue.Queue()

    def worker():
        try:
            # Fetch eMAR data for the month
            emar_data = api_functions.fetch_emar_data_for_month(api_url, resident_name, year_month)
            if emar_data == 'token_expired':
                result_queue.put('token_expired')
                return

            # Fetch discontinued medications with their discontinuation dates
            discontinued_medications = api_functions.fetch_discontinued_medications(api_url, resident_name)
            if discontinued_medications == 'token_expired':
                result_queue.put('token_expired')
                return

            # Fetch original structure of medications for the resident
            original_structure = api_functions.fetch_medications_for_resident(api_url, resident_name)
            if original_structure == 'token_expired':
                result_queue.put('token_expired')
                return

            # Package the results
            results = (emar_data, discontinued_medications, original_structure)
            result_queue.put(results)
        except Exception as e:
            sg.popup_error(f"Failed to load eMAR data: {e}", title="Loading Error")
            result_queue.put(None)

    threading.Thread(target=worker, daemon=True).start()
    return result_queue


def show_loading_window_for_emar(api_url, resident_name, year_month):
    """
    Show a loading window while the eMAR data is being loaded.
    """
    progress_max = 100  # Define maximum progress bar value for quick fill
    progress_layout = [
        [sg.Text('Loading eMAR Data...')],
        [sg.ProgressBar(progress_max, orientation='h', size=(20, 20), key='-PROGRESS-')]
    ]
    progress_window = sg.Window('Please Wait', progress_layout, modal=True, finalize=True)
    progress_bar = progress_window['-PROGRESS-']

    result_queue = load_emar_data(api_url, resident_name, year_month)

    while True:
        event, values = progress_window.read(timeout=10)  # Short timeout for rapid update
        if event == sg.WIN_CLOSED:
            break

        for i in range(progress_max + 1):
            progress_bar.UpdateBar(i)
            event, values = progress_window.read(timeout=10)
            if event == sg.WIN_CLOSED or not result_queue.empty():
                break

        if not result_queue.empty():
            results = result_queue.get()
            progress_window.close()
            return results if results else None

    progress_window.close()
    return None

#----------------------------------- Meal Data Loading -----------------------------------

def load_meal_data(api_url):
    """
    Load meal data by making multiple API calls.
    This function runs in a separate thread and uses a queue to return data to the main thread.
    """
    result_queue = queue.Queue()

    def worker():
        try:
            # Fetch meal data
            breakfast = api_functions.fetch_raw_meal_data(api_url, 'breakfast')
            lunch = api_functions.fetch_raw_meal_data(api_url, 'lunch')
            dinner = api_functions.fetch_raw_meal_data(api_url, 'dinner')

            # Package the results
            results = (breakfast, lunch, dinner)
            result_queue.put(results)
        except Exception as e:
            sg.popup_error(f"Failed to load meal data: {e}", title="Loading Error")
            result_queue.put(None)

    threading.Thread(target=worker, daemon=True).start()
    return result_queue


def show_loading_window_for_meals(api_url):
    """
    Show a loading window while the meal data is being loaded.
    """
    progress_max = 100  # Define maximum progress bar value for quick fill
    progress_layout = [
        [sg.Text('Loading Meal Data...')],
        [sg.ProgressBar(progress_max, orientation='h', size=(20, 20), key='-PROGRESS-')]
    ]
    progress_window = sg.Window('Please Wait', progress_layout, modal=True, finalize=True)
    progress_bar = progress_window['-PROGRESS-']

    result_queue = load_meal_data(api_url)

    while True:
        event, values = progress_window.read(timeout=10)  # Short timeout for rapid update
        if event == sg.WIN_CLOSED:
            break

        for i in range(progress_max + 1):
            progress_bar.UpdateBar(i)
            event, values = progress_window.read(timeout=10)
            if event == sg.WIN_CLOSED or not result_queue.empty():
                break

        if not result_queue.empty():
            results = result_queue.get()
            progress_window.close()
            return results if results else None

    progress_window.close()
    return None

