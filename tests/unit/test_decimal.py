from decimal import Decimal
import decimal
import math

from contracting.stdlib.bridge.decimal import ContractingDecimal, fix_precision, MAX_DECIMAL, neg_sci_not
from unittest import TestCase
import unittest


class TestDecimal(TestCase):
    def test_init(self):
        ContractingDecimal('1.1')

    def test_init_float(self):
        ContractingDecimal(1.2)

    def test_init_int(self):
        ContractingDecimal(1)

    def test_bool_true(self):
        self.assertTrue(ContractingDecimal(1))

    def test_bool_false(self):
        self.assertFalse(ContractingDecimal(0))

    def test_eq_whole_numbers(self):
        self.assertEqual(ContractingDecimal(1), ContractingDecimal(1))

    def test_eq_floats(self):
        self.assertEqual(ContractingDecimal(1.234), ContractingDecimal(1.234))

    def test_lt(self):
        self.assertLess(ContractingDecimal(1), ContractingDecimal(2))
        self.assertLess(ContractingDecimal(1.1), ContractingDecimal(2.2))

    def test_lte(self):
        self.assertLessEqual(ContractingDecimal(1), ContractingDecimal(2))
        self.assertLessEqual(ContractingDecimal(1.1), ContractingDecimal(2.2))
        self.assertLessEqual(ContractingDecimal(2.2), ContractingDecimal(2.2))

    def test_gt(self):
        self.assertGreater(ContractingDecimal(10), ContractingDecimal(2))
        self.assertGreater(ContractingDecimal(10.1), ContractingDecimal(2.2))

    def test_gte(self):
        self.assertGreaterEqual(ContractingDecimal(10), ContractingDecimal(2))
        self.assertGreaterEqual(ContractingDecimal(10.1), ContractingDecimal(2.2))
        self.assertGreaterEqual(ContractingDecimal(2.2), ContractingDecimal(2.2))

    def test_str(self):
        f = ContractingDecimal(1.23445)
        self.assertEqual(str(f), '1.23445')

    def test_neg(self):
        self.assertEqual(-ContractingDecimal(1), ContractingDecimal(-1))

    def test_pos(self):
        self.assertEqual(+ContractingDecimal(1), ContractingDecimal(1))

    def test_other_equality(self):
        self.assertEqual(ContractingDecimal(1), 1)
        self.assertEqual(ContractingDecimal(1), 1.0)

    def test_abs(self):
        self.assertEqual(abs(ContractingDecimal(1)), 1)
        self.assertEqual(abs(ContractingDecimal(-1)), 1)

    def test_add(self):
        self.assertEqual(ContractingDecimal(1) + ContractingDecimal(1), 2)
        self.assertEqual(ContractingDecimal(1) + ContractingDecimal(10), 11)

        self.assertEqual(ContractingDecimal(1.23456) + ContractingDecimal(6.54321), ContractingDecimal(7.77777))

    def test_arbitrarily_large_number(self):
        a = ContractingDecimal('38327950288419716939937510.582097494459230781640628620899')
        b = ContractingDecimal('67523846748184676694051320.005681271452635608277857713427')
        c = ContractingDecimal('105851797036604393633988830.587778765911866389918486334326')

        self.assertEqual(a + b, c)

    def test_zero_equality(self):
        self.assertEqual(ContractingDecimal(0), 0)

    def test_sub(self):
        self.assertEqual(ContractingDecimal(1) - ContractingDecimal(1), 0)
        self.assertEqual(ContractingDecimal(1) - ContractingDecimal(10), -9)

        self.assertEqual(ContractingDecimal(1.23456) - ContractingDecimal(6.54321), ContractingDecimal(-5.30865))

    def test_add_negs(self):
        self.assertEqual(ContractingDecimal(1) + ContractingDecimal(-1), 0)

    def test_radd(self):
        self.assertEqual(1 + ContractingDecimal(1), 2)
        self.assertEqual(1 + ContractingDecimal(10), 11)

        self.assertEqual(1.23456 + ContractingDecimal(6.54321), ContractingDecimal(7.77777))

    def test_rsub(self):
        self.assertEqual(1 - ContractingDecimal(1), 0)
        self.assertEqual(1 - ContractingDecimal(10), -9)

        self.assertEqual(1.23456 - ContractingDecimal(6.54321), ContractingDecimal(-5.30865))

    def test_mul(self):
        self.assertEqual(ContractingDecimal(5) * ContractingDecimal(42), 210)
        self.assertEqual(ContractingDecimal(0) * ContractingDecimal(100), 0)
        self.assertEqual(ContractingDecimal(-5) * ContractingDecimal(42), -210)
        self.assertEqual(ContractingDecimal(5.1234) * ContractingDecimal(2.3451), ContractingDecimal('12.01488534'))

    def test_rmul(self):
        self.assertEqual(5 * ContractingDecimal(42), 210)
        self.assertEqual(0 * ContractingDecimal(100), 0)
        self.assertEqual(-5 * ContractingDecimal(42), -210)
        self.assertEqual(5.1234 * ContractingDecimal(2.3451), ContractingDecimal('12.01488534'))

    def test_div(self):
        self.assertEqual((ContractingDecimal(1) / ContractingDecimal(3)), ContractingDecimal('0.333333333333333333333333333333'))
        self.assertEqual(ContractingDecimal(3) / ContractingDecimal(1), 3)

    def test_div_large_decimals(self):
        a = '0.78164062862089986280348253421170'
        b = '0.53642401735797937714409102114816'

        c = ContractingDecimal(a) / ContractingDecimal(b)

        print(c)

    def test_fix_precision_cuts_too_low(self):
        d = Decimal('1.123456789012345678901234567890123')
        e = Decimal('1.12345678901234567890123456789')

        self.assertEqual(fix_precision(d), e)

    def test_fix_precision_cuts_too_high(self):
        e = Decimal('123456789012345678901234567890')
        self.assertEqual(fix_precision(e), MAX_DECIMAL)

    def test_fix_precision_doesnt_cut_high(self):
        e = Decimal('12345678901234567890123456789')
        self.assertEqual(fix_precision(e), e)

    def test_fix_precision_cuts_all_decimals_if_too_high(self):
        e = Decimal('123456789012345678901234567890.123456')
        self.assertEqual(fix_precision(e), MAX_DECIMAL)

    def test_fix_precision_cuts_decimals_if_high_but_not_too_high(self):
        e = Decimal('12345678901234567890123456789.123456789012345678901234567890')
        f = Decimal('12345678901234567890123456789.12345678901234567890123456789')

        self.assertEqual(fix_precision(e), f)

    def test_contracting_decimal_can_round(self):
        s = '12345678901234567890123456789.123456789012345678901234567890'
        self.assertEqual(round(Decimal(s), 10), round(ContractingDecimal(s), 10))

    def test_sci_not_whole_number(self):
        s = '2e-5'
        expected = '0.00002'

        self.assertEqual(neg_sci_not(s), expected)

    def test_sci_not_decimal(self):
        s = '2.2e-7'
        expected = '0.00000022'

        self.assertEqual(neg_sci_not(s), expected)

    def test_sci_not_e0(self):
        s = '2e-0'
        expected = '2'

        self.assertEqual(neg_sci_not(s), expected)

    def test_sci_not_extra_precision(self):
        s = '20e-5'
        expected = '20e-5'

        self.assertEqual(neg_sci_not(s), expected)

if "__main__" == __name__:
    unittest.main()