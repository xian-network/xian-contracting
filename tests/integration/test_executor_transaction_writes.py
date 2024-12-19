import importlib
from unittest import TestCase
from contracting.stdlib.bridge.time import Datetime
from contracting.client import ContractingClient
from contracting.storage.driver import Driver
import os

class TestTransactionWrites(TestCase):
    def setUp(self):
        self.c = ContractingClient()
        self.c.flush()

        currency_path = os.path.join(os.path.dirname(__file__), "test_contracts", "currency.s.py")

        with open(currency_path) as f:
            contract = f.read()

        self.c.submit(contract, name="currency")

        self.c.executor.driver.commit()

    def tearDown(self):
        self.c.raw_driver.flush_full()

    def test_transfers(self):
        self.c.set_var(
            contract="currency", variable="balances", arguments=["bill"], value=200
        )
        res3 = self.c.executor.execute(
            contract_name="currency",
            function_name="transfer",
            kwargs={"to": "someone", "amount": 100},
            stamps=1000,
            sender="bill",
        )
        self.assertEquals(res3["writes"], self.c.executor.driver.pending_writes)
        res2 = self.c.executor.execute(
            contract_name="currency",
            function_name="transfer",
            kwargs={"to": "someone", "amount": 100},
            stamps=1000,
            sender="bill",
        )
        
        self.assertEquals(res2["writes"], self.c.executor.driver.pending_writes)
        # This operation will raise an exception, so will not make any writes.
        res3 = self.c.executor.execute(
            contract_name="currency",
            function_name="transfer",
            kwargs={"to": "someone", "amount": 100},
            stamps=1000,
            sender="bill",
        )
        self.assertEquals(res3["writes"], {})


if __name__ == "__main__":
    import unittest

    unittest.main()
