"""Launch the built, offline application on this computer's loopback interface."""
import argparse
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if not (ROOT / "frontend" / "dist" / "index.html").exists():
        raise SystemExit("Frontend build is missing. Run Setup.cmd first.")

    from app.core.local_only import install_local_only_network_policy
    install_local_only_network_policy()

    import uvicorn
    url = f"http://127.0.0.1:{args.port}"
    server = uvicorn.Server(uvicorn.Config(
        "app.main:app", host="127.0.0.1", port=args.port, access_log=False
    ))

    def open_when_ready():
        while not server.should_exit:
            if server.started:
                webbrowser.open(url)
                return
            time.sleep(.2)

    if not args.no_browser:
        threading.Thread(target=open_when_ready, daemon=True).start()
    print(f"DataMap Studio: {url}\nAll processing stays on this PC. Press Ctrl+C to stop.")
    server.run()

if __name__ == "__main__":
    main()
