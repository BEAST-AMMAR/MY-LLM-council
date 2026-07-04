import subprocess
import os

print("Starting LLM Council Project...")

print("1. Starting ML Engine (Backend)...")
backend_python = os.path.abspath(os.path.join("ml_engine", ".venv", "Scripts", "python.exe"))
backend = subprocess.Popen(
    [backend_python, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"],
    cwd="ml_engine"
)

print("2. Starting Next.js App (Frontend)...")
frontend_env = os.environ.copy()
frontend_env["NEXT_TELEMETRY_DISABLED"] = "1"
frontend = subprocess.Popen(
    ["node", os.path.join("node_modules", "next", "dist", "bin", "next"), "dev"],
    cwd="frontend",
    env=frontend_env
)

print("\nProject Launched! The Frontend should be available at http://localhost:3000 shortly.")
print("Press Ctrl+C to stop both servers.\n")

try:
    backend.wait()
    frontend.wait()
except KeyboardInterrupt:
    print("\nStopping servers...")
    backend.terminate()
    frontend.terminate()
