from contracting.storage.driver import Driver
from contracting.execution.runtime import rt
from contracting import constants as c
from contracting.stdlib.bridge.decimal import ContractingDecimal

driver = rt.env.get('__Driver') or Driver()


class Datum:
    def __init__(self, contract, name, driver: Driver):
        self._driver = driver
        self._key = self._driver.make_key(contract, name)


class Variable(Datum):
    def __init__(self, contract, name, driver: Driver = driver, t=None):
        self._type = None

        if isinstance(t, type) or None:
            self._type = t

        super().__init__(contract, name, driver=driver)

    def set(self, value):
        if self._type is not None:
            assert isinstance(value, self._type), (f'Wrong type passed to variable! '
                                                   f'Expected {self._type}, got {type(value)}.')

        self._driver.set(self._key, value)

    def get(self):
        return self._driver.get(self._key)


class Hash(Datum):
    def __init__(self, contract, name, driver: Driver = driver, default_value=None):
        super().__init__(contract, name, driver=driver)
        self._default_value = default_value

        # Store the default_value in storage if it's not None
        if default_value is not None:
            self._driver.set(f'{self._key}{c.DELIMITER}{c.DEFAULT}', default_value)

    def _set(self, key, value):
        self._driver.set(f'{self._key}{c.DELIMITER}{key}', value)

    def _get(self, item):
        value = self._driver.get(f'{self._key}{c.DELIMITER}{item}')

        # Add Python defaultdict behavior for easier smart contracting
        if value is None:
            # Retrieve the default_value from storage if not set
            if self._default_value is None:
                self._default_value = self._driver.get(f'{self._key}{c.DELIMITER}{c.DEFAULT}')
            value = self._default_value

        if isinstance(value, (float, ContractingDecimal)):
            return ContractingDecimal(str(value))

        return value

    def _validate_key(self, key):
        if isinstance(key, tuple):
            assert len(key) <= c.MAX_HASH_DIMENSIONS, (f'Too many dimensions ({len(key)}) for hash. '
                                                       f'Max is {c.MAX_HASH_DIMENSIONS}')

            new_key_str = ''
            for k in key:
                assert not isinstance(k, slice), 'Slices prohibited in hashes.'

                k = str(k)

                assert c.DELIMITER not in k, 'Illegal delimiter in key.'
                assert c.INDEX_SEPARATOR not in k, 'Illegal separator in key.'

                new_key_str += f'{k}{c.DELIMITER}'

            key = new_key_str[:-len(c.DELIMITER)]
        else:
            key = str(key)

            assert c.DELIMITER not in key, 'Illegal delimiter in key.'
            assert c.INDEX_SEPARATOR not in key, 'Illegal separator in key.'

        assert len(key) <= c.MAX_KEY_SIZE, f'Key is too long ({len(key)}). Max is {c.MAX_KEY_SIZE}.'
        return key

    def _prefix_for_args(self, args):
        multi = self._validate_key(args)
        prefix = f'{self._key}{c.DELIMITER}'
        if multi != '':
            prefix += f'{multi}{c.DELIMITER}'

        return prefix

    def all(self, *args):
        prefix = self._prefix_for_args(args)
        return self._driver.values(prefix=prefix)

    def _items(self, *args):
        prefix = self._prefix_for_args(args)
        return self._driver.items(prefix=prefix)

    def items(self, *args):
        kvs = self._items(*args)
        prefix = self._prefix_for_args(args)
        processed_items = {}
        for full_key, value in kvs.items():
            # Remove the prefix from the full key
            key_suffix = full_key[len(prefix):]
            if key_suffix.startswith(self._delimiter):
                key_suffix = key_suffix[len(self._delimiter):]
            # Split the key_suffix by delimiter to get the original key components
            key_components = key_suffix.split(self._delimiter)
            # If the key was a tuple, reconstruct it
            if len(key_components) == 1:
                key = key_components[0]
            else:
                key = tuple(key_components)
            processed_items[key] = value
        return processed_items.items()

    def clear(self, *args):
        kvs = self._items(*args)

        for k in kvs.keys():
            self._driver.delete(k)

    def __setitem__(self, key, value):
        # handle multiple hashes differently
        key = self._validate_key(key)
        self._set(key, value)

    def __getitem__(self, key):
        key = self._validate_key(key)
        return self._get(key)

    def __contains__(self, key):
        raise Exception('Cannot use "in" with a Hash.')


class ForeignVariable(Variable):
    def __init__(self, contract, name, foreign_contract, foreign_name, driver: Driver = driver):
        super().__init__(contract, name, driver=driver)
        self._key = self._driver.make_key(foreign_contract, foreign_name)

    def set(self, value):
        raise ReferenceError


class ForeignHash(Hash):
    def __init__(self, contract, name, foreign_contract, foreign_name, driver: Driver = driver):
        super().__init__(contract, name, driver=driver)
        self._key = self._driver.make_key(foreign_contract, foreign_name)

        # Retrieve the default_value from the foreign Hash's storage
        self._default_value = self._driver.get(f'{self._key}{c.DELIMITER}{c.DEFAULT}')

    def _set(self, key, value):
        raise ReferenceError

    def __setitem__(self, key, value):
        raise ReferenceError

    def __getitem__(self, item):
        return super().__getitem__(item)

    def items(self, *args):
        return super().items(*args)

    def clear(self, *args):
        raise Exception('Cannot write with a ForeignHash.')
