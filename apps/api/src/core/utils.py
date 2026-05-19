import logging
import secrets
import string
from datetime import datetime, timezone
from functools import wraps
from time import perf_counter

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

logger = logging.getLogger(__name__)
BASE62_ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase
SEALED_BYTES_VERSION = 1


def camelcase(s):
    parts = iter(s.split('_'))
    return next(parts) + ''.join(i.title() for i in parts)


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def base62_encode(payload: bytes) -> str:
    value = int.from_bytes(payload, byteorder='big')
    leading_zero_count = len(payload) - len(payload.lstrip(b'\0'))
    encoded = ''
    while value:
        value, remainder = divmod(value, 62)
        encoded = BASE62_ALPHABET[remainder] + encoded

    return BASE62_ALPHABET[0] * leading_zero_count + encoded


def base62_decode(encoded_value: str) -> bytes:
    leading_zero_count = len(encoded_value) - len(encoded_value.lstrip(BASE62_ALPHABET[0]))
    value = 0
    for char in encoded_value[leading_zero_count:]:
        value = value * 62 + BASE62_ALPHABET.index(char)

    payload = value.to_bytes((value.bit_length() + 7) // 8, byteorder='big') if value else b''
    return b'\0' * leading_zero_count + payload


def encrypt_bytes(payload: bytes, key: bytes) -> bytes:
    nonce = secrets.token_bytes(12)
    padding = secrets.token_bytes(secrets.randbelow(16))
    plaintext = bytes([SEALED_BYTES_VERSION]) + bytes([len(padding)]) + padding + payload
    ciphertext = ChaCha20Poly1305(key).encrypt(nonce, plaintext, None)
    return nonce + ciphertext


def decrypt_bytes(encrypted_payload: bytes, key: bytes) -> bytes | None:
    if not encrypted_payload:
        return None

    try:
        if len(encrypted_payload) < 12 + 16 + 2:
            return None
        nonce = encrypted_payload[:12]
        ciphertext = encrypted_payload[12:]
        plaintext = ChaCha20Poly1305(key).decrypt(nonce, ciphertext, None)
        if len(plaintext) < 2:
            return None
        version = plaintext[0]
        padding_len = plaintext[1]
        value_offset = 2 + padding_len
        if version != SEALED_BYTES_VERSION or len(plaintext) < value_offset:
            return None
        return plaintext[value_offset:]
    except (InvalidTag, ValueError, TypeError):
        return None


def log_execution_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        started_at = perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
        logger.info(
            'Function execution time',
            extra={
                'function_name': func.__qualname__,
                'duration_ms': elapsed_ms,
            },
        )
        return result

    return wrapper
