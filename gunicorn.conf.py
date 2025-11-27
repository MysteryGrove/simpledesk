import multiprocessing

# Number of worker processes based on CPU count
workers = max(2, multiprocessing.cpu_count() * 2 + 1)

# Use an asynchronous worker class to better handle concurrent requests
worker_class = "gevent"
