"""Smoke test without user credentials, recordings or model downloads."""
import asyncio
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'app'))
import server


def main():
    import av
    import numpy as np
    import onnxruntime
    import sherpa_onnx
    from faster_whisper.vad import get_speech_timestamps, VadOptions
    assert get_speech_timestamps(np.zeros(16000, dtype=np.float32), VadOptions()) == []
    with tempfile.TemporaryDirectory() as temp:
        config_file = Path(temp) / 'models.json'
        with patch.object(server, 'CONFIG_FILE', config_file):
            assert all(not p['has_key'] for p in server.public_config()['profiles'])
            # New keys used in a connection test must never reach OS storage.
            with patch.object(server, 'protect_secret', side_effect=AssertionError('Transient test persisted a key')):
                resolved = server.resolve_profile('ark', {'api_key': 'test-only'})
                assert resolved['api_key'] == 'test-only'
                assert resolved['secret'] == ''
            payload = {'profiles': [dict(id='ark', name='Test', base_url='https://example.invalid/v1', model='test', api_key='test-only')], 'default_profile': 'ark'}
            class Request:
                async def json(self):
                    return payload
            with patch.object(server, 'protect_secret', return_value='keychain:test-reference'):
                result = asyncio.run(server.set_config(Request()))
            assert result['profiles'][0]['has_key']
            saved = config_file.read_text('utf-8')
            assert 'test-only' not in saved and 'api_key' not in saved
            payload['profiles'][0]['api_key'] = ''
            with patch.object(server, 'unprotect_secret', return_value='test-only'), patch.object(server, 'protect_secret', side_effect=AssertionError('Blank key replaced existing credential')):
                asyncio.run(server.set_config(Request()))
            assert json.loads(config_file.read_text('utf-8'))['profiles'][0]['secret'] == 'keychain:test-reference'
    print('PASS: backend, credential configuration, local VAD and platform ASR dependencies')


if __name__ == '__main__':
    main()
