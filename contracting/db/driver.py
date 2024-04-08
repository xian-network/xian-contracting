from contracting.db.encoder import encode, decode, encode_kv
from contracting.execution.runtime import rt
from contracting.stdlib.bridge.time import Datetime
from contracting.stdlib.bridge.decimal import ContractingDecimal
from contracting import config
from contracting.hlcpy import HLC
from datetime import datetime
import marshal
import decimal
import requests
import os
from pathlib import Path
import shutil
import logging
from contracting.db.hdf5 import hdf5 as h5c
import warnings


# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)


FILE_EXT = ".d"
HASH_EXT = ".x"

STORAGE_HOME = Path().home().joinpath(".cometbft/xian")

# DB maps bytes to bytes
# Driver maps string to python object
CODE_KEY = "__code__"
TYPE_KEY = "__type__"
AUTHOR_KEY = "__author__"
OWNER_KEY = "__owner__"
TIME_KEY = "__submitted__"
COMPILED_KEY = "__compiled__"
DEVELOPER_KEY = "__developer__"


class FSDriver:
    def __init__(self, root=None):
        self.root = Path(root) if root is not None else STORAGE_HOME
        logger.debug(f"Using root {self.root}")
        self.contract_state = self.root.joinpath("contract_state")
        self.run_state = self.root.joinpath("run_state")

        self.__build_directories()

    def __build_directories(self):
        self.contract_state.mkdir(exist_ok=True, parents=True)
        self.run_state.mkdir(exist_ok=True, parents=True)

    def __parse_key(self, key):
        try:
            filename, variable = key.split(config.INDEX_SEPARATOR, 1)
            variable = variable.replace(config.DELIMITER, config.HDF5_GROUP_SEPARATOR)
        except:
            filename = "__misc"
            variable = key.replace(config.DELIMITER, config.HDF5_GROUP_SEPARATOR)

        return filename, variable

    def __filename_to_path(self, filename):
        return (
            str(self.run_state.joinpath(filename))
            if filename.startswith("__")
            else str(self.contract_state.joinpath(filename))
        )

    def __get_files(self):
        return sorted(os.listdir(self.contract_state) + os.listdir(self.run_state))

    def __get_keys_from_file(self, filename):
        return [
            filename
            + config.INDEX_SEPARATOR
            + g.replace(config.HDF5_GROUP_SEPARATOR, config.DELIMITER)
            for g in h5c.get_groups(self.__filename_to_path(filename))
        ]

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        self.delete(key)

    def get(self, item: str):
        filename, variable = self.__parse_key(item)

        return (
            decode(h5c.get_value(self.__filename_to_path(filename), variable))
            if len(filename) < config.FILENAME_LEN_MAX
            else None
        )

    def get_block(self, item: str):
        filename, variable = self.__parse_key(item)
        block_num = (
            h5c.get_block(self.__filename_to_path(filename), variable)
            if len(filename) < config.FILENAME_LEN_MAX
            else None
        )

        return config.BLOCK_NUM_DEFAULT if block_num is None else int(block_num)

    def set(self, key, value, block_num=None):
        if block_num:
            self.safe_set(key, value, block_num)
            return

        filename, variable = self.__parse_key(key)

        if len(filename) < config.FILENAME_LEN_MAX:
            h5c.set(
                self.__filename_to_path(filename),
                variable,
                encode(value) if value is not None else None,
                None,
            )

    def safe_set(self, key: str, value: any, block_num: str):
        filename, variable = self.__parse_key(key)

        if len(filename) < config.FILENAME_LEN_MAX:
            current_block = (
                h5c.get_block(self.__filename_to_path(filename), variable) or "-1"
            )

            if int(block_num) >= int(current_block):
                h5c.set(
                    self.__filename_to_path(filename),
                    variable,
                    encode(value) if value is not None else None,
                    str(block_num),
                )

    def flush(self):
        if self.run_state.is_dir():
            shutil.rmtree(self.run_state)
        if self.contract_state.is_dir():
            shutil.rmtree(self.contract_state)

        self.__build_directories()

    def is_file(self, filename):
        file_path = Path(self.__filename_to_path(filename))
        return file_path.is_file()

    def flush_file(self, filename):
        file = Path(self.__filename_to_path(filename))
        if file.is_file():
            file.unlink()

    def delete(self, key):
        filename, variable = self.__parse_key(key)
        if len(filename) < config.FILENAME_LEN_MAX:
            h5c.delete(self.__filename_to_path(filename), variable)

    def iter(self, prefix="", length=0):
        try:
            filename, _ = self.__parse_key(prefix)
        except Exception:
            return self.keys(prefix=prefix, length=length)

        if not self.is_file(filename=filename):
            return []

        keys_from_file = self.__get_keys_from_file(filename)

        keys = [key for key in keys_from_file if key.startswith(prefix)]
        keys.sort()

        return keys if length == 0 else keys[:length]

    def keys(self, prefix=None, length=0):
        keys = set()
        try:
            for filename in self.__get_files():
                for key in self.__get_keys_from_file(filename):
                    if prefix and key.startswith(prefix):
                        keys.add(key)
                    elif not prefix:
                        keys.add(key)

                    if 0 < length <= len(keys):
                        raise AssertionError(
                            "Length threshold has been hit. Continuing."
                        )
        except AssertionError:
            pass

        keys = list(keys)
        keys.sort()
        return keys

    def get_contracts(self):
        return sorted(os.listdir(self.contract_state))

