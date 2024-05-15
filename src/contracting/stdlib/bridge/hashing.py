import hashlib

from types import ModuleType

'''
Bytes can't be stored in JSON so we use hex-strings converted into bytes and back.
'''


def sha3(hex_str: str):
    try:
        byte_str = bytes.fromhex(hex_str)
    except ValueError:
        byte_str = hex_str.encode()

    hasher = hashlib.sha3_256()
    hasher.update(byte_str)

    hashed_bytes = hasher.digest()

    return hashed_bytes.hex()


def sha256(hex_str: str):
    try:
        byte_str = bytes.fromhex(hex_str)
    except ValueError:
        byte_str = hex_str.encode()

    hasher = hashlib.sha256()
    hasher.update(byte_str)

    hashed_bytes = hasher.digest()

    return hashed_bytes.hex()


hashlib_module = ModuleType('hashlib')
hashlib_module.sha3 = sha3
hashlib_module.sha256 = sha256

exports = {
    'hashlib': hashlib_module,
}
