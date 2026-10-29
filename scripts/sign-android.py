#!/usr/bin/env python3
"""Sign aligned APKs with the fixed release identity and verify before publication."""
import base64
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile


def verify(apksigner, apk, pin):
    result = subprocess.run([str(apksigner), 'verify', '--verbose', '--print-certs-pem', str(apk)],
                            check=True, capture_output=True, text=True)
    certificates = re.findall(r'-----BEGIN CERTIFICATE-----(.*?)-----END CERTIFICATE-----', result.stdout, re.S)
    fingerprints = {hashlib.sha256(base64.b64decode(''.join(c.split()), validate=True)).hexdigest()
                    for c in certificates}
    if fingerprints != {pin}:
        raise ValueError('APK does not have exactly the pinned release certificate')


def main():
    pin = Path(__file__).with_name('android-certificate.sha256').read_text().strip()
    if not re.fullmatch('[0-9a-f]{64}', pin):
        raise ValueError('Invalid release certificate pin')
    for name in ('ANDROID_SIGNING_STORE', 'ANDROID_SIGNING_PASSWORD', 'ANDROID_SIGNING_ALIAS'):
        if not os.environ.get(name):
            raise ValueError('Missing ' + name)
    store = Path(os.environ['ANDROID_SIGNING_STORE'])
    if store.is_symlink() or not store.is_file():
        raise ValueError('Missing or unsafe signing store')
    sdk = Path(os.environ.get('ANDROID_HOME') or os.environ['ANDROID_SDK_ROOT'])
    versions = [p for p in (sdk / 'build-tools').iterdir()
                if re.fullmatch(r'\d+(?:\.\d+)+', p.name)
                and (p / 'apksigner').is_file() and (p / 'zipalign').is_file()]
    tools = max(versions, key=lambda p: tuple(map(int, p.name.split('.'))))
    apks = sorted(Path('signed-apk').glob('*.apk'))
    if not apks:
        raise ValueError('No APKs to sign')
    for apk in apks:
        with tempfile.TemporaryDirectory(prefix='rustdesk-sign-', dir=apk.parent) as temporary:
            aligned, signed = Path(temporary) / 'aligned.apk', Path(temporary) / 'signed.apk'
            subprocess.run([str(tools / 'zipalign'), '-f', '-P', '16', '4', str(apk), str(aligned)], check=True)
            subprocess.run([str(tools / 'apksigner'), 'sign', '--ks', str(store),
                            '--ks-key-alias', os.environ['ANDROID_SIGNING_ALIAS'],
                            '--ks-pass', 'env:ANDROID_SIGNING_PASSWORD',
                            '--key-pass', 'env:ANDROID_SIGNING_PASSWORD',
                            '--out', str(signed), str(aligned)], check=True)
            verify(tools / 'apksigner', signed, pin)
            subprocess.run([str(tools / 'zipalign'), '-c', '-P', '16', '4', str(signed)], check=True)
            signed.replace(apk)
        print('Verified release APK: ' + str(apk) + ' certificate SHA-256: ' + pin)


if __name__ == '__main__':
    main()
