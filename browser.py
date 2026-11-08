
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

import websocket  # pip install websocket-client, used to control Chrome

HERE = Path(__file__).resolve().parent
PAGE = HERE / "collector.html" # test page 
DATA = HERE / "our_json_data"   # All the recordings are saved here


def find_browser():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]  # Checks the usual Chrome and Edge paths on Windows and Mac and uses the first one it finds
    for c in candidates:
        if os.path.exists(c):
            return c
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    sys.exit("Couldn't find Chrome or Edge. Install Chrome, or put its path in find_browser().")


def _write_prefs(profile, download_dir):
    # Set the download folder and mark the last exit as clean (no restore pages popup)
    prefs_file = profile / "Default" / "Preferences"
    prefs_file.parent.mkdir(parents=True, exist_ok=True)
    prefs = {}
    if prefs_file.exists():
        try:
            prefs = json.loads(prefs_file.read_text(encoding="utf-8"))
        except Exception:
            prefs = {}
    prefs.setdefault("download", {}).update({
        "default_directory": str(download_dir), "prompt_for_download": False, "directory_upgrade": True})
    prefs.setdefault("savefile", {})["default_directory"] = str(download_dir)
    prefs.setdefault("profile", {}).update({"exit_type": "Normal", "exited_cleanly": True})
    prefs_file.write_text(json.dumps(prefs), encoding="utf-8")


class Session:
    # Opens the page full screen. After the tasks, call wait_for_file() then close()

    def __init__(self, label, level=None, extra=None):
        self.out_dir = DATA / label
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.before = set(self.out_dir.glob("*.json"))

        profile = HERE / ".browser_profile"
        _write_prefs(profile, self.out_dir)

        query = {"label": label}
        if level:
            query["level"] = level
        if label == "bot":
            query["device"] = "pyautogui"
        if extra:
            query.update(extra)
        url = PAGE.as_uri() + "?" + urlencode(query)

        self.proc = subprocess.Popen([
            find_browser(), f"--user-data-dir={profile}", "--no-first-run",
            "--no-default-browser-check", "--hide-crash-restore-bubble",
            "--remote-debugging-port=0",
            "--start-fullscreen", "--new-window", url,
        ])
        self._force_fullscreen(profile)

    def _force_fullscreen(self, profile, timeout=20):
        # macOS sometimes ignores --start-fullscreen, so ask Chrome directly
        # Returns once the page fills the screen, has stopped resizing and has focus
        end = time.time() + timeout
        ws = None
        while ws is None and time.time() < end:      # wait for Chrome and the page to be up
            try:
                port = (profile / "DevToolsActivePort").read_text().split()[0]
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=2))
                tab = next(t for t in tabs if t["type"] == "page" and "collector.html" in t["url"])
                ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=5, suppress_origin=True)
            except (OSError, ValueError, IndexError, StopIteration, websocket.WebSocketException):
                time.sleep(0.2)

        def send(method, **params):
            ws.send(json.dumps({"id": 1, "method": method, "params": params}))
            while True:
                reply = json.loads(ws.recv())
                if reply.get("id") == 1:
                    return reply.get("result", {})

        try:
            last, since, asked = None, time.time(), 0
            while ws and time.time() < end:
                win = send("Browser.getWindowForTarget")
                if win["bounds"].get("windowState") != "fullscreen" and time.time() - asked > 2:
                    send("Browser.setWindowBounds", windowId=win["windowId"], bounds={"windowState": "fullscreen"})
                    asked = time.time()
                send("Page.bringToFront")
                page = send("Runtime.evaluate", returnByValue=True, expression=
                            "[innerWidth, innerHeight, screenX, screenY, screen.width, document.hasFocus()]")["result"]["value"]
                if page != last:
                    last, since = page, time.time()
                if page[0] >= page[4] - 5 and page[5] and time.time() - since > 1:
                    return True
                time.sleep(0.2)
        except (OSError, KeyError, websocket.WebSocketException):
            pass
        finally:
            if ws:
                ws.close()
        print("  WARNING: couldn't make the window full screen. Don't keep this session.")
        return False

    def new_file(self):
        # Returns the session file once it has finished downloading, else None
        done = [p for p in self.out_dir.glob("*.json") if p not in self.before]
        return done[0] if done else None

    def wait_for_file(self, timeout=None):
        # Waits until the page has saved its JSON or the window was closed
        start = time.time()
        while timeout is None or time.time() - start < timeout:
            f = self.new_file()
            if f:
                time.sleep(0.5)
                return f
            if self.proc.poll() is not None:   # user closed the window
                return None
            time.sleep(0.3)
        return None

    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        time.sleep(1)