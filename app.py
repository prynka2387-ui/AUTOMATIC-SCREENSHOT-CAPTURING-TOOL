"""
SnapAuto - Flask Backend
========================
Install:  pip install flask pillow
Run:      python app.py
Open:     http://127.0.0.1:5000
"""

import os
import time
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from PIL import ImageGrab

app = Flask(__name__)

# ── Global state ──────────────────────────────────────────
status = {
    "running": False,
    "taken": 0,
    "total": 0,
    "log": [],
    "folder": "screenshots"
}

stop_event = threading.Event()


# ── Screenshot class ──────────────────────────────────────
class ScreenshotTool:

    def __init__(self, folder="screenshots", interval=5, total=10):
        self.folder   = folder
        self.interval = interval
        self.total    = total

    def take_screenshot(self):
        # Create folder if it doesn't exist
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

        # Make filename using current date and time
        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".png"
        filepath = os.path.join(self.folder, filename)

        # Capture and save
        screenshot = ImageGrab.grab()
        screenshot.save(filepath)
        return filename

    def run(self):
        global status, stop_event
        status["running"] = True
        status["taken"]   = 0
        status["total"]   = self.total
        status["log"]     = []
        status["folder"]  = self.folder
        stop_event.clear()

        self._log(f"Started — {self.total} screenshots every {self.interval}s")

        for i in range(1, self.total + 1):
            if stop_event.is_set():
                self._log("Stopped by user.")
                break

            try:
                filename = self.take_screenshot()
                status["taken"] = i
                self._log(f"[{i}/{self.total}] Saved: {filename}")
            except Exception as e:
                self._log(f"Error: {str(e)}")

            if i < self.total and not stop_event.is_set():
                time.sleep(self.interval)

        status["running"] = False
        self._log(f"Done! {status['taken']} screenshots saved in '{self.folder}'")

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        status["log"].append(f"[{ts}]  {msg}")


# ── Flask routes ──────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    if status["running"]:
        return jsonify({"error": "Already running"}), 400

    data     = request.json
    folder   = data.get("folder",   "screenshots")
    interval = int(data.get("interval", 5))
    total    = int(data.get("total",    10))

    tool = ScreenshotTool(folder=folder, interval=interval, total=total)
    t = threading.Thread(target=tool.run, daemon=True)
    t.start()

    return jsonify({"message": "Started"})


@app.route("/stop", methods=["POST"])
def stop():
    stop_event.set()
    return jsonify({"message": "Stop signal sent"})


@app.route("/status")
def get_status():
    return jsonify(status)


if __name__ == "__main__":
    print("SnapAuto running at http://127.0.0.1:5000")
    app.run(debug=True)
