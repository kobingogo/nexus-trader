import signal
import threading
import time

def test_signal():
    try:
        print("Attempting to set signal in thread...")
        signal.signal(signal.SIGALRM, lambda s, f: None)
        print("Success!")
    except ValueError as e:
        print(f"Caught expected error: {e}")

t = threading.Thread(target=test_signal)
t.start()
t.join()
