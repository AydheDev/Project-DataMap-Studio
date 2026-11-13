"""Launch the built application on loopback. No Node runtime is needed after setup."""
import argparse
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"backend"))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=8000)
    parser.add_argument("--no-browser",action="store_true")
    args=parser.parse_args()
    if not (ROOT/"frontend"/"dist"/"index.html").exists():
        raise SystemExit("Frontend build is missing. Run Setup.cmd first.")
    url=f"http://127.0.0.1:{args.port}"
    def open_when_ready():
        for _ in range(50):
            try:
                with urllib.request.urlopen(url+"/api/health",timeout=1) as response:
                    if response.status==200:
                        webbrowser.open(url)
                        return
            except Exception:
                time.sleep(.2)
    if not args.no_browser:
        threading.Thread(target=open_when_ready,daemon=True).start()
    import uvicorn
    print(f"DataMap Studio: {url}\nKeep this window open. Press Ctrl+C to stop.")
    uvicorn.run("app.main:app",host="127.0.0.1",port=args.port,access_log=False)

if __name__=="__main__":
    main()
