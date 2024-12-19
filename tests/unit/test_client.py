from unittest import TestCase
from contracting.client import ContractingClient
from contracting.storage.driver import Driver
import os
from pathlib import Path

class TestClient(TestCase):
    def setUp(self):
        self.client = None

        self.driver = Driver()
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        submission_file_path = os.path.join(self.script_dir, "contracts", "submission.s.py")
        with open(submission_file_path) as f:
            self.submission_contract_file = f.read()

    def tearDown(self):
        if self.client:
            self.client.flush()

    def test_set_submission_updates_contract_file(self):
        self.client = ContractingClient(driver=self.driver)
        self.client.flush()

        submission_1_code = self.client.raw_driver.get('submission.__code__')
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        submission_file_path = os.path.join(self.script_dir, "precompiled", "updated_submission.py")
        
        self.driver.flush_full()
        self.client.set_submission_contract(filename=submission_file_path)

        submission_2_code = self.client.raw_driver.get('submission.__code__')

        self.assertNotEqual(submission_1_code, submission_2_code)

    def test_can_create_instance_without_submission_contract(self):
        self.client = ContractingClient(submission_filename=None, driver=self.driver)

        self.assertIsNotNone(self.client)


    def test_gets_submission_contract_from_state_if_no_filename_provided(self):
        self.driver.set_contract(name='submission', code=self.submission_contract_file)
        self.driver.commit()

        self.client = ContractingClient(submission_filename=None, driver=self.driver)

        self.assertIsNotNone(self.client.submission_contract)

    def test_set_submission_contract__sets_from_submission_filename_property(self):
        self.client = ContractingClient(driver=self.driver)

        self.client.raw_driver.flush_full()
        self.client.submission_contract = None

        contract = self.client.raw_driver.get_contract('submission')
        self.assertIsNone(contract)
        self.assertIsNone(self.client.submission_contract)

        self.client.set_submission_contract()

        contract = self.client.raw_driver.get_contract('submission')
        self.assertIsNotNone(contract)
        self.assertIsNotNone(self.client.submission_contract)

    def test_set_submission_contract__sets_from_submission_from_state(self):
        self.client = ContractingClient(driver=self.driver)

        self.client.raw_driver.flush_full()
        self.client.submission_contract = None

        contract = self.client.raw_driver.get_contract('submission')
        self.assertIsNone(contract)
        self.assertIsNone(self.client.submission_contract)

        self.driver.set_contract(name='submission', code=self.submission_contract_file)
        self.driver.commit()

        self.client.set_submission_contract()

        contract = self.client.raw_driver.get_contract('submission')
        self.assertIsNotNone(contract)
        self.assertIsNotNone(self.client.submission_contract)

    def test_set_submission_contract__no_contract_provided_or_found_raises_AssertionError(self):
        self.client = ContractingClient(driver=self.driver)

        self.client.raw_driver.flush_full()
        self.client.submission_filename = None

        with self.assertRaises(AssertionError):
            self.client.set_submission_contract()

    def test_submit__raises_AssertionError_if_no_submission_contract_set(self):
        self.client = ContractingClient(submission_filename=None, driver=self.driver)

        with self.assertRaises(AssertionError):
            self.client.submit(f="")


