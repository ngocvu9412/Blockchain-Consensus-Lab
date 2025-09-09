import socket
import json
import threading
import time

DEFAULT_PORTS = [9000,9001,9002,9003,9004]

def send_json(host, port, obj, timeout=3.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.sendall((json.dumps(obj)+'\n').encode())
    except Exception as e:
        print(f"[send_fail] host={host} port={port} err={e}")
        return False
    finally:
        s.close()
    return True

class Server(threading.Thread):
    def __init__(self, port, handler):
        super().__init__(daemon=True)
        self.port = port
        self.handler = handler
        self._stop = False

    def run(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', self.port))
        srv.listen(16)
        srv.settimeout(0.5)
        while not self._stop:
            try:
                conn, addr = srv.accept()
                data = b''
                with conn:
                    conn.settimeout(0.5)
                    while True:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        data += chunk
                        if b'\n' in data:
                            break
                if data:
                    try:
                        obj = json.loads(data.decode().strip())
                        self.handler(obj)
                    except Exception as e:
                        print("SERVER HANDLER ERROR:", e, flush=True)
            except socket.timeout:
                pass
            except Exception:
                time.sleep(0.1)

    def stop(self):
        self._stop = True
