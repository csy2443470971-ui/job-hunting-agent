"""Job Hunter Agent's window on Windows and Linux (on a Mac, the app is mac/, built by mac/build.sh).

    pythonw -m dashboard.launcher        what the Start menu and desktop icons run (install.ps1 makes them)

It starts the dashboard if it isn't running (and stops it on quit if it started it) and shows it in a native window:
WebView2 on Windows (built into Windows 10 and 11), GTK or Qt on Linux, through pywebview. One window only: opening
it again, or a jobhunter:// link, brings the same window forward.
"""
from __future__ import annotations
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = int(os.getenv("JHA_PORT", "8765"))
URL = f"http://127.0.0.1:{PORT}/"
ICON = ROOT / "docs" / "brand" / "app-icon" / "AppIcon.ico"
HAILING = PORT - 1          # the running window listens here; a second launch says "come forward" and exits


def up() -> bool:
    try:
        return urllib.request.urlopen(URL + "api/config", timeout=1).status == 200
    except Exception:
        return False


def main() -> None:
    os.chdir(ROOT)
    hail = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        hail.bind(("127.0.0.1", HAILING)); hail.listen(4)
    except OSError:                       # already open: bring that window forward instead of opening another
        try:
            socket.create_connection(("127.0.0.1", HAILING), timeout=2).close()
        except OSError:
            pass
        return
    server = None
    if not up():
        (ROOT / "data").mkdir(exist_ok=True)
        log = open(ROOT / "data" / "app.log", "a")
        py = Path(sys.executable)
        if py.name.lower() == "pythonw.exe":          # the server wants a console-less but normal interpreter
            py = py.with_name("python.exe") if py.with_name("python.exe").exists() else py
        flags = 0x08000000 if os.name == "nt" else 0   # CREATE_NO_WINDOW: no console flashing up
        server = subprocess.Popen([str(py), "-m", "dashboard.app"], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
        for _ in range(80):
            if up():
                break
            time.sleep(.25)
    if os.name == "nt":                   # the taskbar groups this window as Job Hunter Agent, not as Python
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("JobHunterAgent.Dashboard")
        except Exception:
            pass
    import webview
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True
    win = webview.create_window("Job Hunter Agent", URL if up() else "data:text/html,<p style='font:15px sans-serif;padding:40px'>"
                                "The dashboard didn't start. See data/app.log in the project folder.</p>",
                                width=1440, height=900, min_size=(760, 520))

    def listen():
        while True:
            try:
                c, _ = hail.accept(); c.close()
                win.restore(); win.show()
                if os.name == "nt":
                    _front(win)
            except Exception:
                pass

    def started():
        threading.Thread(target=listen, daemon=True).start()
        if os.name == "nt" and ICON.exists():
            _set_icon(win)
    try:
        webview.start(started, icon=str(ICON) if ICON.exists() else None, private_mode=False,
                      storage_path=str(ROOT / "data" / "webview"))   # the page's own settings survive a restart
    finally:
        if server and server.poll() is None:
            server.terminate()


def _set_icon(win) -> None:
    """Windows: the window and taskbar show the app icon (pywebview's own icon option is for GTK and Qt)."""
    try:
        import clr  # noqa: F401  (pythonnet, which pywebview's Windows backend uses)
        from System import Action
        from System.Drawing import Icon
        form = win.native
        form.Invoke(Action(lambda: setattr(form, "Icon", Icon(str(ICON)))))
    except Exception:
        pass


def _front(win) -> None:
    try:
        from System import Action
        form = win.native
        form.Invoke(Action(lambda: (form.Activate(), setattr(form, "TopMost", True), setattr(form, "TopMost", False))))
    except Exception:
        pass


if __name__ == "__main__":
    main()
