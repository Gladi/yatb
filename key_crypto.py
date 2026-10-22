"""
YATB - Verschlüsselung der API-Keys (Format "enc2")

* Master-Schlüssel: 32 Zufallsbytes (base64) in einer Datei, standardmäßig das
  Docker-Secret /run/secrets/yatb_master_key (Pfad über YATB_MASTER_KEY_FILE).
  Er steht nie in der .env und nie in der Datenbank.
* Pro Server wird per HKDF-SHA256 ein eigener AES-256-Schlüssel abgeleitet
  (Kontext = Guild-ID).
* AES-256-GCM mit zufälliger Nonce; Guild-ID und Anbieter sind AAD. Ein
  Ciphertext lässt sich so weder auf einen anderen Server noch auf einen anderen
  Anbieter übertragen.
* Fingerprint (für die serverübergreifende Verbrauchszählung) = HMAC-SHA256 mit
  einem separat abgeleiteten Schlüssel, nie ein einfacher Hash des Keys.

Format: enc2:<kid>:<base64url(nonce || ciphertext || tag)>
<kid> = Kennung des Master-Schlüssels (erkennt "falscher Master-Schlüssel").
"""
import base64
import binascii
import hashlib
import hmac
import logging
import os
from typing import Dict, Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

log = logging.getLogger("yatb.crypto")

PREFIX = "enc2:"
MASTER_KEY_FILE = os.getenv("YATB_MASTER_KEY_FILE", "/run/secrets/yatb_master_key")
MASTER_KEY_BYTES = 32
_SALT = b"yatb-v2"
_NONCE_BYTES = 12


class KeyCryptoError(Exception):
    """Entschlüsselung fehlgeschlagen. Die Meldung enthält nie Key-Material."""


def _derive(master: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=_SALT, info=info).derive(master)


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


class KeyCrypto:
    def __init__(self, master: bytes):
        if len(master) != MASTER_KEY_BYTES:
            raise ValueError(f"Master-Schlüssel muss {MASTER_KEY_BYTES} Bytes lang sein.")
        self._master = master
        self._fp_key = _derive(master, b"yatb/v2/fp")
        self.kid = _derive(master, b"yatb/v2/kid").hex()[:8]
        self._guild_keys: Dict[int, AESGCM] = {}

    def __repr__(self) -> str:  # nie Schlüsselmaterial in Logs/Tracebacks
        return f"<KeyCrypto kid={self.kid}>"

    def _aead(self, guild_id: int) -> AESGCM:
        gid = int(guild_id)
        aead = self._guild_keys.get(gid)
        if aead is None:
            aead = AESGCM(_derive(self._master, b"yatb/v2/enc/guild:%d" % gid))
            self._guild_keys[gid] = aead
        return aead

    @staticmethod
    def _aad(guild_id: int, provider: str) -> bytes:
        return f"yatb:v2|g={int(guild_id)}|p={provider}".encode()

    def encrypt(self, secret: str, guild_id: int, provider: str) -> str:
        nonce = os.urandom(_NONCE_BYTES)
        ct = self._aead(guild_id).encrypt(nonce, secret.encode(), self._aad(guild_id, provider))
        return f"{PREFIX}{self.kid}:{_b64e(nonce + ct)}"

    def decrypt(self, token: str, guild_id: int, provider: str) -> str:
        if not token or not token.startswith(PREFIX):
            raise KeyCryptoError("kein enc2-Format")
        try:
            kid, payload = token[len(PREFIX):].split(":", 1)
        except ValueError:
            raise KeyCryptoError("enc2-Format beschädigt") from None
        if kid != self.kid:
            raise KeyCryptoError(f"falscher Master-Schlüssel (kid {kid}, geladen {self.kid})")
        try:
            raw = _b64d(payload)
        except (binascii.Error, ValueError):
            raise KeyCryptoError("enc2-Format beschädigt") from None
        if len(raw) <= _NONCE_BYTES + 16:
            raise KeyCryptoError("enc2-Format beschädigt")
        try:
            plain = self._aead(guild_id).decrypt(raw[:_NONCE_BYTES], raw[_NONCE_BYTES:], self._aad(guild_id, provider))
        except InvalidTag:
            raise KeyCryptoError("Authentifizierung fehlgeschlagen (falscher Server/Anbieter oder manipuliert)") from None
        return plain.decode()

    def fingerprint(self, provider: str, secret: str) -> str:
        return hmac.new(self._fp_key, f"{provider}\0{secret}".encode(), hashlib.sha256).hexdigest()


def load_master(path: str = MASTER_KEY_FILE) -> Optional[bytes]:
    """Liest den Master-Schlüssel. None, wenn die Datei fehlt oder ungültig ist (Fehler wird geloggt)."""
    try:
        with open(path, encoding="ascii") as fh:
            text = fh.read().strip()
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError) as exc:
        log.error("Master-Schlüssel %s nicht lesbar: %s", path, type(exc).__name__)
        return None
    try:
        master = base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError):
        log.error("Master-Schlüssel %s ist kein gültiges base64.", path)
        return None
    if len(master) != MASTER_KEY_BYTES:
        log.error("Master-Schlüssel %s hat %d statt %d Bytes.", path, len(master), MASTER_KEY_BYTES)
        return None
    return master


def load_crypto(path: str = MASTER_KEY_FILE) -> Optional[KeyCrypto]:
    master = load_master(path)
    if master is None:
        return None
    crypto = KeyCrypto(master)
    log.info("Master-Schlüssel geladen (kid %s).", crypto.kid)
    return crypto
