import threading
import time

event = threading.Event()

def consumer():
    print("Consumer: Waiting for event...")
    event.wait() # Blocks until event is set
    print("Consumer: Event triggered! Processing data...")
    event.wait()
    print("Consumer: Event 2 tiggered! Processing trash...")

def producer():
    print("Producer: Generating data...")
    time.sleep(2)
    event.set() # Triggers the event
    print("Producer: Event set.")
    event.clear()
    time.sleep(2)
    event.set()
    print("Producer: Event 2 set.")

t1 = threading.Thread(target=consumer)
t2 = threading.Thread(target=producer)

t1.start()
t2.start()