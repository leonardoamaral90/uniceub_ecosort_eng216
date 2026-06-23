import socket
import sys
import time

host = sys.argv[1]
port = int(sys.argv[2])
timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 60

start = time.time()
while time.time() - start < timeout:
    try:
        with socket.create_connection((host, port), timeout=2):
            sys.exit(0)
    except OSError:
        time.sleep(1)

sys.exit(1)
