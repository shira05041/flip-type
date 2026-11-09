"""FlipType main: tray icon + global hotkey (Ctrl+Shift+Q) that flips the selected text's layout."""

import os
import sys
import threading
import time
import winreg

import pystray
from PIL import Image, ImageDraw, ImageFont

from fliptype import clipboard, winapi
from fliptype.converter import convert

APP_NAME = "FlipType"
HOTKEY_MODS = winapi.MOD_CONTROL | winapi.MOD_SHIFT
HOTKEY_VK = ord("Q")
HOTKEY_LABEL = "Ctrl+Shift+Q"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


# ---- the actual flip -------------------------------------------------------
def flip_selection() -> None:
    winapi.wait_keys_released(extra_vks=(HOTKEY_VK,))

    try:
        saved = clipboard.snapshot()
    except OSError:
        saved = []

    before = clipboard.sequence_number()
    winapi.send_ctrl("C")

    # Wait for the target app to put the selection on the clipboard.
    deadline = time.monotonic() + 0.5
    while clipboard.sequence_number() == before and time.monotonic() < deadline:
        time.sleep(0.01)
    if clipboard.sequence_number() == before:
        return  # nothing selected / app ignored Ctrl+C

    text = clipboard.get_text()
    if not text:
        return

    converted, target = convert(text)
    clipboard.set_text(converted)
    winapi.send_ctrl("V")
    winapi.switch_layout(target)

    # Give the app time to read the clipboard before restoring the user's content.
    time.sleep(0.3)
    if saved:
        try:
            clipboard.restore(saved)
        except OSError:
            pass


# ---- autostart -------------------------------------------------------------
def _launch_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "FlipType.pyw")
    return f'"{pythonw}" "{script}"'


def autostart_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, APP_NAME)
            return True
    except OSError:
        return False


def set_autostart(enabled: bool) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if enabled:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _launch_command())
        else:
            try:
                winreg.DeleteValue(k, APP_NAME)
            except FileNotFoundError:
                pass


# ---- tray icon -------------------------------------------------------------
def _make_icon() -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=14, fill=(37, 99, 235, 255))
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except OSError:
        font = ImageFont.load_default()
    d.text((8, 15), "A", font=font, fill="white")
    d.text((34, 15), "א", font=font, fill=(253, 224, 71, 255))
    return img


def main() -> None:
    if not winapi.acquire_single_instance("Local\\FlipTypeSingleInstance"):
        return

    hotkey_thread_id = {}
    registered = threading.Event()
    result = {"ok": False}

    def on_registered(ok: bool) -> None:
        result["ok"] = ok
        registered.set()

    def hotkey_worker() -> None:
        hotkey_thread_id["id"] = winapi.current_thread_id()
        winapi.run_hotkey_loop(HOTKEY_MODS, HOTKEY_VK, flip_selection, on_registered)

    threading.Thread(target=hotkey_worker, daemon=True).start()
    registered.wait(2)

    def toggle_autostart(icon, item):
        set_autostart(not autostart_enabled())

    def quit_app(icon, item):
        if "id" in hotkey_thread_id:
            winapi.stop_hotkey_loop(hotkey_thread_id["id"])
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem(f"FlipType – {HOTKEY_LABEL}", None, enabled=False),
        pystray.MenuItem("הפעלה עם Windows", toggle_autostart, checked=lambda item: autostart_enabled()),
        pystray.MenuItem("יציאה", quit_app),
    )
    icon = pystray.Icon(APP_NAME, _make_icon(), f"FlipType ({HOTKEY_LABEL})", menu)

    def on_ready(icon):
        icon.visible = True
        if result["ok"]:
            icon.notify(f"סמנו טקסט ולחצו {HOTKEY_LABEL} להמרה", "FlipType פועל")
        else:
            icon.notify(f"הקיצור {HOTKEY_LABEL} תפוס על ידי תוכנה אחרת", "FlipType – שגיאה")

    icon.run(setup=on_ready)


if __name__ == "__main__":
    main()
