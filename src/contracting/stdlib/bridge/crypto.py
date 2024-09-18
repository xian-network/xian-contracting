from types import ModuleType
import randomx
import nacl


def verify(vk: str, msg: str, signature: str):
    vk = bytes.fromhex(vk)
    msg = msg.encode()
    signature = bytes.fromhex(signature)

    vk = nacl.signing.VerifyKey(vk)
    try:
        vk.verify(msg, signature)
    except:
        return False
    return True


def key_is_valid(key: str):
    """ Check if the given address is valid.
     Can be used with public and private keys """
    if not len(key) == 64:
        return False
    try:
        int(key, 16)
    except:
        return False
    return True


def randomx_hash(key: str, message: str):
    try:
        key_bytes = bytes.fromhex(key)
    except ValueError:
        key_bytes = key.encode()
    try:
        message_bytes = bytes.fromhex(message)
    except ValueError:
        message_bytes = message.encode()
    vm = randomx.RandomX(key_bytes, full_mem=False, secure=False, large_pages=False)
    return vm(message_bytes).hex()


crypto_module = ModuleType('crypto')
crypto_module.verify = verify
crypto_module.key_is_valid = key_is_valid
crypto_module.randomx_hash = randomx_hash

exports = {
    'crypto': crypto_module
}
