import urllib.request
import os
import subprocess

print("Downloading Visual Studio C++ Build Tools...")
url = "https://aka.ms/vs/17/release/vs_buildtools.exe"
out_path = "vs_buildtools.exe"

urllib.request.urlretrieve(url, out_path)
print("Download complete. Launching the installer...")

# Launch the installer to install C++ workloads
# We don't use --passive so the user can actually see it and click through if needed
subprocess.Popen([out_path, "--add", "Microsoft.VisualStudio.Workload.VCTools", "--includeRecommended"])
print("Installer launched! Please check your taskbar or screen for the Visual Studio Installer.")