class CacheDriver:
    def __init__(self, driver=None):
        self.pending_writes = {}  # L2 cache
        self.cache = {}  # L1 cache
        self.driver = driver or FSDriver()  # L0 cache
        self.hlc = HLC()

        self.pending_reads = {}

        self.pending_deltas = {}

    def get_nanos(self, timestamp):
        # Convert timestamp to HLC clock then to nanoseconds
        temp_hlc = self.hlc.from_str(timestamp)
        timestamp_nanoseconds, _ = temp_hlc.tuple()
        return timestamp_nanoseconds

    def find(self, key: str):
        value = self.pending_writes.get(key)
        if value is not None:
            return value

        value = self.cache.get(key)
        if value is not None:
            return value

        value = self.driver.get(key)
        if value is not None:
            return value

        return None

    def get(self, key: str, save: bool = True):
        value = self.find(key)

        if save:
            if self.pending_reads.get(key) is None:
                self.pending_reads[key] = value

            if value is not None:
                rt.deduct_read(*encode_kv(key, value))

        return value

    def set(self, key, value):
        rt.deduct_write(*encode_kv(key, value))

        if self.pending_reads.get(key) is None:
            self.get(key)

        if type(value) == decimal.Decimal or type(value) == float:
            value = ContractingDecimal(str(value))

        self.pending_writes[key] = value

    def delete(self, key):
        self.set(key, None)

    def soft_apply_rewards(self, hcl: str):
        logger.debug("SOFT APPLY REWARDS")
        deltas = {}

        for k, v in self.pending_writes.items():
            current = self.pending_reads.get(k)
            deltas[k] = (current, v)

            self.cache[k] = v

        self.pending_deltas[hcl]["rewards"] = deltas

        # Clear the top cache
        self.pending_reads = {}
        self.pending_writes.clear()

    def soft_apply(self, hcl):
        hlc = hcl # This is because the original writer called it with a typo
        self.hard_apply(hlc)

    def hard_apply(self, hlc):
        deltas = {}
        for k, v in self.pending_writes.items():
            current = self.pending_reads.get(k)
            deltas[k] = (current, v)

            self.cache[k] = v

        self.pending_deltas[hlc] = {"writes": deltas, "reads": self.pending_reads}

        # Clear the top cache
        self.pending_reads = {}
        self.pending_writes.clear()

        # see if the HCL even exists
        if self.pending_deltas.get(hlc) is None:
            return

        # Run through the sorted HCLs from oldest to newest applying each one until the hcl committed is

        to_delete = []
        for _hlc, _deltas in sorted(self.pending_deltas.items()):
            # Run through all state changes, taking the second value, which is the post delta
            for key, delta in _deltas["writes"].items():
                try:
                    _block_num = self.get_nanos(_hlc)
                    self.driver.set(key=key, value=delta[1], block_num=str(_block_num))
                except (TypeError, ValueError):
                    # Safe set not supported on selected driver
                    self.driver.set(key=key, value=delta[1])

                # self.cache[key] = delta[1]

            # Add the key (
            to_delete.append(_hlc)
            if _hlc == hlc:
                break

        # Remove the deltas from the set
        [self.pending_deltas.pop(key) for key in to_delete]

    def hard_apply_one(self, hlc: str) -> dict:
        pending_delta = self.pending_deltas.pop(hlc)

        # see if the HCL even exists
        if pending_delta is None:
            return

        # Run through all state changes, taking the second value, which is the post delta
        for key, delta in pending_delta["writes"].items():
            try:
                block_num = self.get_nanos(hlc)
                self.driver.set(key=key, value=delta[1], block_num=block_num)
            except (TypeError, ValueError):
                # Safe set not supported on selected driver
                self.driver.set(key=key, value=delta[1])

        return pending_delta

    def bust_cache(self, writes: dict):
        if not writes:
            return

        for key in writes.keys():
            should_clear = True
            for pd in self.pending_deltas.values():
                should_clear = key not in list(pd["writes"].keys())
                if not should_clear:
                    break

            if should_clear:
                self.cache.pop(key, None)

    def reset_cache(self):
        self.cache = {}

    # Same as hard apply but for only the most recent changes and the cache
    def commit(self):
        self.cache.update(self.pending_writes)

        for k, v in self.cache.items():
            if v is None:
                self.driver.delete(k)
            else:
                self.driver.set(k, v)

        self.cache.clear()
        self.pending_writes.clear()
        self.pending_reads = {}

    def rollback(self, hlc=None):
        if hlc is None:
            # Returns to disk state which should be whatever it was prior to any write sessions
            self.cache.clear()
            self.pending_reads = {}
            self.pending_writes.clear()
            self.pending_deltas.clear()
        else:
            to_delete = []
            for _hlc, _deltas in sorted(self.pending_deltas.items())[::-1]:
                # Clears the current reads/writes, and the reads/writes that get made when rolling back from the
                # last HLC
                self.pending_reads = {}
                self.pending_writes.clear()

                if _hlc < hlc:
                    # if we are less than the HLC then top processing anymore, this is our rollback point
                    break
                else:
                    # if we are still greater than or equal to then mark this as delete and rollback its changes
                    to_delete.append(_hlc)
                    # Run through all state changes, taking the second value, which is the post delta
                    for key, delta in _deltas["writes"].items():
                        # self.set(key, delta[0])
                        self.cache[key] = delta[0]

            # Remove the deltas from the set
            [self.pending_deltas.pop(key) for key in to_delete]

    def clear_pending_state(self):
        self.rollback()


