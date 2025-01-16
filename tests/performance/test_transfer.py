from unittest import TestCase
import secrets
from contracting.storage.driver import Driver
from contracting.execution.executor import Executor
import os

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


class TestSandbox(TestCase):
    def setUp(self):
        self.d = Driver()
        self.d.flush_full()

        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        submission_path = os.path.join(self.script_dir, "test_contracts", "submission.s.py")
        with open(submission_path) as f:
            contract = f.read()

        self.d.set_contract(name='submission',
                            code=contract)
        self.d.commit()

        self.recipients = [secrets.token_hex(16) for _ in range(10000)]

    def tearDown(self):
        self.d.flush_full()

    def test_transfer_performance(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(os.path.join(self.script_dir, "test_contracts", "erc20_clone.s.py")))

        for r in self.recipients:
            e.execute(sender='stu',
                      contract_name='con_erc20_clone',
                      function_name='transfer',
                      kwargs={
                          'amount': 1,
                          'to': r
                      })