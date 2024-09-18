from unittest import TestCase
from contracting.stdlib.bridge.crypto import randomx_hash
import binascii

class TestCrypto(TestCase):

    def test_randomx_hash(self):

        expected = [
            "a86260b7bf2c35910177ae47bad732b415d977d865a3d64c12e06a3f012b2ee7",
            "aa820e6869feccba3e58790437de698bafc2eeaf1a135c928d1b59b2473fb74d",
            "776a5cb55b212950c55911a99b1fc35f36e937e2b1ff6cdf6aff27e0bb36f637",
            "f2f1ae1030f53b743da7c13f9c2f85db6991f0617e360663c815158d72897ec4",
            "0ea23341e489a9720ff4bfbd0391338918a295d46416b87dfe8a785cce9eb51d",
        ]
        
        seed_hash = binascii.unhexlify('63eceef7919087068ac5d1b7faffa23fc90a58ad0ca89ecb224a2ef7ba282d48')

        for x in range(5):
            m = "Hello RandomX {}".format(x)
            print("Hashing: {}".format(m))
            if x == 0:
                print("(first takes a while, please wait)")
            # h = 1 + x
            # bh = pyrx.get_rx_hash(m, seed_hash, h)
            # hh = binascii.hexlify(bh).decode()
            # print("Result: {}".format(hh))
            # assert hh == expected[x]
            breakpoint()
            res = randomx_hash('63eceef7919087068ac5d1b7faffa23fc90a58ad0ca89ecb224a2ef7ba282d48', "hello")
            # breakpoint()