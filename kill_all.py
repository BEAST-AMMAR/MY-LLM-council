import os, subprocess
# Kill all python and node processes
for proc in ["python.exe", "node.exe"]:
    try:
        os.system(f"taskkill /F /IM {proc}")
    except:
        pass
print("All server processes killed.")
