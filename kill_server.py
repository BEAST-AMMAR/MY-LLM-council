import os
import subprocess

print("Killing python processes...")
os.system("taskkill /F /IM python.exe")
print("Done.")
