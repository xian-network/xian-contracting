from contracting.storage.encoder import encode_kv
from contracting.execution.runtime import rt
from contracting.stdlib.bridge.time import Datetime
from contracting.stdlib.bridge.decimal import ContractingDecimal
from datetime import datetime
from pathlib import Path
from cachetools import TTLCache
from contracting import constants
from contracting.storage import hdf5

import marshal
import decimal
import os
import shutil

FILE_EXT = ".d"
HASH_EXT = ".x"

DELIMITER = "."
HASH_DEPTH_DELIMITER = ":"

CODE_KEY = "__code__"
TYPE_KEY = "__type__"
AUTHOR_KEY = "__author__"
OWNER_KEY = "__owner__"
TIME_KEY = "__submitted__"
COMPILED_KEY = "__compiled__"
DEVELOPER_KEY = "__developer__"


class Driver:
    def __init__(self, bypass_cache=False, storage_home=constants.STORAGE_HOME):
        self.pending_deltas = {}
        self.pending_writes = {}
        self.pending_reads = {}
        self.transaction_writes = {}
        self.log_events = []
        self.cache = TTLCache(maxsize=1000, ttl=6*3600)
        self.bypass_cache = bypass_cache
        self.contract_state = storage_home.joinpath("contract_state")
        self.run_state = storage_home.joinpath("run_state")
        self.__build_directories()

    def __build_directories(self):
        self.contract_state.mkdir(exist_ok=True, parents=True)
        self.run_state.mkdir(exist_ok=True, parents=True)

    def __parse_key(self, key):
        # Split the key into parts (filename, group, etc.)
        parts = key.split(constants.INDEX_SEPARATOR, 1)  # Ensure key contains the INDEX_SEPARATOR
        
        # The first part should be the filename (e.g., "currency")
        filename = parts[0].split(constants.DELIMITER, 1)[0]  # Get only 'currency' from 'currency.balances'
        
        # The rest (after the first '.') becomes the group and attribute inside the HDF5 file
        if len(parts) > 1:
            variable = parts[1].replace(constants.DELIMITER, constants.HDF5_GROUP_SEPARATOR)
        else:
            variable = parts[0].replace(constants.DELIMITER, constants.HDF5_GROUP_SEPARATOR)
        
        return filename, variable


    def __filename_to_path(self, filename):
        if filename.startswith("__"):
            return str(self.run_state.joinpath(filename))
        else:
            return str(self.contract_state.joinpath(filename))

    def __get_files(self):
        return sorted(os.listdir(self.contract_state) + os.listdir(self.run_state))
    
    def is_file(self, filename):
        file_path = Path(self.__filename_to_path(filename))
        return file_path.is_file()

    def get(self, key: str, save: bool = True):
        """
        Get a value from the cache, pending reads, or disk. If save is True, 
        the value will be saved to pending_reads.
        """ 
        # Parse the key to get the filename and group
        value = self.find(key)
        if save and self.pending_reads.get(key) is None:
            self.pending_reads[key] = value
        if value is not None:
            rt.deduct_read(*encode_kv(key, value))
        return value


    def set(self, key, value, is_txn_write=False):
        rt.deduct_write(*encode_kv(key, value))
        if self.pending_reads.get(key) is None:
            self.get(key)
        if type(value) in [decimal.Decimal, float]:
            value = ContractingDecimal(str(value))
        self.pending_writes[key] = value
        if is_txn_write:
            self.transaction_writes[key] = value


    def find(self, key: str):
        """
        Find the value for a given key. If not found in cache or pending writes, 
        it will look it up from the disk.
        """
        if self.bypass_cache:
            # Parse the key to get the filename and group
            filename, variable = self.__parse_key(key)
            value = hdf5.get_value_from_disk(self.__filename_to_path(filename), variable)
            return value

        value = self.pending_writes.get(key)
        if value is None:
            value = self.cache.get(key)
        if value is None:
            # Parse the key to get the filename and group for disk lookup
            filename, variable = self.__parse_key(key)
            value = hdf5.get_value_from_disk(self.__filename_to_path(filename), variable)
        return value


    def __get_keys_from_file(self, filename):
        return hdf5.get_groups(self.__filename_to_path(filename))

    def keys_from_disk(self, prefix=None, length=0):
        """
        Get all keys from disk with a given prefix
        """
        keys = set()
        try:
            for filename in self.__get_files():
                for key in self.__get_keys_from_file(filename):
                    if prefix and key.startswith(prefix):
                        keys.add(key)
                    elif not prefix:
                        keys.add(key)

                    if 0 < length <= len(keys):
                        raise AssertionError("Length threshold has been hit. Continuing.")
        except AssertionError:
            pass

        keys = list(keys)
        keys.sort()
        return keys

    def iter_from_disk(self, prefix="", length=0):
        try:
            filename, _ = self.__parse_key(prefix)
        except Exception:
            return self.keys(prefix=prefix)

        if not self.is_file(filename=filename):
            return []

        keys_from_file = self.__get_keys_from_file(filename)

        keys = [key for key in keys_from_file if key.startswith(prefix)]
        keys.sort()

        return keys if length == 0 else keys[:length]

    def value_from_disk(self, key):
        """
        Retrieve a value from the disk based on the parsed key.
        """
        # Parse the key to get the filename and group
        filename, variable = self.__parse_key(key)
        return hdf5.get_value_from_disk(self.__filename_to_path(filename), variable)

    def items(self, prefix=""):
        """
        Get all existing items with a given prefix.
        """
        _items = {}
        keys = set()

        # Collect pending writes with matching prefix
        for k, v in self.pending_writes.items():
            if k.startswith(prefix) and v is not None:
                _items[k] = v
                keys.add(k)

        # Collect cache items with matching prefix
        for k, v in self.cache.items():
            if k.startswith(prefix) and v is not None:
                _items[k] = v
                keys.add(k)

        # Collect keys from the disk
        db_keys = set(self.iter_from_disk(prefix=prefix))

        # Subtract already collected keys and add missing ones from disk
        for k in db_keys - keys:
            _items[k] = self.get(k)  # Cache get will add the keys to the cache

        return _items


    def keys(self, prefix=""):
        return list(self.items(prefix).keys())

    def values(self, prefix=""):
        l = list(self.items(prefix).values())
        return list(self.items(prefix).values())

    def make_key(self, contract, variable, args=[]):
        contract_variable = DELIMITER.join((contract, variable))
        if args:
            return HASH_DEPTH_DELIMITER.join((contract_variable, *[str(arg) for arg in args]))
        return contract_variable

    def set_var(self, contract, variable, arguments=[], value=None, mark=True):
        """
        Set a variable in a contract.
        """
        # Construct the key and set the value
        key = self.make_key(contract, variable, arguments)
        self.set(key, value)

    def get_var(self, contract, variable, arguments=[], mark=True):
        """
        Get a variable from a contract.
        """
        # Construct the key and get the value
        key = self.make_key(contract, variable, arguments)
        return self.get(key)

    def get_owner(self, name):
        owner = self.get_var(name, OWNER_KEY)
        if owner == "":
            owner = None
        return owner

    def get_time_submitted(self, name):
        return self.get_var(name, TIME_KEY)

    def get_compiled(self, name):
        return self.get_var(name, COMPILED_KEY)

    def get_contract(self, name):
        return self.get_var(name, CODE_KEY)

    def set_contract(
        self,
        name,
        code,
        owner=None,
        overwrite=False,
        timestamp=Datetime._from_datetime(datetime.now()),
        developer=None,
    ):
        if self.get_contract(name) is None:
            code_obj = compile(code, "", "exec")
            code_blob = marshal.dumps(code_obj)

            self.set_var(name, CODE_KEY, value=code)
            self.set_var(name, COMPILED_KEY, value=code_blob)
            self.set_var(name, OWNER_KEY, value=owner)
            self.set_var(name, TIME_KEY, value=timestamp)
            self.set_var(name, DEVELOPER_KEY, value=developer)

    def delete_contract(self, name):
        """
        Fully delete a contract from the caches and disk
        """
        for key in self.keys(name):
            if self.cache.get(key) is not None:
                del self.cache[key]

            if self.pending_writes.get(key) is not None:
                del self.pending_writes[key]

            self.delete_key_from_disk(key)

    def get_contract_files(self):
        """
        Get all contract files as a list of strings
        """
        return sorted(os.listdir(self.contract_state))

    def delete_key_from_disk(self, key):
        """
        Delete a key from the disk by parsing the filename and group from the key.
        """
        # Parse the key to get the filename and group
        filename, variable = self.__parse_key(key)
        if len(filename) < constants.FILENAME_LEN_MAX:
            hdf5.delete_key_from_disk(self.__filename_to_path(filename), variable)

    def flush_cache(self):
        self.pending_writes.clear()
        self.pending_reads.clear()
        self.pending_deltas.clear()
        self.transaction_writes.clear()
        self.log_events.clear()
        self.cache.clear()

    def flush_disk(self):
        shutil.rmtree(self.run_state, ignore_errors=True)
        shutil.rmtree(self.contract_state, ignore_errors=True)
        self.__build_directories()

    def flush_file(self, filename):
        file_path = self.__filename_to_path(filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)
            
    def set_event(self, event):
        self.log_events.append(event)

    def flush_full(self):
        """
        Flush all caches and disk storage.
        """
        self.flush_disk()
        self.flush_cache()

    def delete(self, key):
        """
        Delete a key fully from the caches and queue it for deletion from disk on commit.
        """
        self.set(key, None)  # Setting the value to None will mark it for deletion

    def rollback(self, nanos=None):
        """
        Rollback to a given Nanoseconds in L2 cache or if no Nanoseconds is given, rollback to the latest state on disk.
        """
        if nanos is None:
            # Resets to the latest state on disk
            self.cache.clear()
            self.pending_reads.clear()
            self.pending_writes.clear()
            self.pending_deltas.clear()
        else:
            to_delete = []
            for _nanos, _deltas in sorted(self.pending_deltas.items(), reverse=True):
                if _nanos < nanos:
                    break
                to_delete.append(_nanos)
                for key, delta in _deltas['writes'].items():
                    self.cache[key] = delta[0]  # Restoring the value before the write

            for _nanos in to_delete:
                self.pending_deltas.pop(_nanos, None)

    def commit(self):
        """
        Save the current state to disk and clear the L1 and L2 caches.
        """
        for k, v in self.pending_writes.items():
            # Parse the key before applying to HDF5
            filename, variable = self.__parse_key(k)
            if v is None:
                hdf5.delete_key_from_disk(self.__filename_to_path(filename), variable)
            else:
                hdf5.set_value_to_disk(self.__filename_to_path(filename), variable, v, None)

        self.cache.clear()
        self.pending_writes.clear()
        self.pending_reads.clear()


    def hard_apply(self, nanos):
        """
        Save the current state to disk and L1 cache and clear the L2 cache.
        """

        deltas = {}
        for k, v in self.pending_writes.items():
            current = self.pending_reads.get(k)
            deltas[k] = (current, v)

            self.cache[k] = v

        self.pending_deltas[nanos] = {"writes": deltas, "reads": self.pending_reads}

        # Clear the top cache
        self.pending_reads = {}
        self.pending_writes.clear()

        # Run through the sorted HCLs from oldest to newest applying each one
        to_delete = []
        for _nanos, _deltas in sorted(self.pending_deltas.items()):
            # Run through all state changes, taking the second value, which is the post delta
            for key, delta in _deltas["writes"].items():
                # Parse the key before applying to HDF5
                filename, variable = self.__parse_key(key)
                hdf5.set_value_to_disk(self.__filename_to_path(filename), variable, delta[1], nanos)

            to_delete.append(_nanos)
            if _nanos == nanos:
                break

        # Remove the deltas from the set
        [self.pending_deltas.pop(key) for key in to_delete]


    def get_all_contract_state(self):
        """
        Queries the disk storage and returns a dictionary with all the state from the contract storage directory.
        """
        all_contract_state = {}
        for file_path in self.contract_state.iterdir():
            filename = file_path.name
            keys = hdf5.get_all_keys_from_file(self.__filename_to_path(filename))
            for key in keys:
                full_key = f"{filename}{DELIMITER}{key}"
                value = self.get(full_key)
                all_contract_state[full_key] = value

        return all_contract_state
    

    def get_run_state(self):
        """
        Retrieves the latest state information from the run state directory.
        """
        run_state = {}
        for file_path in self.run_state.iterdir():
            filename = file_path.name
            keys = self.__get_keys_from_file(self.__filename_to_path(filename))
            for key in keys:
                full_key = f"{filename}{DELIMITER}{key}"
                value = hdf5.get_value_from_disk(self.__filename_to_path(filename), key)
                run_state[full_key] = value

        return run_state


    def clear_transaction_writes(self):
        """
        Clear the transaction-specific writes.
        """
        self.transaction_writes.clear()

    def clear_events(self):
        self.log_events.clear()
