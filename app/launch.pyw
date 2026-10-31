import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent.parent
URL = 'http://127.0.0.1:19331/'


def process_options():
    return {'creationflags': 0x08000000} if sys.platform == 'win32' else {'start_new_session': True}


def python_executable():
    candidates = (ROOT / '.venv/Scripts/pythonw.exe', ROOT / 'runtime/python/pythonw.exe') if sys.platform == 'win32' else (ROOT / '.venv/bin/python',)
    return next((p for p in candidates if p.exists()), Path(sys.executable))


def find_browser():
    if sys.platform == 'darwin':
        names = ('Google Chrome.app/Contents/MacOS/Google Chrome', 'Microsoft Edge.app/Contents/MacOS/Microsoft Edge', 'Chromium.app/Contents/MacOS/Chromium')
        candidates = [folder / name for folder in (Path('/Applications'), Path.home() / 'Applications') for name in names]
    elif sys.platform == 'win32':
        candidates = [Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'Microsoft/Edge/Application/msedge.exe', Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Microsoft/Edge/Application/msedge.exe', Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Google/Chrome/Application/chrome.exe']
    else:
        candidates = []
    return next((p for p in candidates if p.exists()), None)


def ready():
    try:
        with urllib.request.urlopen(URL + 'api/health', timeout=1) as response:
            return json.load(response).get('app') == '听桥'
    except Exception:
        return False


def windows_identity(timeout=0, shortcuts=False):
    if sys.platform != 'win32':
        return
    try:
        from windows_shell import prepare_shortcuts, update_running_windows
        if shortcuts:
            prepare_shortcuts(ROOT, python_executable())
        if not shortcuts or timeout:
            update_running_windows(ROOT, python_executable(), timeout)
    except OSError as exc:
        logs = ROOT / 'logs'
        logs.mkdir(exist_ok=True)
        with (logs / 'launcher.log').open('a', encoding='utf-8') as out:
            out.write(f'Taskbar integration: {exc}\n')


def focus_windows_app():
    if sys.platform != 'win32':
        return False
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    found = []

    def find(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            text = ctypes.create_unicode_buffer(user32.GetWindowTextLengthW(hwnd) + 1)
            user32.GetWindowTextW(hwnd, text, len(text))
            if text.value == '听桥 · 录音识别与分析':
                found.append(hwnd)
        return True

    user32.EnumWindows(callback_type(find), 0)
    if not found:
        return False
    windows_identity()
    user32.ShowWindow(found[0], 9)
    user32.SetForegroundWindow(found[0])
    return True


def main():
    if sys.platform not in ('win32', 'darwin'):
        raise SystemExit('当前支持 Windows 和 macOS。')
    windows_identity(shortcuts=True)
    if not ready():
        logs = ROOT / 'logs'
        logs.mkdir(exist_ok=True)
        (ROOT / 'data').mkdir(exist_ok=True)
        with (logs / 'server.log').open('a', encoding='utf-8') as out, (logs / 'server-error.log').open('a', encoding='utf-8') as err:
            process = subprocess.Popen([str(python_executable()), str(ROOT / 'app/server.py')], cwd=str(ROOT), stdout=out, stderr=err, **process_options())
            (ROOT / 'data/server.pid').write_text(str(process.pid), 'ascii')
        for _ in range(100):
            if ready():
                break
            if process.poll() is not None:
                if ready():
                    break
                raise SystemExit('听桥服务未能启动，请查看 logs/server-error.log。')
            time.sleep(.2)
        else:
            raise SystemExit('听桥服务启动超时，请查看 logs/server-error.log。')
    if focus_windows_app():
        return
    browser = find_browser()
    if browser:
        args = [str(browser), '--app=' + URL, '--user-data-dir=' + str(ROOT / 'data/browser'), '--no-first-run', '--no-default-browser-check', '--disable-sync', '--disable-extensions', '--disable-features=msEdgeSidebarV2,msEdgeFirstRunExperience,msImplicitSignin', '--window-size=1400,930']
        if os.environ.get('TINGQIAO_DEBUG') == '1':
            args += ['--remote-debugging-port=19332', '--remote-debugging-address=127.0.0.1']
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **process_options())
        windows_identity(timeout=15)
    else:
        webbrowser.open(URL)


if __name__ == '__main__':
    main()
