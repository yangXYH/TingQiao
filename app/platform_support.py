"""Native credential storage and process locking for Windows and macOS."""
import base64
import contextlib
import sys
import uuid

KEYCHAIN_SERVICE = 'org.tingqiao.model-credentials'
KEYCHAIN_PREFIX = 'keychain:'


def _mac_keyring():
    try:
        # Select the native backend explicitly: never fall back to a file backend.
        from keyring.backends.macOS import Keyring
        return Keyring()
    except Exception:
        raise RuntimeError('无法使用 macOS 钥匙串，请运行安装脚本并解锁登录钥匙串') from None


def _windows_crypt(value, decrypt=False):
    import ctypes
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_ubyte))]

    raw = base64.b64decode(value) if decrypt else value.encode('utf-8')
    buf = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
    incoming, outgoing = Blob(len(raw), buf), Blob()
    if decrypt:
        ok = ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(incoming), None, None, None, None, 1, ctypes.byref(outgoing))
    else:
        ok = ctypes.windll.crypt32.CryptProtectData(ctypes.byref(incoming), '听桥模型凭据', None, None, None, 1, ctypes.byref(outgoing))
    if not ok:
        raise RuntimeError('Windows 无法读取或保存模型密钥，请在模型设置中重新填写')
    try:
        data = ctypes.string_at(outgoing.pbData, outgoing.cbData)
        return data.decode('utf-8') if decrypt else base64.b64encode(data).decode('ascii')
    finally:
        ctypes.windll.kernel32.LocalFree(outgoing.pbData)


def protect_secret(text):
    if not text:
        return ''
    if sys.platform == 'win32':
        return _windows_crypt(text)
    if sys.platform == 'darwin':
        account = uuid.uuid4().hex
        try:
            _mac_keyring().set_password(KEYCHAIN_SERVICE, account, text)
        except Exception:
            raise RuntimeError('无法保存模型密钥，请允许 Python 访问 macOS 登录钥匙串') from None
        return KEYCHAIN_PREFIX + account
    raise RuntimeError('当前仅支持 Windows 和 macOS 的安全密钥存储')


def unprotect_secret(sealed):
    if not sealed:
        return ''
    if sealed.startswith(KEYCHAIN_PREFIX):
        if sys.platform != 'darwin':
            raise RuntimeError('此密钥保存在 Mac 钥匙串中，请在本机重新填写')
        try:
            value = _mac_keyring().get_password(KEYCHAIN_SERVICE, sealed[len(KEYCHAIN_PREFIX):])
        except Exception:
            raise RuntimeError('无法读取模型密钥，请允许 Python 访问 macOS 登录钥匙串') from None
        if value is None:
            raise RuntimeError('钥匙串中没有找到模型密钥，请在模型设置中重新填写')
        return value
    if sys.platform == 'win32':
        return _windows_crypt(sealed, decrypt=True)
    raise RuntimeError('此密钥由 Windows 加密，请在 Mac 上重新填写')


def forget_secret(sealed):
    """Best-effort cleanup after a connection is removed or a key is replaced."""
    if sys.platform == 'darwin' and sealed.startswith(KEYCHAIN_PREFIX):
        try:
            _mac_keyring().delete_password(KEYCHAIN_SERVICE, sealed[len(KEYCHAIN_PREFIX):])
        except Exception:
            pass


@contextlib.contextmanager
def server_lock(path):
    """Hold a kernel-managed file lock; a stale file never blocks a restart."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        handle.seek(0, 2)
        if not handle.tell():
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        try:
            if sys.platform == 'win32':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
            return
        try:
            yield True
        finally:
            handle.seek(0)
            if sys.platform == 'win32':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
