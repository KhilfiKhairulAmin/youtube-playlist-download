import threading

registered_functions: dict[str, threading.Thread] = dict()
event = threading.Event()


def register_function(func):
  registered_functions[str(func)] = threading.Thread(target=func)


def start_function(func):
  registered_functions[str(func)].start()


def start_all_function():
  for func in registered_functions:
    registered_functions[str(func)].start()


def await_event_set():
  event.wait()


def set_event():
  event.set()


def clear_event():
  event.clear()


def signal_event():
  set_event()
  clear_event()

