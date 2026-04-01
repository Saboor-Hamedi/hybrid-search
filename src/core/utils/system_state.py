# Global State for System Operations
# Allows cross-module communication for long-running tasks

# In-memory flag for stopping active indexing jobs
stop_requested = False

# Active jobs count
active_indexing_jobs = 0

def request_stop():
    global stop_requested
    stop_requested = True

def clear_stop():
    global stop_requested
    stop_requested = False

def is_stop_requested():
    return stop_requested
