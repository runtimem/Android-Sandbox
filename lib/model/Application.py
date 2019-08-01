from androguard.misc import APK

import hashlib
import logging

logging.getLogger("androguard").setLevel(logging.CRITICAL)
logging.getLogger("dad").setLevel(logging.CRITICAL)


class Application(APK):

    def __init__(self, path):
        APK.__init__(self, path)
        self.path = path
        self.hash_sha256 = None

    def __repr__(self):
        return f"Package: {self.package}\nMainActivity : {self.get_main_activity()}"

    def get_sha256_hash(self):
        if self.hash_sha256 is None:
            sha256_hash = hashlib.sha256()
            with open(self.path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            self.hash_sha256 = sha256_hash.hexdigest()
        return self.hash_sha256
