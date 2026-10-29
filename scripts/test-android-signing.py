import base64
import hashlib
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).parents[1] / 'scripts/actions/sign-android.py'
if not SCRIPT.exists():
    SCRIPT = Path(__file__).with_name('sign-android.py')
MODULE = runpy.run_path(str(SCRIPT))


class CertificateVerificationTest(unittest.TestCase):
    def test_only_exact_certificate_is_accepted_after_successful_verification(self):
        cert = b'expected certificate'
        pin = hashlib.sha256(cert).hexdigest()
        def pem(data):
            return '-----BEGIN CERTIFICATE-----\n' + base64.b64encode(data).decode() + '\n-----END CERTIFICATE-----'
        for output, accepted in [(pem(cert), True), ('', False), (pem(b'other'), False),
                                 (pem(cert) + pem(b'other'), False), ('public key digest: ' + pin, False)]:
            with self.subTest(output=output), patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, output, '')):
                if accepted:
                    MODULE['verify']('apksigner', 'app.apk', pin)
                else:
                    with self.assertRaises(ValueError):
                        MODULE['verify']('apksigner', 'app.apk', pin)
        with patch.object(subprocess, 'run', side_effect=subprocess.CalledProcessError(1, ['apksigner'])):
            with self.assertRaises(subprocess.CalledProcessError):
                MODULE['verify']('apksigner', 'app.apk', pin)


if __name__ == '__main__':
    unittest.main()
