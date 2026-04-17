import base64
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

_SALT_SIZE = 16
_NONCE_SIZE = 12
_KEY_SIZE = 32          # AES-256
_ITERATIONS = 260_000


class CryptoManager:
    def __init__(self, passphrase: Optional[str] = None):
        self._passphrase = (passphrase or os.environ.get("APP_CRYPTO_PASSPHRASE", "default-dev-passphrase")).encode()

    def _derive_key(self, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=_KEY_SIZE,
            salt=salt,
            iterations=_ITERATIONS,
        )
        return kdf.derive(self._passphrase)

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        salt = os.urandom(_SALT_SIZE)
        nonce = os.urandom(_NONCE_SIZE)
        key = self._derive_key(salt)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        payload = salt + nonce + ciphertext
        return base64.b64encode(payload).decode()

    def decrypt(self, token: str) -> str:
        if not token:
            return ""
        try:
            payload = base64.b64decode(token.encode())
            salt = payload[:_SALT_SIZE]
            nonce = payload[_SALT_SIZE:_SALT_SIZE + _NONCE_SIZE]
            ciphertext = payload[_SALT_SIZE + _NONCE_SIZE:]
            key = self._derive_key(salt)
            aesgcm = AESGCM(key)
            return aesgcm.decrypt(nonce, ciphertext, None).decode()
        except Exception:
            return ""


_manager: Optional[CryptoManager] = None


def get_crypto() -> CryptoManager:
    global _manager
    if _manager is None:
        _manager = CryptoManager()
    return _manager


def set_passphrase(passphrase: str) -> None:
    global _manager
    _manager = CryptoManager(passphrase)
