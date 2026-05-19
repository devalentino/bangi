import time
from datetime import datetime, timezone
from uuid import UUID

import base62
import pytest
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305


def click_uuid(value):
    return UUID(f'00000000-0000-0000-0000-{value:012d}')


def encode_flow_timestamp_cookie(timestamp, encryption_key):
    nonce = b'testnonce123'
    padding = b'test-padding'
    plaintext = b'\x01' + bytes([len(padding)]) + padding + timestamp.to_bytes(8, byteorder='big', signed=False)
    ciphertext = ChaCha20Poly1305(bytes.fromhex(encryption_key)).encrypt(nonce, plaintext, None)
    encoded_value = base62.encodebytes(nonce + ciphertext)
    return encoded_value.decode('ascii') if isinstance(encoded_value, bytes) else encoded_value


def decode_flow_timestamp_cookie(cookie_value, encryption_key):
    payload = base62.decodebytes(cookie_value)
    plaintext = ChaCha20Poly1305(bytes.fromhex(encryption_key)).decrypt(payload[:12], payload[12:], None)
    padding_len = plaintext[1]
    return int.from_bytes(plaintext[2 + padding_len :], byteorder='big', signed=False)


@pytest.fixture
def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture
def timestamp(utcnow):
    return int(time.time())


@pytest.fixture
def today(utcnow):
    return utcnow.date()
