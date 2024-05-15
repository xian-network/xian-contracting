from decimal import Decimal

import decimal

MAX_UPPER_PRECISION = 30
MAX_LOWER_PRECISION = 30
CONTEXT = decimal.Context(
    prec=MAX_UPPER_PRECISION + MAX_LOWER_PRECISION,
    rounding=decimal.ROUND_FLOOR,
    Emin=-100,
    Emax=100
)
decimal.setcontext(CONTEXT)


def make_min_decimal_str(prec):
    s = '0.'
    for i in range(prec - 1):
        s += '0'
    s += '1'
    return s


def make_max_decimal_str(prec):
    s = '1'
    for i in range(prec - 1):
        s += '0'
    return s


def neg_sci_not(s: str):
    try:
        base, exp = s.split('e-')

        if float(base) > 9:
            return s

        base = base.replace('.', '')

        numbers = ('0' * (int(exp) - 1)) + base

        if int(exp) > 0:
            numbers = '0.' + numbers

        return numbers
    except ValueError:
        return s


MAX_DECIMAL = Decimal(make_max_decimal_str(MAX_UPPER_PRECISION))
MIN_DECIMAL = Decimal(make_min_decimal_str(MAX_LOWER_PRECISION))


def should_round(x: Decimal):
    s = str(x)

    try:
        upper, lower = s.split('.')
    except ValueError:
        return False

    if len(lower) > MAX_LOWER_PRECISION - 1:
        return True


def fix_precision(x: Decimal):
    if x > MAX_DECIMAL:
        return MAX_DECIMAL

    if should_round(x):
        return x.quantize(MIN_DECIMAL, rounding=decimal.ROUND_FLOOR).normalize()

    return ContractingDecimal(x)


class ContractingDecimal:
    def _get_other(self, other):
        if type(other) == ContractingDecimal:
            return other._d
        elif type(other) == float or type(other) == int:
            o = str(other)
            return Decimal(neg_sci_not(o))
        return other

    def __init__(self, a):
        if type(a) == float or type(a) == int:
            o = str(a)
            self._d = Decimal(neg_sci_not(o))
        elif type(a) == Decimal:
            self._d = a
        elif type(a) == str:
            self._d = Decimal(neg_sci_not(a))
        else:
            self._d = Decimal(a)

    def __bool__(self):
        return self._d > 0

    def __eq__(self, other):
        return self._d.__eq__(self._get_other(other))

    def __lt__(self, other):
        return self._d.__lt__(self._get_other(other))

    def __le__(self, other):
        return self._d.__le__(self._get_other(other))

    def __gt__(self, other):
        return self._d.__gt__(self._get_other(other))

    def __ge__(self, other):
        return self._d.__ge__(self._get_other(other))

    def __str__(self):
        return self._d.__str__()

    def __repr__(self):
        return self._d.__str__()

    def __neg__(self):
        return self._d.__neg__()

    def __pos__(self):
        return self._d.__pos__()

    def __abs__(self):
        return self._d.__abs__()

    def __add__(self, other):
        x = self._d.__add__(self._get_other(other))
        return fix_precision(x)

    def __radd__(self, other):
        return fix_precision(self._d.__radd__(self._get_other(other)))

    def __sub__(self, other):
        return fix_precision(self._d.__sub__(self._get_other(other)))

    def __rsub__(self, other):
        return fix_precision(self._d.__rsub__(self._get_other(other)))

    def __mul__(self, other):
        return fix_precision(self._d.__mul__(self._get_other(other)))

    def __rmul__(self, other):
        return fix_precision(self._d.__rmul__(self._get_other(other)))

    def __truediv__(self, other):
        return fix_precision(self._d.__truediv__(self._get_other(other)))

    def __rtruediv__(self, other):
        return fix_precision(self._d.__rtruediv__(self._get_other(other)))

    def __divmod__(self, other):
        return fix_precision(self._d.__divmod__(self._get_other(other)))

    def __rdivmod__(self, other):
        return fix_precision(self._d.__divmod__(self._get_other(other)))

    def __mod__(self, other):
        return fix_precision(self._d.__mod__(self._get_other(other)))

    def __rmod__(self, other):
        return fix_precision(self._d.__rmod__(self._get_other(other)))

    def __floordiv__(self, other):
        return fix_precision(self._d.__floordiv__(self._get_other(other)))

    def __rfloordiv__(self, other):
        return fix_precision(self._d.__rfloordiv__(self._get_other(other)))

    def __pow__(self, other):
        return fix_precision(self._d.__pow__(self._get_other(other)))

    def __rpow__(self, other):
        return fix_precision(self._d.__rpow__(self._get_other(other)))

    def __int__(self):
        return self._d.__int__()

    def __float__(self):
        return float(self._d)

    def __round__(self, n=None):
        return self._d.__round__(n)


exports = {
    'decimal': ContractingDecimal
}
