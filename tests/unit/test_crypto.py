from unittest import TestCase
from contracting.stdlib.bridge.crypto import randomx_hash
import random
import string
import binascii

class TestCrypto(TestCase):

    def random_string(self, length):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def random_hex_string(self, length):
        return ''.join(random.choices('0123456789abcdef', k=length))

    def test_randomx_hash(self):

        expected = [
            "7ba1fefe2ac793fcdea6436b8fb0cbc3254e2a289027896d9a9d0a747759897f",
            "d2d88402817eb5d37be0e4b80ee3670e596ce1303c22c87c2d576b63e4c3283f",
            "4d9f9aa4aa4f27eac09f700a52047b76d1168936fa01e352aeeb172c1eb56005",
            "fb8e209d45012ef72583bd846ba6c8dfa86e59f3a59c769f7ea3f55bbb9b9f9b",
            "7798a6d5cb45fe0aa79dae48a50138e52b1bf0c0a9fd7664306ccffbde660612",
        ]

        for x in range(5):
            m = "Hello RandomX {}".format(x)
            print("Hashing: {}".format(m))
            res = randomx_hash('63eceef7919087068ac5d1b7faffa23fc90a58ad0ca89ecb224a2ef7ba282d48', m + str(x))
            self.assertEqual(res, expected[x])
            self.assertEqual(str(type(res)), "<class 'str'>")

    def test_randomx_hash_invalid_hex_key(self):
        key = 'invalidhexkey'
        message = '4d657373616765'
        res = randomx_hash(key, message)
        self.assertEqual(res, 'f2649fde52dc7a395e9be604116ff46299130d4e57d745331f23c5538c125ef5')

    def test_randomx_hash_empty_key(self):
        key = ''
        message = '4d657373616765'
        res = randomx_hash(key, message)
        self.assertEqual(res, "b5b573af85a6880b3e0c391d22e0700d8cd375948386da31d0c534bd72c6e30f")

    def test_randomx_hash_fuzz_mixed_input(self):
        for _ in range(100):
            key = self.random_string(random.randint(1, 128))
            message = self.random_string(random.randint(1, 128))
            try:
                result = randomx_hash(key, message)
                self.assertIsInstance(result, str)
                self.assertEqual(len(result), 64)  # Assuming the hash length is 64 hex characters
            except Exception as e:
                self.fail(f"randomx_hash raised an exception with mixed input: {e}")
