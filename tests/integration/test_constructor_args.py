from unittest import TestCase
from contracting.stdlib.bridge.time import Datetime
from contracting.client import ContractingClient


class TestSenecaClientReplacesExecutor(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.raw_driver.flush_full()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract)

        self.c.raw_driver.commit()

        # submit erc20 clone
        with open('./test_contracts/constructor_args_contract.s.py') as f:
            self.code = f.read()

    def test_custom_args_works(self):
        self.c.submit(self.code, name='con_constructor_args_contract', constructor_args={'a': 123, 'b': 321})

        contract = self.c.get_contract('con_constructor_args_contract')
        a, b = contract.get()

        self.assertEqual(a, 123)
        self.assertEqual(b, 321)

    def test_custom_args_overloading(self):
        with self.assertRaises(TypeError):
            self.c.submit(self.code, name='con_constructor_args_contract', constructor_args={'a': 123, 'x': 321})

    def test_custom_args_not_enough_args(self):
        with self.assertRaises(TypeError):
            self.c.submit(self.code, name='con_constructor_args_contract', constructor_args={'a': 123})
