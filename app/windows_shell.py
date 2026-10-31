"""Windows taskbar identity for the browser-hosted TingQiao window.

Use the same AppUserModelID on the window and its real launcher shortcut.
The relaunch command must start TingQiao, not a generic Edge window.
"""
import contextlib
import ctypes as C
from pathlib import Path
import subprocess
import sys
import time
import uuid

APP_ID = 'YangXYH.TingQiao'
APP_TITLE = '听桥'
WINDOW_TITLE = '听桥 · 录音识别与分析'


class GUID(C.Structure):
    _fields_ = [('data1', C.c_uint32), ('data2', C.c_uint16), ('data3', C.c_uint16), ('data4', C.c_ubyte * 8)]

    @classmethod
    def parse(cls, value):
        return cls.from_buffer_copy(uuid.UUID(value).bytes_le)


class PROPERTYKEY(C.Structure):
    _fields_ = [('fmtid', GUID), ('pid', C.c_uint32)]


class _Array(C.Structure):
    _fields_ = [('count', C.c_uint32), ('pointer', C.c_void_p)]


class _Value(C.Union):
    _fields_ = [('pointer', C.c_void_p), ('array', _Array), ('number', C.c_int64)]


class PROPVARIANT(C.Structure):
    _fields_ = [('vt', C.c_uint16), ('reserved1', C.c_uint16), ('reserved2', C.c_uint16), ('reserved3', C.c_uint16), ('value', _Value)]


FMTID = GUID.parse('9f4c2855-9f79-4b39-a8d0-e1d42de1d5f3')
IID_STORE = GUID.parse('886d8eeb-8cf2-4446-8d02-cdba1dbdcf99')
IID_LINK = GUID.parse('000214f9-0000-0000-c000-000000000046')
IID_FILE = GUID.parse('0000010b-0000-0000-c000-000000000046')
CLSID_LINK = GUID.parse('00021401-0000-0000-c000-000000000046')


def _check(result):
    if result < 0:
        raise OSError(f'Windows Shell operation failed (0x{result & 0xffffffff:08X})')


def _dlls():
    if sys.platform != 'win32':
        raise OSError('Windows Shell integration is only available on Windows')
    ole = C.OleDLL('ole32')
    shell = C.OleDLL('shell32')
    ole.CoInitializeEx.argtypes = [C.c_void_p, C.c_uint32]
    ole.CoInitializeEx.restype = C.c_long
    ole.CoCreateInstance.argtypes = [C.POINTER(GUID), C.c_void_p, C.c_uint32, C.POINTER(GUID), C.POINTER(C.c_void_p)]
    ole.CoCreateInstance.restype = C.c_long
    ole.PropVariantClear.argtypes = [C.POINTER(PROPVARIANT)]
    shell.SHGetPropertyStoreForWindow.argtypes = [C.c_void_p, C.POINTER(GUID), C.POINTER(C.c_void_p)]
    shell.SHGetPropertyStoreForWindow.restype = C.c_long
    shell.SHGetKnownFolderPath.argtypes = [C.POINTER(GUID), C.c_uint32, C.c_void_p, C.POINTER(C.c_void_p)]
    ole.CoTaskMemFree.argtypes = [C.c_void_p]
    return ole, shell


def _method(pointer, index, result, *args):
    address = C.cast(pointer, C.POINTER(C.POINTER(C.c_void_p))).contents[index]
    return C.WINFUNCTYPE(result, C.c_void_p, *args)(address)


def _release(pointer):
    if pointer:
        _method(pointer, 2, C.c_uint32)(pointer)


def _query(pointer, iid):
    result = C.c_void_p()
    _check(_method(pointer, 0, C.c_long, C.POINTER(GUID), C.POINTER(C.c_void_p))(pointer, C.byref(iid), C.byref(result)))
    return result


@contextlib.contextmanager
def _com():
    ole, shell = _dlls()
    result = ole.CoInitializeEx(None, 2)
    initialized = result in (0, 1)
    if not initialized and result & 0xffffffff != 0x80010106:
        _check(result)
    try:
        yield ole, shell
    finally:
        if initialized:
            ole.CoUninitialize()


def _set_string(store, pid, text):
    key = PROPERTYKEY(FMTID, pid)
    buffer = C.create_unicode_buffer(text)
    value = PROPVARIANT()
    value.vt = 31  # VT_LPWSTR; SetValue copies this borrowed string.
    value.value.pointer = C.cast(buffer, C.c_void_p)
    _check(_method(store, 6, C.c_long, C.POINTER(PROPERTYKEY), C.POINTER(PROPVARIANT))(store, C.byref(key), C.byref(value)))


def _read_string(store, pid, ole):
    key, value = PROPERTYKEY(FMTID, pid), PROPVARIANT()
    _check(_method(store, 5, C.c_long, C.POINTER(PROPERTYKEY), C.POINTER(PROPVARIANT))(store, C.byref(key), C.byref(value)))
    try:
        return C.wstring_at(value.value.pointer) if value.vt == 31 and value.value.pointer else ''
    finally:
        ole.PropVariantClear(C.byref(value))


