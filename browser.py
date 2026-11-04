"""
Shared helper: opens collector.html in its own full-screen Chrome/Edge window
(a separate profile, so it never touches your normal browser) and saves the
downloaded session file straight into the right data folder.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
PAGE = HERE / "collector.html"
DATA = HERE / "our_json_data"     


def find_browser():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    sys.exit("Couldn't find Chrome or Edge. Install Chrome, or put its path in find_browser().")


def _write_prefs(profile, download_dir):
    """Set the download folder and mark the last exit as clean (no 'restore pages?' popup)."""
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
    """Usage:
        s = Session(label="bot", level="easy")   # opens the page full screen
        ... do the tasks ...
        s.wait_for_file(); s.close()
    """

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
            "--start-fullscreen", "--new-window", url,
        ])

    def new_file(self):
        """Return the session file once it has finished downloading, else None."""
        done = [p for p in self.out_dir.glob("*.json") if p not in self.before]
        return done[0] if done else None

    def wait_for_file(self, timeout=None):
        """Wait until the page has saved its JSON (or the window was closed)."""
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