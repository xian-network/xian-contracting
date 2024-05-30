from xian_py.wallet import verify_msg, key_is_valid
from types import ModuleType


crypto_module = ModuleType('crypto')
crypto_module.verify = verify_msg
crypto_module.key_is_valid = key_is_valid


exports = {
    'crypto': crypto_module
}
