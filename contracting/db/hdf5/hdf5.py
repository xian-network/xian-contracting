import os
import h5py
from contextlib import contextmanager
import errno

ATTR_LEN_MAX = 64000
ATTR_VALUE = "value"
ATTR_BLOCK = "block"
LOCK_SUFFIX = "-lock"
LOCK_TIMEOUT = 10

@contextmanager
def file_lock(lock_path):
    try:
        os.makedirs(lock_path)
        yield
    finally:
        try:
            os.rmdir(lock_path)
        except OSError as e:
            if e.errno != errno.ENOENT:  # No such file or directory
                raise
            
def write_attr(file_or_path, group_name, attr_name, value):
    # If a file path is provided instead of an open file object, open the file here.
    if isinstance(file_or_path, str):
        with h5py.File(file_or_path, 'a') as f:
            _write_attr_to_file(f, group_name, attr_name, value)
    else:
        _write_attr_to_file(file_or_path, group_name, attr_name, value)

def _write_attr_to_file(file, group_name, attr_name, value):
    # The existing logic to write an attribute.
    with file_lock(file.filename + LOCK_SUFFIX):
        grp = file.require_group(group_name)
        if attr_name in grp.attrs:
            del grp.attrs[attr_name]
        if value:
            grp.attrs[attr_name] = value

def get_attr(file_path, group_name, attr_name):
    with file_lock(file_path + LOCK_SUFFIX):
        with h5py.File(file_path, 'a') as f:
            try:
                value = f[group_name].attrs[attr_name]
                return value.decode() if isinstance(value, bytes) else value
            except KeyError:
                return None

def set(file_path, group_name, value, blocknum):
    with h5py.File(file_path, 'a') as f:
        write_attr(f, group_name, ATTR_VALUE, value)
        write_attr(f, group_name, ATTR_BLOCK, blocknum)

def get_value(file_path, group_name):
    return get_attr(file_path, group_name, ATTR_VALUE)

def get_block(file_path, group_name):
    return get_attr(file_path, group_name, ATTR_BLOCK)

def delete(file_path, group_name):
    with file_lock(file_path + LOCK_SUFFIX):
        with h5py.File(file_path, 'a') as f:
            try:
                del f[group_name].attrs[ATTR_VALUE]
                del f[group_name].attrs[ATTR_BLOCK]
            except KeyError:
                pass  # Ignore if the attribute doesn't exist

def get_groups(file_path):
    with file_lock(file_path + LOCK_SUFFIX):
        with h5py.File(file_path, 'r') as f:
            return list(f.keys())
