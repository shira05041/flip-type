"""Clipboard access via ctypes, including snapshot/restore of the user's clipboard."""

import ctypes
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

# Formats whose handle is NOT an HGLOBAL (GDI objects etc.) - can't be copied byte-wise.
# CF_BITMAP, CF_METAFILEPICT, CF_PALETTE, CF_ENHMETAFILE, CF_OWNERDISPLAY, CF_DSP* variants.
_NON_HGLOBAL = {2, 3, 9, 14, 0x0080, 0x0082, 0x0083, 0x008E}

user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL
user32.CloseClipboard.restype = wintypes.BOOL
user32.EmptyClipboard.restype = wintypes.BOOL
user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE
user32.EnumClipboardFormats.argtypes = [wintypes.UINT]
user32.EnumClipboardFormats.restype = wintypes.UINT
user32.GetClipboardSequenceNumber.restype = wintypes.DWORD
kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalSize.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalSize.restype = ctypes.c_size_t
kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]


class _Open:
    """Context manager that opens the clipboard, retrying while another app holds it."""

    def __enter__(self):
        for _ in range(50):
            if user32.OpenClipboard(None):
                return self
            time.sleep(0.01)
        raise OSError("Could not open clipboard")

    def __exit__(self, *exc):
        user32.CloseClipboard()


def sequence_number() -> int:
    return user32.GetClipboardSequenceNumber()


def _alloc(data: bytes):
    h = kernel32.GlobalAlloc(GMEM_MOVEABLE, max(len(data), 1))
    if not h:
        raise MemoryError("GlobalAlloc failed")
    p = kernel32.GlobalLock(h)
    ctypes.memmove(p, data, len(data))
    kernel32.GlobalUnlock(h)
    return h


def get_text() -> str | None:
    with _Open():
        h = user32.GetClipboardData(CF_UNICODETEXT)
        if not h:
            return None
        p = kernel32.GlobalLock(h)
        try:
            return ctypes.wstring_at(p)
        finally:
            kernel32.GlobalUnlock(h)


def set_text(text: str) -> None:
    data = (text + "\0").encode("utf-16-le")
    with _Open():
        user32.EmptyClipboard()
        h = _alloc(data)
        if not user32.SetClipboardData(CF_UNICODETEXT, h):
            kernel32.GlobalFree(h)


def snapshot() -> list[tuple[int, bytes]]:
    """Copy every byte-copyable format currently on the clipboard."""
    items = []
    with _Open():
        fmt = user32.EnumClipboardFormats(0)
        while fmt:
            if fmt not in _NON_HGLOBAL:
                h = user32.GetClipboardData(fmt)
                if h:
                    p = kernel32.GlobalLock(h)
                    if p:
                        try:
                            items.append((fmt, ctypes.string_at(p, kernel32.GlobalSize(h))))
                        finally:
                            kernel32.GlobalUnlock(h)
            fmt = user32.EnumClipboardFormats(fmt)
    return items


def restore(items: list[tuple[int, bytes]]) -> None:
    with _Open():
        user32.EmptyClipboard()
        for fmt, data in items:
            h = _alloc(data)
            if not user32.SetClipboardData(fmt, h):
                kernel32.GlobalFree(h)