class ContractDriver(CacheDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delimiter = "."
        self.log = logging.getLogger("Driver")

    def items(self, prefix=""):
        # Get all of the items in the cache currently
        _items = {}
        keys = set()

        for k, v in self.pending_writes.items():
            if k.startswith(prefix) and v is not None:
                _items[k] = v
                keys.add(k)

        for k, v in self.cache.items():
            if k.startswith(prefix) and v is not None:
                _items[k] = v
                keys.add(k)

        # Get all of the keys we need
        db_keys = set(self.driver.iter(prefix=prefix))

        # Subtract the already gotten keys
        for k in db_keys - keys:
            _items[k] = self.get(k)  # Cache get will add the keys to the cache

        return _items

    def keys(self, prefix=""):
        return list(self.items(prefix).keys())

    def values(self, prefix=""):
        l = list(self.items(prefix).values())
        return list(self.items(prefix).values())

    def make_key(self, contract, variable, args=[]):
        contract_variable = self.delimiter.join((contract, variable))
        if args:
            return ":".join((contract_variable, *[str(arg) for arg in args]))
        return contract_variable

    def get_var(self, contract, variable, arguments=[], mark=True):
        key = self.make_key(contract, variable, arguments)
        return self.get(key)

    def set_var(self, contract, variable, arguments=[], value=None, mark=True):
        key = self.make_key(contract, variable, arguments)
        self.set(key, value)

    def get_contract(self, name):
        return self.get_var(name, CODE_KEY)

    def get_owner(self, name):
        owner = self.get_var(name, OWNER_KEY)
        if owner == "":
            owner = None
        return owner

    def get_time_submitted(self, name):
        return self.get_var(name, TIME_KEY)

    def get_compiled(self, name):
        return self.get_var(name, COMPILED_KEY)

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
        for key in self.keys(name):
            if self.cache.get(key) is not None:
                del self.cache[key]

            if self.pending_writes.get(key) is not None:
                del self.pending_writes[key]

            self.driver.delete(key)

    def flush(self):
        self.driver.flush()
        self.clear_pending_state()

    def get_contract_keys(self, name):
        return self.keys(name)

    def rollback_drivers(self, hlc_timestamp):
        # Roll back the current state to the point of the last block consensus
        self.log.debug(
            f"Length of Pending Deltas BEFORE {len(self.driver.pending_deltas.keys())}"
        )
        self.log.debug(f"rollback to hlc_timestamp: {hlc_timestamp}")

        if hlc_timestamp is None:
            # Returns to disk state which should be whatever it was prior to any write sessions
            self.cache.clear()
            self.reads = set()
            self.pending_writes.clear()
            self.pending_deltas.clear()
        else:
            to_delete = []
            for _hlc, _deltas in sorted(self.pending_deltas.items())[::-1]:
                # Clears the current reads/writes, and the reads/writes that get made when rolling back from the
                # last HLC
                self.reads = set()
                self.pending_writes.clear()

                if _hlc < hlc_timestamp:
                    self.log.debug(f"{_hlc} is less than {hlc_timestamp}, breaking!")
                    # if we are less than the HLC then top processing anymore, this is our rollback point
                    break
                else:
                    # if we are still greater than or equal to then mark this as delete and rollback its changes
                    to_delete.append(_hlc)
                    # Run through all state changes, taking the second value, which is the post delta
                    for key, delta in _deltas["writes"].items():
                        # self.set(key, delta[0])
                        self.cache[key] = delta[0]

            # Remove the deltas from the set
            self.log.debug(to_delete)
            [self.pending_deltas.pop(key) for key in to_delete]

        # self.driver.rollback(hlc=hlc_timestamp)

        self.log.debug(
            f"Length of Pending Deltas AFTER {len(self.driver.pending_deltas.keys())}"
        )