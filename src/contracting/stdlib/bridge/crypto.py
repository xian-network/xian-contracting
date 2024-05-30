from xian_py.wallet import verify_msg
from types import ModuleType


crypto_module = ModuleType('crypto')
crypto_module.verify = verify_msg

exports = {
    'crypto': crypto_module
}
