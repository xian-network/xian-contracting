from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime
import os

class TestSenecaClientReplacesExecutor(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.flush()

        dater_path = os.path.join(os.path.dirname(__file__), "test_contracts", "dater.py")

        with open(dater_path) as f:
            self.c.submit(f=f.read(), name='con_dater')

        self.dater = self.c.get_contract('con_dater')

    def tearDown(self):
        self.c.flush()

    def test_datetime_passed_argument_and_now_are_correctly_compared(self):
        self.dater.replicate(d=Datetime(year=3000, month=1, day=1))

    def test_datetime_passed_argument_and_now_are_correctly_compared_json(self):
        with self.assertRaises(TypeError):
            self.dater.replicate(d={'__time__':[3000, 12, 15, 12, 12, 12, 0]})

        with self.assertRaises(TypeError):
            self.dater.replicate(d=[2025, 11, 15, 21, 47, 14, 0])

    def test_datetime_subtracts(self):
        self.dater.subtract(d1=Datetime(year=2000, month=1, day=1), d2=Datetime(year=2001, month=1, day=1))