from unittest import TestCase
from contracting.client import ContractingClient
import os

class TestRunPrivateFunction(TestCase):
    def setUp(self):
        self.client = ContractingClient()

        private_methods_path = os.path.join(os.path.dirname(__file__), "test_contracts", "private_methods.s.py")

        with open(private_methods_path) as f:
            code = f.read()

        self.client.submit(code, name='private_methods')
        self.private_methods = self.client.get_contract('private_methods')

    def tearDown(self):
        self.client.flush()

    def test_can_call_public_func(self):
        self.assertEqual(self.private_methods.call_private(), 'abc')

    def test_cannot_call_private_func(self):
        with self.assertRaises(Exception):
            self.private_methods.private()

    def test_cannot_execute_private_func(self):
        with self.assertRaises(AssertionError):
            self.private_methods.executor.execute(
                sender='sys',
                contract_name='private_methods',
                function_name='__private',
                kwargs={}
            )

    def test_can_call_private_func_if_run_private_function_called(self):
        self.assertEqual(self.private_methods.run_private_function('__private'), 'abc')

    def test_can_call_private_func_if_run_private_function_called_and_no_prefix(self):
        self.assertEqual(self.private_methods.run_private_function('private'), 'abc')

    def test_can_call_private_but_then_not(self):
        self.assertEqual(self.private_methods.run_private_function('private'), 'abc')

        with self.assertRaises(AssertionError):
            self.private_methods.executor.execute(
                sender='sys',
                contract_name='private_methods',
                function_name='__private',
                kwargs={}
            )
