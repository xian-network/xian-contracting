import unittest
import os
from shutil import rmtree
from datetime import datetime
from contracting.storage.driver import Driver

class TestDriver(unittest.TestCase):

    def setUp(self):
        # Setup a fresh instance of Driver and ensure a clean storage environment
        self.driver = Driver(bypass_cache=False)
        self.driver.flush_full()

    def tearDown(self):
        # Clean up any state that might affect other tests
        self.driver.flush_full()

    def test_set_and_get(self):
        key = 'test_key'
        value = 'test_value'
        self.driver.set(key, value)
        self.driver.commit()
        retrieved_value = self.driver.get(key)
        self.assertEqual(retrieved_value, value)

    def test_find(self):
        key = 'test_key'
        value = 'test_value'
        self.driver.set(key, value)
        self.driver.commit()
        retrieved_value = self.driver.find(key)
        self.assertEqual(retrieved_value, value)

    def test_keys_from_disk(self):
        key1 = 'test_key1'
        key2 = 'test_key2'
        value = 'test_value'
        self.driver.set(key1, value)
        self.driver.set(key2, value)
        self.driver.commit()
        keys = self.driver.keys_from_disk()
        self.assertIn(key1, keys)
        self.assertIn(key2, keys)

    def test_iter_from_disk(self):
        key1 = 'test_key1'
        key2 = 'test_key2'
        prefix_key = 'prefix_key'
        value = 'test_value'
        self.driver.set(key1, value)
        self.driver.set(key2, value)
        self.driver.set(prefix_key, value)
        self.driver.commit()
        keys = self.driver.iter_from_disk(prefix=prefix_key)
        self.assertIn(prefix_key, keys)
        self.assertNotIn(key1, keys)
        self.assertNotIn(key2, keys)

    def test_items(self):
        prefix_key = 'prefix_key'
        value = 'test_value'
        self.driver.set(prefix_key, value)
        self.driver.commit()
        items = self.driver.items(prefix=prefix_key)
        self.assertIn(prefix_key, items)
        self.assertEqual(items[prefix_key], value)

    def test_delete_key_from_disk(self):
        key = 'test_key'
        value = 'test_value'
        self.driver.set(key, value)
        self.driver.commit()
        self.driver.delete_key_from_disk(key)
        retrieved_value = self.driver.value_from_disk(key)
        self.assertIsNone(retrieved_value)

    def test_flush_cache(self):
        key = 'test_key'
        value = 'test_value'
        self.driver.set(key, value)
        self.driver.flush_cache()
        self.assertFalse(self.driver.pending_writes)

    def test_flush_disk(self):
        key = 'test_key'
        value = 'test_value'
        self.driver.set(key, value)
        self.driver.commit()
        self.driver.flush_disk()
        self.assertFalse(self.driver.get(key))

    def test_commit(self):
        key = 'test_key'
        value = 'test_value'
        self.driver.set(key, value)
        self.driver.commit()
        retrieved_value = self.driver.get(key)
        self.assertEqual(retrieved_value, value)

    def test_get_all_contract_state(self):
        key = 'contract.key'
        value = 'contract_value'
        self.driver.set(key, value)
        self.driver.commit()
        contract_state = self.driver.get_all_contract_state()
        self.assertIn(key, contract_state)
        self.assertEqual(contract_state[key], value)
        
    def test_transaction_writes(self):
        key = 'test_key'
        value = 'test_value'
        self.driver.set(key, value, is_txn_write=True)
        # self.driver.commit()
        transaction_writes = self.driver.transaction_writes
        self.assertIn(key, transaction_writes)
        self.assertEqual(transaction_writes[key], value)
        
    def test_clear_transaction_writes(self):
        key = 'test_key'
        value = 'test_value'
        self.driver.set(key, value)
        # self.driver.commit()
        self.driver.clear_transaction_writes()
        transaction_writes = self.driver.transaction_writes
        self.assertNotIn(key, transaction_writes)

    def test_get_run_state(self):
        # We can't test this function here since we are not running a real blockchain.
        pass

if __name__ == '__main__':
    unittest.main()
