"""Run the mobile API and Telegram worker in one Railway service."""
import logging
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import threading


def main():
    # Telegram HTTP request URLs contain its credential.
    if len(sys.argv) > 1 and sys.argv[1] == "--telegram":
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        runpy.run_path(str(Path(__file__).with_name("telegram_bot.py")), run_name="__main__")
        return 0

    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    children = []
    code = 0
    try:
        children.append(subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "0.0.0.0", "--port", os.environ.get("PORT", "8080")
        ]))
        children.append(subprocess.Popen([sys.executable, __file__, "--telegram"]))
        while not stop.wait(0.5):
            if any(child.poll() is not None for child in children):
                code = 1
                break
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
    return code


if __name__ == "__main__":
    sys.exit(main())
