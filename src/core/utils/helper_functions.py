import time


# Back to the menu
def go_back(text):
    return text.lower() in ["back", "b"]


# Skip empty input
def check_if_empty_input(text):
    return len(text.strip()) == 0


def measure_time():
    start_time = time.time()

    def format_elapsed_time():
        total_seconds = time.time() - start_time

        # Calculate whole minutes
        minutes = int(total_seconds // 60)

        # Calculate remaining seconds
        seconds = total_seconds % 60

        # Format the elapsed time
        if minutes > 0:
            return f"{minutes} minutes {seconds:.2f} seconds"
        else:
            return f"{seconds:.2f} seconds"

    return format_elapsed_time
