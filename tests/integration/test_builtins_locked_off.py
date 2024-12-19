from unittest import TestCase
from contracting.client import ContractingClient
import os

class TestBuiltinsLockedOff(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')

    def tearDown(self):
        self.c.raw_driver.flush_full()


    def test_if_builtin_can_be_submitted(self):
        builtin_path = os.path.join(os.path.dirname(__file__), "test_contracts", "builtin_lib.s.py")

        with open(builtin_path) as f:
            contract = f.read()

        with self.assertRaises(Exception):
            self.c.submit(contract, name='con_builtin')

    def test_if_non_builtin_can_be_submitted(self):
        pass


class TestMathBuiltinsLockedOff(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')

    def tearDown(self):
        self.c.raw_driver.flush_full()

    def test_if_builtin_can_be_submitted(self):
        mathtime_path = os.path.join(os.path.dirname(__file__), "test_contracts", "mathtime.s.py")

        with open(mathtime_path) as f:
            contract = f.read()

        with self.assertRaises(Exception):
            self.c.submit(contract, name='con_mathtime')


class TestDatabaseLoaderLoadsFirst(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')

    def tearDown(self):
        self.c.raw_driver.flush_full()

    def test_if_builtin_can_be_submitted(self):
        contracting_path = os.path.join(os.path.dirname(__file__), "test_contracts", "contracting.s.py")

        with open(contracting_path) as f:
            contract = f.read()
            self.c.submit(contract, name='con_contracting')

        import_test_path = os.path.join(os.path.dirname(__file__), "test_contracts", "import_test.s.py")

        with open(import_test_path) as f:
            contract = f.read()
            with self.assertRaises(ImportError):
                self.c.submit(contract, name='con_import_test')


class TestDynamicImport(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')

    def tearDown(self):
        self.c.raw_driver.flush_full()

    def test_if_builtin_can_be_submitted(self):
        dynamic_import_path = os.path.join(os.path.dirname(__file__), "test_contracts", "dynamic_import.s.py")

        with open(dynamic_import_path) as f:
            contract = f.read()
            self.c.submit(contract, name='con_dynamic_import')

        dynamic_import = self.c.get_contract('con_dynamic_import')

        with self.assertRaises(ImportError):
            dynamic_import.import_thing(name='con_math')


class TestFloatIssue(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')

    def tearDown(self):
        self.c.raw_driver.flush_full()

    def test_if_builtin_can_be_submitted(self):
        float_issue_path = os.path.join(os.path.dirname(__file__), "test_contracts", "float_issue.s.py")

        with open(float_issue_path) as f:
            contract = f.read()
            self.c.submit(contract, name='con_float_issue')

        float_issue = self.c.get_contract('con_float_issue')

        float_issue.get(x=0.1, y=0.1)
