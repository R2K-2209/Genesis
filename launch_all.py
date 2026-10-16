"""
AegisRegistry 1-Click Unified Launcher
Starts both the Dynamic FastAPI Backend Server and the Streamlit Dashboard in a single command.
"""

import sys
import os
import time
import subprocess
import threading
import uvicorn
import httpx

# Ensure workspace directory is current directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def start_backend():
    from dynamic_api_server import app
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


def main():
    print("=" * 70)
    print("  🛡️  STARTING AEGISREGISTRY UNIFIED PLATFORM  🛡️")
    print("=" * 70)

    # 1. Start Dynamic API Backend in a background thread
    print("\n[1/2] Starting Dynamic API Server on http://127.0.0.1:8000...")
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # Wait for backend to be live
    time.sleep(2)
    backend_online = False
    for _ in range(5):
        try:
            with httpx.Client(timeout=1.0) as client:
                r = client.get("http://127.0.0.1:8000/api/admin/apis")
                if r.status_code == 200:
                    backend_online = True
                    break
        except Exception:
            time.sleep(1)

    if backend_online:
        print("      [OK] Dynamic API Server is ONLINE!")
    else:
        print("      [WAIT] Server starting up in background...")

    # 2. Launch Streamlit Dashboard
    print("\n[2/2] Launching Interactive Studio Dashboard on http://localhost:8501...")
    print("      Opening browser automatically...\n")

    cmd = [sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.headless=false"]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nStopping AegisRegistry...")


if __name__ == "__main__":
    main()
