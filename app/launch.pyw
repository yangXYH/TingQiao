import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import webbrowser

root=Path(__file__).resolve().parent.parent
url='http://127.0.0.1:19331/'
def ready():
    try:
        with urllib.request.urlopen(url+'api/health',timeout=1) as r:
            return json.load(r).get('app')=='听桥'
    except Exception:
        return False

if not ready():
    logs=root/'logs';logs.mkdir(exist_ok=True)
    python=next((p for p in (root/'.venv/Scripts/pythonw.exe',root/'runtime/python/pythonw.exe') if p.exists()),Path(sys.executable))
    with (logs/'server.log').open('a',encoding='utf-8') as out,(logs/'server-error.log').open('a',encoding='utf-8') as err:
        p=subprocess.Popen([str(python),str(root/'app/server.py')],cwd=str(root),stdout=out,stderr=err,creationflags=0x08000000)
        (root/'data/server.pid').write_text(str(p.pid),'ascii')
    for _ in range(100):
        if ready():break
        time.sleep(.2)
    else:
        ctypes.windll.user32.MessageBoxW(None,'听桥服务未能启动。请检查 logs 文件夹中的 server-error.log。','听桥',16)
        raise SystemExit(1)

# Reuse the existing application window when the shortcut is opened again.
found=[]
callback_type=ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.c_void_p,ctypes.c_void_p)
def find_window(hwnd,_):
    if ctypes.windll.user32.IsWindowVisible(hwnd):
        length=ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        text=ctypes.create_unicode_buffer(length+1)
        ctypes.windll.user32.GetWindowTextW(hwnd,text,length+1)
        if '听桥 · 录音识别与分析' in text.value:
            found.append(hwnd)
    return True
ctypes.windll.user32.EnumWindows(callback_type(find_window),0)
if found:
    ctypes.windll.user32.ShowWindow(found[0],9)
    ctypes.windll.user32.SetForegroundWindow(found[0])
    raise SystemExit(0)

browser=next((p for p in [Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft/Edge/Application/msedge.exe',Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Microsoft/Edge/Application/msedge.exe',Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Google/Chrome/Application/chrome.exe'] if p.exists()),None)
if browser:
    args=[str(browser),'--app='+url,'--user-data-dir='+str(root/'data/browser'),'--no-first-run','--no-default-browser-check','--disable-sync','--disable-extensions','--disable-features=msEdgeSidebarV2,msEdgeFirstRunExperience,msImplicitSignin','--window-size=1400,930']
    if os.environ.get('TINGQIAO_DEBUG')=='1':args+=['--remote-debugging-port=19332','--remote-debugging-address=127.0.0.1']
    subprocess.Popen(args,creationflags=0x08000000)
else:
    webbrowser.open(url)
