import psutil
import os
import signal

killed = False
for proc in psutil.process_iter(['pid', 'name']):
    try:
        for conn in proc.connections(kind='inet'):
            if conn.laddr.port == 8001:
                print(f"Killing {proc.info['name']} with PID {proc.info['pid']}")
                os.kill(proc.info['pid'], signal.SIGTERM)
                killed = True
    except Exception as e:
        pass

if not killed:
    print("No process found on port 8001.")
