from contracting.storage.driver import Driver
from contracting.execution.runtime import rt
from contracting import constants
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
        self._delimiter = constants.DELIMITER
        self._default_value = default_value

    def _set(self, key, value):
        self._driver.set(f'{self._key}{self._delimiter}{key}', value)

    def _get(self, item):
        value = self._driver.get(f'{self._key}{self._delimiter}{item}')

        # Add Python defaultdict behavior for easier smart contracting
        if value is None:
            value = self._default_value

        if type(value) == float or type(value) == ContractingDecimal:
            return ContractingDecimal(str(value))

        return value

    def _validate_key(self, key):
        if isinstance(key, tuple):
            assert len(key) <= constants.MAX_HASH_DIMENSIONS, (f'Too many dimensions ({len(key)}) for hash. '
                                                               f'Max is {constants.MAX_HASH_DIMENSIONS}')

            new_key_str = ''
            for k in key:
                assert not isinstance(k, slice), 'Slices prohibited in hashes.'

                k = str(k)

                assert constants.DELIMITER not in k, 'Illegal delimiter in key.'
                assert constants.INDEX_SEPARATOR not in k, 'Illegal separator in key.'

                new_key_str += f'{k}{self._delimiter}'

            key = new_key_str[:-len(self._delimiter)]
        else:
            key = str(key)

            assert constants.DELIMITER not in key, 'Illegal delimiter in key.'
            assert constants.INDEX_SEPARATOR not in key, 'Illegal separator in key.'

        assert len(key) <= constants.MAX_KEY_SIZE, f'Key is too long ({len(key)}). Max is {constants.MAX_KEY_SIZE}.'
        return key

    def _prefix_for_args(self, args):
        multi = self._validate_key(args)
        prefix = f'{self._key}{self._delimiter}'
        if multi != '':
            prefix += f'{multi}{self._delimiter}'

        return prefix

    def all(self, *args):
        prefix = self._prefix_for_args(args)
        return self._driver.values(prefix=prefix)

    def _items(self, *args):
        prefix = self._prefix_for_args(args)
        return self._driver.items(prefix=prefix)

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

    def _set(self, key, value):
        raise ReferenceError

    def __setitem__(self, key, value):
        raise ReferenceError

    def __getitem__(self, item):
        return super().__getitem__(item)

    def clear(self, *args):
        raise Exception('Cannot write with a ForeignHash.')
