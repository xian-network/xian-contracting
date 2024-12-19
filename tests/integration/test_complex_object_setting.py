from contracting.client import ContractingClient
from unittest import TestCase
import os

def contract():
    storage = Hash()

    @export
    def create(x: int, y: int, color: str):
        storage[x, y] = {
            'color': color,
            'owner': ctx.caller
        }

    @export
    def update(x: int, y: int, color: str):
        s = storage[x, y]

        s['color'] = color

        storage[x, y] = s


class TestComplexStorage(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.flush()

        self.c.submit(contract, name="con_contract")
        self.contract = self.c.get_contract('con_contract')

    def tearDown(self):
        self.c.flush()

    def test_storage(self):
        self.contract.create(x=1, y=2, color='howdy')
        self.assertEqual(self.contract.storage[1, 2]['color'], 'howdy')

    def test_modify(self):
        self.contract.create(x=1, y=2, color='howdy')
        self.contract.update(x=1, y=2, color='yoyoyo')
