from types import ModuleType
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


crypto_module = ModuleType('crypto')
crypto_module.verify = verify
crypto_module.key_is_valid = key_is_valid

exports = {
    'crypto': crypto_module
}