def relaunch_properties(root, python):
    root = Path(root)
    return {2: subprocess.list2cmdline([str(python), str(root / 'app/launch.pyw')]),
            3: str(root / 'app/static/favicon.ico') + ',0', 4: APP_TITLE, 5: APP_ID}


def set_window_identity(hwnd, root, python):
    with _com() as (_, shell):
        store = C.c_void_p()
        _check(shell.SHGetPropertyStoreForWindow(hwnd, C.byref(IID_STORE), C.byref(store)))
        try:
            # Set relaunch metadata before changing the grouping identity.
            for pid, text in relaunch_properties(root, python).items():
                _set_string(store, pid, text)
        finally:
            _release(store)


def read_window_identity(hwnd):
    with _com() as (ole, shell):
        store = C.c_void_p()
        _check(shell.SHGetPropertyStoreForWindow(hwnd, C.byref(IID_STORE), C.byref(store)))
        try:
            return {pid: _read_string(store, pid, ole) for pid in (2, 3, 4, 5)}
        finally:
            _release(store)


def write_shortcut(path, root, python):
    path, root = Path(path), Path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _com() as (ole, shell):
        link = C.c_void_p()
        _check(ole.CoCreateInstance(C.byref(CLSID_LINK), None, 1, C.byref(IID_LINK), C.byref(link)))
        store = file = None
        try:
            for index, text in ((20, str(python)), (11, subprocess.list2cmdline([str(root / 'app/launch.pyw')])), (9, str(root)), (7, APP_TITLE)):
                _check(_method(link, index, C.c_long, C.c_wchar_p)(link, text))
            _check(_method(link, 17, C.c_long, C.c_wchar_p, C.c_int)(link, str(root / 'app/static/favicon.ico'), 0))
            store = _query(link, IID_STORE)
            _set_string(store, 5, APP_ID)
            _check(_method(store, 7, C.c_long)(store))
            file = _query(link, IID_FILE)
            _check(_method(file, 6, C.c_long, C.c_wchar_p, C.c_int)(file, str(path), 1))
        finally:
            _release(file)
            _release(store)
            _release(link)
        notify = shell.SHChangeNotify
        notify.argtypes = [C.c_long, C.c_uint32, C.c_wchar_p, C.c_void_p]
        notify(0x2000, 0x0005, str(path), None)


def read_shortcut_identity(path):
    with _com() as (ole, _):
        link = C.c_void_p()
        _check(ole.CoCreateInstance(C.byref(CLSID_LINK), None, 1, C.byref(IID_LINK), C.byref(link)))
        file = store = None
        try:
            file = _query(link, IID_FILE)
            _check(_method(file, 5, C.c_long, C.c_wchar_p, C.c_uint32)(file, str(path), 0))
            store = _query(link, IID_STORE)
            return _read_string(store, 5, ole)
        finally:
            _release(store)
            _release(file)
            _release(link)


def _known_folder(folder_id):
    with _com() as (ole, shell):
        pointer = C.c_void_p()
        _check(shell.SHGetKnownFolderPath(C.byref(GUID.parse(folder_id)), 0, None, C.byref(pointer)))
        try:
            return Path(C.wstring_at(pointer))
        finally:
            ole.CoTaskMemFree(pointer)


def prepare_shortcuts(root, python):
    with _com() as (_, shell):
        shell.SetCurrentProcessExplicitAppUserModelID.argtypes = [C.c_wchar_p]
        _check(shell.SetCurrentProcessExplicitAppUserModelID(APP_ID))
    programs = _known_folder('a77f5d77-2e2b-44c3-a6a2-aba601054a51')
    write_shortcut(programs / '听桥.lnk', root, python)
    desktop = _known_folder('b4bfcc3a-db2c-424c-b029-7fe99a87c641') / '听桥.lnk'
    if desktop.exists():
        write_shortcut(desktop, root, python)


def app_windows():
    from ctypes import wintypes
    user = C.WinDLL('user32', use_last_error=True)
    callback_type = C.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user.IsWindowVisible.argtypes = [wintypes.HWND]
    user.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user.GetWindowTextW.argtypes = [wintypes.HWND, C.c_wchar_p, C.c_int]
    found = []
    def visit(hwnd, _):
        if user.IsWindowVisible(hwnd):
            title = C.create_unicode_buffer(user.GetWindowTextLengthW(hwnd) + 1)
            user.GetWindowTextW(hwnd, title, len(title))
            if title.value == WINDOW_TITLE:
                found.append(hwnd)
        return True
    user.EnumWindows(callback_type(visit), 0)
    return found


def update_running_windows(root, python, timeout=0):
    deadline = time.monotonic() + timeout
    while True:
        windows = app_windows()
        for hwnd in windows:
            set_window_identity(hwnd, root, python)
        if windows or time.monotonic() >= deadline:
            return windows
        time.sleep(.2)
