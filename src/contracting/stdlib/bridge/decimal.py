DECIMAL_PLACES = 30  # Number of decimal places for minimal unit

def to_minimal_unit(amount):
    if isinstance(amount, (int, float)):
        amount = str(amount)

    if '.' in amount:
        integer_part, fractional_part = amount.split('.')
    else:
        integer_part, fractional_part = amount, ''

    integer_part = integer_part.lstrip('0') or '0'
    fractional_part = fractional_part.rstrip('0')

    if len(fractional_part) > DECIMAL_PLACES:
        raise ValueError(f"Amount has more than {DECIMAL_PLACES} decimal places.")

    fractional_part = fractional_part.ljust(DECIMAL_PLACES, '0')
    minimal_amount_str = integer_part + fractional_part
    return int(minimal_amount_str)

def from_minimal_unit(amount):
    if not isinstance(amount, int):
        raise TypeError("Amount must be an integer representing minimal units.")

    amount_str = str(amount).rjust(DECIMAL_PLACES + 1, '0')
    integer_part = amount_str[:-DECIMAL_PLACES]
    fractional_part = amount_str[-DECIMAL_PLACES:].rstrip('0')

    if fractional_part:
        return f"{integer_part}.{fractional_part}"
    else:
        return integer_part

class ContractingDecimal:
    def __init__(self, value):
        if isinstance(value, ContractingDecimal):
            self._value = value._value
        elif isinstance(value, (int, str)):
            self._value = to_minimal_unit(value)
        else:
            raise TypeError("Value must be an integer, string, or ContractingInteger.")

    def _get_other(self, other):
        if isinstance(other, ContractingDecimal):
            return other._value
        elif isinstance(other, int):
            return other
        elif isinstance(other, str):
            return to_minimal_unit(other)
        else:
            raise TypeError("Unsupported type for arithmetic operation.")

    def __add__(self, other):
        result = self._value + self._get_other(other)
        return ContractingDecimal(result)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        result = self._value - self._get_other(other)
        return ContractingDecimal(result)

    def __rsub__(self, other):
        result = self._get_other(other) - self._value
        return ContractingDecimal(result)

    def __mul__(self, other):
        result = self._value * self._get_other(other)
        # Since multiplication can increase decimal places, adjust back
        result = result // (10 ** DECIMAL_PLACES)
        return ContractingDecimal(result)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        numerator = self._value * (10 ** DECIMAL_PLACES)
        denominator = self._get_other(other)
        result = numerator // denominator
        return ContractingDecimal(result)

    def __rtruediv__(self, other):
        numerator = self._get_other(other) * (10 ** DECIMAL_PLACES)
        denominator = self._value
        result = numerator // denominator
        return ContractingDecimal(result)

    def __floordiv__(self, other):
        result = self._value // self._get_other(other)
        return ContractingDecimal(result)

    def __rfloordiv__(self, other):
        result = self._get_other(other) // self._value
        return ContractingDecimal(result)

    def __mod__(self, other):
        result = self._value % self._get_other(other)
        return ContractingDecimal(result)

    def __rmod__(self, other):
        result = self._get_other(other) % self._value
        return ContractingDecimal(result)

    def __pow__(self, other):
        result = pow(self._value, self._get_other(other))
        return ContractingDecimal(result)

    def __rpow__(self, other):
        result = pow(self._get_other(other), self._value)
        return ContractingDecimal(result)

    def __eq__(self, other):
        return self._value == self._get_other(other)

    def __ne__(self, other):
        return self._value != self._get_other(other)

    def __lt__(self, other):
        return self._value < self._get_other(other)

    def __le__(self, other):
        return self._value <= self._get_other(other)

    def __gt__(self, other):
        return self._value > self._get_other(other)

    def __ge__(self, other):
        return self._value >= self._get_other(other)

    def __neg__(self):
        return ContractingDecimal(-self._value)

    def __abs__(self):
        return ContractingDecimal(abs(self._value))

    def __int__(self):
        return self._value // (10 ** DECIMAL_PLACES)

    def __str__(self):
        return from_minimal_unit(self._value)

    def __repr__(self):
        return f"ContractingInteger({self.__str__()})"

    def __bool__(self):
        return self._value != 0

    def to_minimal_unit(self):
        return self._value

    @classmethod
    def from_minimal_unit(cls, amount):
        if not isinstance(amount, int):
            raise TypeError("Amount must be an integer representing minimal units.")
        obj = cls(0)
        obj._value = amount
        return obj

exports = {
    'decimal': ContractingDecimal
}
