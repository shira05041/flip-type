"""Thin ctypes wrappers around the Win32 APIs FlipType needs."""

import ctypes
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# ---- constants -------------------------------------------------------------
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
WM_INPUTLANGCHANGEREQUEST = 0x0050

VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LWIN = 0x5B
VK_RWIN = 0x5C

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002

ERROR_ALREADY_EXISTS = 183

LANG_HEBREW = 0x0D
LANG_ENGLISH = 0x09

ULONG_PTR = ctypes.c_size_t


# ---- SendInput structures --------------------------------------------------
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


# ---- prototypes ------------------------------------------------------------
user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL
user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype = wintypes.UINT
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetKeyboardLayoutList.argtypes = [ctypes.c_int, ctypes.POINTER(wintypes.HKL)]
user32.GetKeyboardLayoutList.restype = ctypes.c_int
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.CreateMutexW.restype = wintypes.HANDLE


# ---- hotkey ----------------------------------------------------------------
def current_thread_id() -> int:
    return kernel32.GetCurrentThreadId()


def run_hotkey_loop(modifiers: int, vk: int, callback, on_registered=None) -> None:
    """Register a global hotkey and pump messages on the *calling* thread until WM_QUIT.

    on_registered(ok: bool) is called once after registration is attempted.
    """
    hotkey_id = 1
    ok = bool(user32.RegisterHotKey(None, hotkey_id, modifiers | MOD_NOREPEAT, vk))
    if on_registered:
        on_registered(ok)
    if not ok:
        return
    try:
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY and msg.wParam == hotkey_id:
                try:
                    callback()
                except Exception:  # never let one failure kill the hotkey loop
                    import traceback
                    traceback.print_exc()
    finally:
        user32.UnregisterHotKey(None, hotkey_id)


def stop_hotkey_loop(thread_id: int) -> None:
    user32.PostThreadMessageW(thread_id, WM_QUIT, 0, 0)


# ---- keyboard --------------------------------------------------------------
def _key_down(vk: int) -> bool:
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def wait_keys_released(extra_vks=(), timeout: float = 2.0) -> None:
    """Wait until the user lets go of modifier keys (and the hotkey's letter)."""
    vks = (VK_CONTROL, VK_SHIFT, VK_MENU, VK_LWIN, VK_RWIN, *extra_vks)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and any(_key_down(vk) for vk in vks):
        time.sleep(0.01)


def _key_input(vk: int, up: bool) -> INPUT:
    inp = INPUT(type=INPUT_KEYBOARD)
    inp.u.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=KEYEVENTF_KEYUP if up else 0, time=0, dwExtraInfo=0)
    return inp


def send_ctrl(letter: str) -> None:
    """Send Ctrl+<letter>, e.g. send_ctrl('C')."""
    vk = ord(letter.upper())
    seq = [_key_input(VK_CONTROL, False), _key_input(vk, False),
           _key_input(vk, True), _key_input(VK_CONTROL, True)]
    arr = (INPUT * len(seq))(*seq)
    user32.SendInput(len(seq), arr, ctypes.sizeof(INPUT))


# ---- keyboard layout -------------------------------------------------------
def _installed_layouts() -> list[int]:
    n = user32.GetKeyboardLayoutList(0, None)
    buf = (wintypes.HKL * n)()
    user32.GetKeyboardLayoutList(n, buf)
    return [h or 0 for h in buf]


def switch_layout(lang: str) -> bool:
    """Ask the foreground window to switch to the installed Hebrew ('he') or English ('en') layout."""
    primary = LANG_HEBREW if lang == "he" else LANG_ENGLISH
    for hkl in _installed_layouts():
        if (hkl & 0x3FF) == primary:  # low word = LANGID, low 10 bits = primary language
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                lparam = ctypes.c_ssize_t(hkl).value  # HKL may exceed signed LPARAM range
                return bool(user32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, lparam))
    return False


# ---- single instance -------------------------------------------------------
_mutex_handle = None


def acquire_single_instance(name: str) -> bool:
    """Return False if another instance already holds the named mutex."""
    global _mutex_handle
    _mutex_handle = kernel32.CreateMutexW(None, False, name)
    return ctypes.get_last_error() != ERROR_ALREADY_EXISTS
