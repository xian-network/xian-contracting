from unittest import TestCase
from contracting.stdlib.bridge.time import Datetime
from contracting.client import ContractingClient
import os

class TestDynamicImports(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.raw_driver.flush_full()

        submission_path = os.path.join(os.path.dirname(__file__), "test_contracts", "submission.s.py")

        with open(submission_path) as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract)

        self.c.raw_driver.commit()

        # submit erc20 clone
        stubucks_path = os.path.join(os.path.dirname(__file__), "test_contracts", "stubucks.s.py")

        with open(stubucks_path) as f:
            code = f.read()
            self.c.submit(code, name='con_stubucks')

        tejastokens_path = os.path.join(os.path.dirname(__file__), "test_contracts", "tejastokens.s.py")

        with open(tejastokens_path) as f:
            code = f.read()
            self.c.submit(code, name='con_tejastokens')

        bastardcoin_path = os.path.join(os.path.dirname(__file__), "test_contracts", "bastardcoin.s.py")

        with open(bastardcoin_path) as f:
            code = f.read()
            self.c.submit(code, name='con_bastardcoin')

        dynamic_importing_path = os.path.join(os.path.dirname(__file__), "test_contracts", "dynamic_importing.s.py")

        with open(dynamic_importing_path) as f:
            code = f.read()
            self.c.submit(code, name='con_dynamic_importing')

        self.stubucks = self.c.get_contract('con_stubucks')
        self.tejastokens = self.c.get_contract('con_tejastokens')
        self.bastardcoin = self.c.get_contract('con_bastardcoin')
        self.dynamic_importing = self.c.get_contract('con_dynamic_importing')

    def tearDown(self):
        self.c.raw_driver.flush_full()

    def test_successful_submission(self):
        self.assertEqual(self.stubucks.balance_of(account='stu'), 123)
        self.assertEqual(self.stubucks.balance_of(account='colin'), 321)

        self.assertEqual(self.tejastokens.balance_of(account='stu'), 321)
        self.assertEqual(self.tejastokens.balance_of(account='colin'), 123)

        self.assertEqual(self.bastardcoin.balance_of(account='stu'), 999)
        self.assertEqual(self.bastardcoin.balance_of(account='colin'), 555)

    def test_get_stubuck_balances(self):
        stu = self.dynamic_importing.balance_for_token(tok='con_stubucks', account='stu')
        colin = self.dynamic_importing.balance_for_token(tok='con_stubucks', account='colin')

        self.assertEqual(stu, 123)
        self.assertEqual(colin, 321)

    def test_get_tejastokens_balances(self):
        stu = self.dynamic_importing.balance_for_token(tok='con_tejastokens', account='stu')
        colin = self.dynamic_importing.balance_for_token(tok='con_tejastokens', account='colin')

        self.assertEqual(stu, 321)
        self.assertEqual(colin, 123)

    def test_get_bastardcoin_balances(self):
        stu = self.dynamic_importing.balance_for_token(tok='con_bastardcoin', account='stu')
        colin = self.dynamic_importing.balance_for_token(tok='con_bastardcoin', account='colin')

        self.assertEqual(stu, 999)
        self.assertEqual(colin, 555)

    def test_is_erc20(self):
        self.assertTrue(self.dynamic_importing.is_erc20_compatible(tok='con_stubucks'))
        self.assertTrue(self.dynamic_importing.is_erc20_compatible(tok='con_tejastokens'))
        self.assertFalse(self.dynamic_importing.is_erc20_compatible(tok='con_bastardcoin'))

    def test_get_balances_erc20_enforced_stubucks(self):
        stu = self.dynamic_importing.only_erc20(tok='con_stubucks', account='stu')
        colin = self.dynamic_importing.only_erc20(tok='con_stubucks', account='colin')

        self.assertEqual(stu, 123)
        self.assertEqual(colin, 321)

    def test_get_balances_erc20_enforced_tejastokens(self):
        stu = self.dynamic_importing.only_erc20(tok='con_tejastokens', account='stu')
        colin = self.dynamic_importing.only_erc20(tok='con_tejastokens', account='colin')

        self.assertEqual(stu, 321)
        self.assertEqual(colin, 123)

    def test_erc20_enforced_fails_for_bastardcoin(self):
        with self.assertRaises(AssertionError):
            stu = self.dynamic_importing.only_erc20(tok='con_bastardcoin', account='stu')

    def test_owner_of_returns_default(self):
        owner_stuff_path = os.path.join(os.path.dirname(__file__), "test_contracts", "owner_stuff.s.py")

        with open(owner_stuff_path) as f:
            code = f.read()
            self.c.submit(code, name='con_owner_stuff', owner='poo')

        owner_stuff = self.c.get_contract('con_owner_stuff')

        self.assertIsNone(owner_stuff.get_owner(s='con_stubucks', signer='poo'))
        self.assertEqual(owner_stuff.get_owner(s='con_owner_stuff', signer='poo'), 'poo')

    def test_ctx_owner_works(self):
        owner_stuff_path = os.path.join(os.path.dirname(__file__), "test_contracts", "owner_stuff.s.py")

        with open(owner_stuff_path) as f:
            code = f.read()
            self.c.submit(code, name='con_owner_stuff', owner='poot')

        owner_stuff = self.c.get_contract('con_owner_stuff')

        self.assertEqual(owner_stuff.owner_of_this(signer='poot'), 'poot')

    def test_incorrect_owner_prevents_function_call(self):
        owner_stuff_path = os.path.join(os.path.dirname(__file__), "test_contracts", "owner_stuff.s.py")

        with open(owner_stuff_path) as f:
            code = f.read()
            self.c.submit(code, name='con_owner_stuff', owner='poot')

        owner_stuff = self.c.get_contract('owner_stuff')
        with self.assertRaises(Exception):
            owner_stuff.owner_of_this()

    def test_delegate_call_with_owner_works(self):
        parent_test_path = os.path.join(os.path.dirname(__file__), "test_contracts", "parent_test.s.py")

        with open(parent_test_path) as f:
            code = f.read()
            self.c.submit(code, name='con_parent_test')

        child_test_path = os.path.join(os.path.dirname(__file__), "test_contracts", "child_test.s.py")

        with open(child_test_path) as f:
            code = f.read()
            self.c.submit(code, name='con_child_test', owner='con_parent_test')

        parent_test = self.c.get_contract('con_parent_test')

        val = parent_test.get_val_from_child(s='con_child_test')

        self.assertEqual(val, 'good')

    def test_delegate_with_wrong_owner_does_not_work(self):
        parent_test_path = os.path.join(os.path.dirname(__file__), "test_contracts", "parent_test.s.py")

        with open(parent_test_path) as f:
            code = f.read()
            self.c.submit(code, name='con_parent_test')

        child_test_path = os.path.join(os.path.dirname(__file__), "test_contracts", "child_test.s.py")

        with open(child_test_path) as f:
            code = f.read()
            self.c.submit(code, name='con_child_test', owner='blorg')

        parent_test = self.c.get_contract('parent_test')

        with self.assertRaises(Exception) as e:
            parent_test.get_val_from_child(s='child_test')
