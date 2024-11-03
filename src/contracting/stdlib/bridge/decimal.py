from decimal import Decimal, Context, ROUND_FLOOR
import decimal

# Define precision constants
MAX_UPPER_PRECISION = 30
MAX_LOWER_PRECISION = 30

# Set the decimal context for precision and rounding
CONTEXT = Context(
    prec=MAX_UPPER_PRECISION + MAX_LOWER_PRECISION,
    rounding=ROUND_FLOOR,
    Emin=-100,
    Emax=100
)
decimal.setcontext(CONTEXT)

# Create min and max decimal strings for precision boundaries
def make_min_decimal_str(prec):
    return '0.' + '0' * (prec - 1) + '1'

def make_max_decimal_str(prec):
    return '1' + '0' * (prec - 1)

# Convert scientific notation to non-exponential format if needed
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

# Define maximum and minimum decimal constants
MAX_DECIMAL = Decimal(make_max_decimal_str(MAX_UPPER_PRECISION))
MIN_DECIMAL = Decimal(make_min_decimal_str(MAX_LOWER_PRECISION))

# Ensure the value is within bounds and quantized
def fix_precision(x: Decimal):
    if x > MAX_DECIMAL:
        return MAX_DECIMAL
    return x.quantize(MIN_DECIMAL, rounding=ROUND_FLOOR).normalize()

# Main ContractingDecimal class
class ContractingDecimal:
    def _get_other(self, other):
        if isinstance(other, ContractingDecimal):
            return other._d
        elif isinstance(other, (float, int)):
            return Decimal(neg_sci_not(str(other)))
        return other

    def __init__(self, a):
        if isinstance(a, (float, int)):
            self._d = Decimal(neg_sci_not(str(a)))
        elif isinstance(a, str):
            self._d = Decimal(neg_sci_not(a))
        elif isinstance(a, Decimal):
            self._d = a
        else:
            self._d = Decimal(a)

        # Clamp and quantize during initialization
        self._d = fix_precision(self._d)

    def __bool__(self):
        return self._d > 0

    def __eq__(self, other):
        return self._d == self._get_other(other)

    def __lt__(self, other):
        return self._d < self._get_other(other)

    def __le__(self, other):
        return self._d <= self._get_other(other)

    def __gt__(self, other):
        return self._d > self._get_other(other)

    def __ge__(self, other):
        return self._d >= self._get_other(other)

    def __str__(self):
        return self._d.to_eng_string()

    def __repr__(self):
        return self._d.to_eng_string()

    def __neg__(self):
        return ContractingDecimal(-self._d)

    def __pos__(self):
        return self

    def __abs__(self):
        return ContractingDecimal(abs(self._d))

    def __add__(self, other):
        return ContractingDecimal(fix_precision(self._d + self._get_other(other)))

    def __radd__(self, other):
        return ContractingDecimal(fix_precision(self._get_other(other) + self._d))

    def __sub__(self, other):
        return ContractingDecimal(fix_precision(self._d - self._get_other(other)))

    def __rsub__(self, other):
        return ContractingDecimal(fix_precision(self._get_other(other) - self._d))

    def __mul__(self, other):
        return ContractingDecimal(fix_precision(self._d * self._get_other(other)))

    def __rmul__(self, other):
        return ContractingDecimal(fix_precision(self._get_other(other) * self._d))

    def __truediv__(self, other):
        return ContractingDecimal(fix_precision(self._d / self._get_other(other)))

    def __rtruediv__(self, other):
        return ContractingDecimal(fix_precision(self._get_other(other) / self._d))

    def __mod__(self, other):
        return ContractingDecimal(fix_precision(self._d % self._get_other(other)))

    def __rmod__(self, other):
        return ContractingDecimal(fix_precision(self._get_other(other) % self._d))

    def __floordiv__(self, other):
        return ContractingDecimal(fix_precision(self._d // self._get_other(other)))

    def __rfloordiv__(self, other):
        return ContractingDecimal(fix_precision(self._get_other(other) // self._d))

    def __pow__(self, other):
        return ContractingDecimal(fix_precision(self._d ** self._get_other(other)))

    def __rpow__(self, other):
        return ContractingDecimal(fix_precision(self._get_other(other) ** self._d))

    def __int__(self):
        return int(self._d)

    def __float__(self):
        return float(self._d)

    def __round__(self, n=None):
        return round(self._d, n)

# Export ContractingDecimal for external use
exports = {
    'decimal': ContractingDecimal
}
