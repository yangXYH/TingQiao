"""Download only the public SenseVoice model files; never read app settings."""
from pathlib import Path
import shutil
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
MODEL = 'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17'
URL = f'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{MODEL}.tar.bz2'
FILES = ('model.int8.onnx', 'tokens.txt', 'LICENSE')


def main():
    target = ROOT / 'models' / 'sensevoice'
    if all((target / name).is_file() and (target / name).stat().st_size > 0 for name in FILES):
        print('SenseVoice is already installed.')
        return
    cache = ROOT / '.cache' / 'models'
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / f'{MODEL}.tar.bz2'
    if not archive.exists():
        partial = archive.with_suffix('.part')
        print('Downloading the public SenseVoice int8 model (about 240 MB)...')
        urllib.request.urlretrieve(URL, partial)
        partial.replace(archive)
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, 'r:bz2') as bundle:
        # Copy only the exact public files. Do not extract paths from the archive.
        for name in FILES:
            member = bundle.getmember(f'{MODEL}/{name}')
            if not member.isfile():
                raise ValueError(f'Invalid model archive entry: {name}')
            with bundle.extractfile(member) as source, (target / name).with_suffix('.part').open('wb') as dest:
                shutil.copyfileobj(source, dest)
            (target / name).with_suffix('.part').replace(target / name)
    print('SenseVoice installed in models/sensevoice.')


if __name__ == '__main__':
    main()
