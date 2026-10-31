import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import uuid

APP = Path(__file__).resolve().parent.parent / 'app'
sys.path.insert(0, str(APP))
import platform_support as support

loader = importlib.machinery.SourceFileLoader('tingqiao_launcher', str(APP / 'launch.pyw'))
spec = importlib.util.spec_from_loader(loader.name, loader)
launch = importlib.util.module_from_spec(spec)
loader.exec_module(launch)


class CredentialTests(unittest.TestCase):
    def test_empty_credentials_need_no_backend(self):
        with patch.object(support, '_mac_keyring', side_effect=AssertionError('Unexpected keychain access')):
            self.assertEqual(support.protect_secret(''), '')
            self.assertEqual(support.unprotect_secret(''), '')

    def test_macos_stores_only_random_reference(self):
        backend = Mock()
        sample = uuid.uuid4().hex
        with patch.object(sys, 'platform', 'darwin'), patch.object(support, '_mac_keyring', return_value=backend):
            reference = support.protect_secret(sample)
            self.assertTrue(reference.startswith(support.KEYCHAIN_PREFIX))
            self.assertNotIn(sample, reference)
            backend.set_password.assert_called_once_with(support.KEYCHAIN_SERVICE, reference.split(':')[1], sample)
            backend.get_password.return_value = sample
            self.assertEqual(support.unprotect_secret(reference), sample)
            support.forget_secret(reference)
            backend.delete_password.assert_called_once()

    def test_keychain_failure_never_falls_back_or_exposes_error(self):
        sample = uuid.uuid4().hex
        backend = Mock()
        backend.set_password.side_effect = RuntimeError(sample)
        with patch.object(sys, 'platform', 'darwin'), patch.object(support, '_mac_keyring', return_value=backend):
            with self.assertRaises(RuntimeError) as exc:
                support.protect_secret(sample)
            self.assertNotIn(sample, str(exc.exception))
            backend.get_password.return_value = None
            with self.assertRaises(RuntimeError):
                support.unprotect_secret('keychain:missing')

    def test_cross_platform_credentials_require_reentry(self):
        with patch.object(sys, 'platform', 'darwin'):
            with self.assertRaisesRegex(RuntimeError, 'Windows'):
                support.unprotect_secret('previous-dpapi-value')
        with patch.object(sys, 'platform', 'win32'):
            with self.assertRaisesRegex(RuntimeError, 'Mac'):
                support.unprotect_secret('keychain:other-machine')

    @unittest.skipUnless(sys.platform == 'win32', 'Windows native credential round trip')
    def test_native_windows_round_trip(self):
        sample = uuid.uuid4().hex
        sealed = support.protect_secret(sample)
        self.assertNotEqual(sealed, sample)
        self.assertEqual(support.unprotect_secret(sealed), sample)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS native credential round trip')
    def test_native_macos_round_trip(self):
        sample = uuid.uuid4().hex
        reference = support.protect_secret(sample)
        try:
            self.assertEqual(support.unprotect_secret(reference), sample)
        finally:
            support.forget_secret(reference)


class LauncherTests(unittest.TestCase):
    def test_macos_processes_detach_without_windows_flags(self):
        with patch.object(sys, 'platform', 'darwin'):
            self.assertEqual(launch.process_options(), {'start_new_session': True})
            self.assertFalse(launch.focus_windows_app())

    def test_macos_falls_back_to_default_browser(self):
        with patch.object(sys, 'platform', 'darwin'), patch.object(launch, 'ready', return_value=True), patch.object(launch, 'find_browser', return_value=None), patch.object(launch.webbrowser, 'open') as opened:
            launch.main()
            opened.assert_called_once_with(launch.URL)

    def test_macos_browser_gets_separate_profile_without_windows_flags(self):
        browser = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
        with patch.object(sys, 'platform', 'darwin'), patch.object(launch, 'ready', return_value=True), patch.object(launch, 'find_browser', return_value=browser), patch.object(launch.subprocess, 'Popen') as popen:
            launch.main()
            args, kwargs = popen.call_args
            self.assertIn('--app=' + launch.URL, args[0])
            self.assertTrue(kwargs['start_new_session'])
            self.assertNotIn('creationflags', kwargs)

    def test_macos_venv_interpreter_is_selected(self):
        with tempfile.TemporaryDirectory(prefix='tingqiao launch ') as temp:
            root = Path(temp)
            python = root / '.venv/bin/python'
            python.parent.mkdir(parents=True)
            python.touch()
            with patch.object(sys, 'platform', 'darwin'), patch.object(launch, 'ROOT', root):
                self.assertEqual(launch.python_executable(), python)

    def test_server_lock_blocks_another_process_and_releases_after_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'server.lock'
            code = 'import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from platform_support import server_lock\nwith server_lock(Path(sys.argv[2])) as acquired: print(int(acquired))'
            def attempt():
                return subprocess.check_output([sys.executable, '-c', code, str(APP), str(path)], text=True).strip()
            with support.server_lock(path) as acquired:
                self.assertTrue(acquired)
                self.assertEqual(attempt(), '0')
            self.assertEqual(attempt(), '1')


if __name__ == '__main__':
    unittest.main()
