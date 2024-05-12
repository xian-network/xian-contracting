from types import ModuleType
import nacl


def verify(vk: str, msg: str, signature: str):
    vk = bytes.fromhex(vk)
    msg = msg.encode()
    signature = bytes.fromhex(signature)

    vk = nacl.signing.VerifyKey(vk)
    try:
        vk.verify(msg, signature)
    except Exception as e:
        return False
    return True


crypto_module = ModuleType('crypto')
crypto_module.verify = verify

exports = {
    'crypto': crypto_module
}
