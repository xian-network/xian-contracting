import h5py

from threading import Lock
from collections import defaultdict
from contracting.storage.encoder import encode, decode
from contracting import constants

# A dictionary to maintain file-specific locks
file_locks = defaultdict(Lock)

# Constants
ATTR_LEN_MAX = 64000
ATTR_VALUE = "value"
ATTR_BLOCK = "block"


def get_file_lock(file_path):
    """Retrieve a lock for a specific file path."""
    return file_locks[file_path]


def get_value(file_path, group_name):
    return get_attr(file_path, group_name, ATTR_VALUE)


def get_block(file_path, group_name):
    return get_attr(file_path, group_name, ATTR_BLOCK)


def get_attr(file_path, group_name, attr_name):
    try:
        with h5py.File(file_path, 'r') as f:
            try:
                value = f[group_name].attrs[attr_name]
                return value.decode() if isinstance(value, bytes) else value
            except KeyError:
                return None
    except OSError:
        # File doesn't exist
        return None



def get_groups(file_path):
    try:
        with h5py.File(file_path, 'r') as f:
            return list(f.keys())
    except OSError:
        # File doesn't exist
        return []



def set(file_path, group_name, value, blocknum, timeout=20):
    """
    Set the value and blocknum attributes in the HDF5 file for the given group.
    """
    # Acquire a file lock to prevent concurrent writes
    lock = get_file_lock(file_path if isinstance(file_path, str) else file_path.filename)
    if lock.acquire(timeout=timeout):
        try:
            with h5py.File(file_path, 'a') as f:

                # Write value and blocknum to the group attributes
                write_attr(f, group_name, ATTR_VALUE, value, timeout)
                write_attr(f, group_name, ATTR_BLOCK, blocknum, timeout)
        finally:
            # Always release the lock after operation
            lock.release()
    else:
        raise TimeoutError("Lock acquisition timed out")


def write_attr(file_or_path, group_name, attr_name, value, timeout=20):
    """
    Write an attribute to a group inside an HDF5 file.
    """

    # Open the file and ensure group exists, then write the attribute
    if isinstance(file_or_path, str):
        with h5py.File(file_or_path, 'a') as f:
            _write_attr_to_file(f, group_name, attr_name, value, timeout)
    else:
        _write_attr_to_file(file_or_path, group_name, attr_name, value, timeout)


def _write_attr_to_file(file, group_name, attr_name, value, timeout):
    """
    Internal method to write the attribute to the group.
    """
    # Ensure the group exists, or create it if necessary
    grp = file.require_group(group_name)

    # Write or update the attribute in the group
    if attr_name in grp.attrs:
        del grp.attrs[attr_name]
    if value is not None:
        grp.attrs[attr_name] = value



def delete(file_path, group_name, timeout=20):
    lock = get_file_lock(file_path if isinstance(file_path, str) else file_path.filename)
    if lock.acquire(timeout=timeout):
        try:
            with h5py.File(file_path, 'a') as f:
                try:
                    del f[group_name].attrs[ATTR_VALUE]
                    del f[group_name].attrs[ATTR_BLOCK]
                except KeyError:
                    pass
        finally:
            lock.release()
    else:
        raise TimeoutError("Lock acquisition timed out")


def set_value_to_disk(file_path, group_name, value, block_num=None, timeout=20):
    """
    Save value to disk with optional block number.
    """
    encoded_value = encode(value) if value is not None else None
 
    set(file_path, group_name, encoded_value, block_num if block_num is not None else -1, timeout)


def delete_key_from_disk(file_path, group_name, timeout=20):
    delete(file_path, group_name, timeout)


def get_value_from_disk(file_path, group_name):
    return decode(get_value(file_path, group_name))


        
def get_all_keys_from_file(file_path):
    """
    Retrieve all keys (datasets and groups) from an HDF5 file and replace '/' with a specified character.
    
    :param file_path: Path to the HDF5 file.
    :param replace_char: Character to replace '/' with in the keys.
    :return: List of all keys in the HDF5 file with '/' replaced by replace_char.
    """
    keys = []

    def visit_func(name, node):
        keys.append(name.replace(constants.HDF5_GROUP_SEPARATOR, constants.DELIMITER))

    with h5py.File(file_path, 'r') as f:
        f.visititems(visit_func)

    return keys
