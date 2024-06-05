import unittest
from contracting.storage.driver import Driver
from contracting.execution.executor import Executor
from contracting.constants import STAMPS_PER_TAU
from xian.processor import TxProcessor
from contracting.client import ContractingClient
import contracting
import random
import string
import os
import sys
from loguru import logger

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

# Change the current working directory
os.chdir(script_dir)

def submission_kwargs_for_file(f):
    # Get the file name only by splitting off directories
    split = f.split('/')
    split = split[-1]

    # Now split off the .s
    split = split.split('.')
    contract_name = split[0]

    with open(f) as file:
        contract_code = file.read()

    return {
        'name': f'con_{contract_name}',
        'code': contract_code,
    }

TEST_SUBMISSION_KWARGS = {
    'sender': 'stu',
    'contract_name': 'submission',
    'function_name': 'submit_contract'
}

class MyTestCase(unittest.TestCase):

    def setUp(self):
        self.c = ContractingClient()
        self.tx_processor = TxProcessor(client=self.c)
        # Hard load the submission contract
        self.d = self.c.raw_driver
        self.d.flush_full()

        with open(contracting.__path__[0] + '/contracts/submission.s.py') as f:
            contract = f.read()

        self.d.set_contract(name='submission', code=contract)

        with open('../integration/test_contracts/currency.s.py') as f:
            contract = f.read()
        self.d.set_contract(name='currency', code=contract)

        self.c.executor.execute(**TEST_SUBMISSION_KWARGS, kwargs=submission_kwargs_for_file('../integration/test_contracts/currency.s.py'), metering=False, auto_commit=True)

        self.c.executor.execute(**TEST_SUBMISSION_KWARGS,
                       kwargs=submission_kwargs_for_file('../integration/test_contracts/exception.py'), 
                       metering=False, auto_commit=True)
        self.d.commit()

    def test_exception(self):
        prior_balance = self.d.get('con_exception.balances:stu')
        logger.debug(f"Prior balance (exception): {prior_balance}")

        
        output = self.tx_processor.process_tx({
            "payload":
            {'sender': 'stu', 'contract': 'con_exception', 'function': 'transfer', 'kwargs': {'amount': 100, 'to': 'colin'},"stamps_supplied":1000},
            "metadata":
            {"signature":"abc"},"b_meta":{"nanos":0,
            "hash":"0x0","height":0}})
        logger.debug(f"Output (exception): {output}")

        new_balance = self.d.get('con_exception.balances:stu')
        logger.debug(f"New balance (exception): {new_balance}")

        self.assertEqual(prior_balance, new_balance)

    def test_non_exception(self):
        prior_balance = self.d.get('con_currency.balances:stu')

        output = self.tx_processor.process_tx({
            "payload":
            {'sender': 'stu', 'contract': 'con_currency', 'function': 'transfer', 'kwargs': {'amount': 100, 'to': 'colin'},"stamps_supplied":1000},
            "metadata":
            {"signature":"abc"},"b_meta":{"nanos":0,"hash":"0x0","height":0}})
        
        new_balance = self.d.get('con_currency.balances:stu')
        logger.debug(f"New balance (non-exception): {new_balance}")

        self.assertEqual(prior_balance - 100, new_balance)

if __name__ == '__main__':
    unittest.main()
