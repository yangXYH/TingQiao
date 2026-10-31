"""Check staged Git blobs without printing potential credential values."""
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
PRIVATE_DIRS = {'data', 'logs', 'runtime', 'models', '.venv', '.cache', 'recordings', 'recycle', 'browser', '__pycache__'}
PRIVATE_NAMES = {'models.json', 'credentials.json', 'secrets.json'}
BLOCKED_SUFFIXES = {'.m4a', '.mp3', '.wav', '.flac', '.ogg', '.aac', '.mp4', '.webm', '.opus', '.wma', '.amr', '.aif', '.aiff', '.onnx', '.exe', '.dll', '.zip', '.7z', '.db', '.pem', '.key', '.pfx', '.p12', '.pyc', '.lnk'}
PATTERNS = {
    'provider API key': re.compile(r'\b(?:ark-[A-Za-z0-9-]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{24,})'),
    'GitHub token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})'),
    'AWS access key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'credential literal': re.compile(r'''["'](?:api_key|api_secret|access_token|secret)["']\s*:\s*["'](?!["'])([^"'\r\n]{12,})["']'''),
    'URL credential': re.compile(r'https?://[^\s/\"\x27]+:[^\s/@\"\x27]+@'),
}


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def main():
    paths = git('diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z').decode('utf-8').split('\0')
    issues = []
    checked = 0
    for name in filter(None, paths):
        path = PurePosixPath(name)
        if (any(part.lower() in PRIVATE_DIRS for part in path.parts)
                or path.name.lower() in PRIVATE_NAMES
                or path.name.startswith('.env') and path.name != '.env.example'
                or path.suffix.lower() in BLOCKED_SUFFIXES
                or '.sqlite' in path.name.lower()):
            issues.append(f'{name}: private data or runtime file')
            continue
        content = git('show', f':{name}')
        checked += 1
        if len(content) > 1024 * 1024:
            issues.append(f'{name}: exceeds the 1 MB source-file limit')
        text = content.decode('utf-8', errors='replace')
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count('\n', 0, match.start()) + 1
                issues.append(f'{name}:{line}: possible {label} (value hidden)')
    if issues:
        print('Release check failed:\n' + '\n'.join(issues))
        return 1
    print(f'Release check passed: {checked} staged source files; no known credentials or private runtime paths detected.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
