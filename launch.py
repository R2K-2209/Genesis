"""
Unified Launcher for Genesis / AegisRegistry.
Starts both the FastAPI Backend (port 8000) and the React Vite Frontend (port 5173).
"""

import sys
import os
import subprocess
import time
import webbrowser

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")

    print("=" * 60)
    print("🛡️  Starting AegisRegistry Platform")
    print("=" * 60)

    # 1. Start FastAPI backend
    print("🚀 Launching FastAPI Backend on http://localhost:8000 ...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=root_dir
    )

    # 2. Wait briefly
    time.sleep(2)

    # 3. Start React Vite frontend
    print("✨ Launching React (Vite) Frontend on http://localhost:5173 ...")
    frontend_cmd = "npm run dev -- --host 0.0.0.0 --port 5173"
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=frontend_dir,
        shell=True
    )

    time.sleep(2)
    print("\n✅ Both servers are online!")
    print("👉 Frontend: http://localhost:5173")
    print("👉 Backend API: http://localhost:8000")
    print("👉 OpenAPI Docs: http://localhost:8000/docs\n")
    print("Press Ctrl+C to stop both servers.")

    try:
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        frontend_proc.terminate()
        backend_proc.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
