import unittest
from xian.processor import TxProcessor
from contracting.client import ContractingClient
from xian.services.simulator import Simulator
from xian.constants import Constants
import os
import pathlib
class MyTestCase(unittest.TestCase):

    def setUp(self):
        constants = Constants()
        self.c = ContractingClient(storage_home=constants.STORAGE_HOME)
        self.tx_processor = TxProcessor(client=self.c)
        self.stamp_calculator = Simulator()
        self.d = self.c.raw_driver
        self.d.flush_full()

        script_dir = os.path.dirname(os.path.abspath(__file__))

        submission_contract_path = os.path.join(script_dir, "contracts", "submission.s.py")

        with open(submission_contract_path) as f:
            contract = f.read()
        self.d.set_contract(name="submission", code=contract)

    def deploy_broken_stuff(self):
         # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))

        proxythis_path = os.path.join(script_dir, "contracts", "proxythis.py")
        with open(proxythis_path) as f:
            contract = f.read()

            self.c.submit(
                contract,
                name="con_proxythis",
            )

            self.proxythis = self.c.get_contract("con_proxythis")

        thistest2_path = os.path.join(script_dir, "contracts", "thistest2.py")

        with open(thistest2_path) as f:
            contract = f.read()

            self.c.submit(
                contract,
                name="con_thistest2",
            )

            self.thistest2 = self.c.get_contract("con_thistest2")

    def test_submit(self):
        self.deploy_broken_stuff()
        self.assertEqual(self.proxythis.proxythis(con="con_thistest2", signer="address"), ("con_thistest2", "con_proxythis"))
        self.assertEqual(self.proxythis.noproxy(signer="address"), ("con_proxythis", "address"))
        self.assertEqual(self.proxythis.nestedproxythis(con="con_thistest2", signer="address"), ("con_thistest2", "con_proxythis"))

if __name__ == '__main__':
    unittest.main()