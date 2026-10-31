import ctypes as C
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

APP = Path(__file__).resolve().parent.parent / 'app'
sys.path.insert(0, str(APP))
import windows_shell as shell


class RelaunchTests(unittest.TestCase):
    def test_relaunch_starts_the_app_not_the_browser(self):
        root = Path('TingQiao folder')
        python = root / '.venv/Scripts/pythonw.exe'
        properties = shell.relaunch_properties(root, python)
        self.assertEqual(properties[2], subprocess.list2cmdline([str(python), str(root / 'app/launch.pyw')]))
        self.assertEqual(properties[5], shell.APP_ID)
        self.assertEqual(properties[4], '听桥')
        self.assertTrue(properties[3].endswith('favicon-round.ico,0'))
        self.assertNotIn('msedge.exe', properties[2])


@unittest.skipUnless(sys.platform == 'win32', 'Native Windows Shell properties')
class NativeShellTests(unittest.TestCase):
    def test_shortcut_persists_the_same_app_id(self):
        with tempfile.TemporaryDirectory(prefix='tingqiao shell ') as temp:
            path = Path(temp) / '听桥.lnk'
            shell.write_shortcut(path, APP.parent, Path(sys.executable))
            self.assertTrue(path.exists())
            self.assertEqual(shell.read_shortcut_identity(path), shell.APP_ID)

    def test_window_properties_are_stored_and_read_by_windows(self):
        from ctypes import wintypes
        user = C.WinDLL('user32')
        user.CreateWindowExW.argtypes = [wintypes.DWORD, C.c_wchar_p, C.c_wchar_p, wintypes.DWORD, C.c_int, C.c_int, C.c_int, C.c_int, wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, C.c_void_p]
        user.CreateWindowExW.restype = wintypes.HWND
        user.DestroyWindow.argtypes = [wintypes.HWND]
        hwnd = user.CreateWindowExW(0, 'STATIC', 'TingQiao shell test', 0, 0, 0, 1, 1, None, None, None, None)
        self.assertTrue(hwnd)
        try:
            shell.set_window_identity(hwnd, APP.parent, Path(sys.executable))
            self.assertEqual(shell.read_window_identity(hwnd), shell.relaunch_properties(APP.parent, Path(sys.executable)))
        finally:
            # Release the window property values before destroying this test window.
            with shell._com() as (_, api):
                store = C.c_void_p()
                shell._check(api.SHGetPropertyStoreForWindow(hwnd, C.byref(shell.IID_STORE), C.byref(store)))
                try:
                    for pid in (2, 3, 4, 5):
                        key, value = shell.PROPERTYKEY(shell.FMTID, pid), shell.PROPVARIANT()
                        shell._check(shell._method(store, 6, C.c_long, C.POINTER(shell.PROPERTYKEY), C.POINTER(shell.PROPVARIANT))(store, C.byref(key), C.byref(value)))
                finally:
                    shell._release(store)
            user.DestroyWindow(hwnd)


if __name__ == '__main__':
    unittest.main()
