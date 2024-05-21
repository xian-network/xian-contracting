from unittest import TestCase
from contracting.storage.encoder import encode, decode, safe_repr, convert_dict, MONGO_MAX_INT, MONGO_MIN_INT
from contracting.stdlib.bridge.time import Datetime, Timedelta
from datetime import datetime
from contracting.stdlib.bridge.decimal import ContractingDecimal


class TestEncode(TestCase):
    def test_int_to_bytes(self):
        i = 1000
        b = '1000'

        self.assertEqual(encode(i), b)

    def test_str_to_bytes(self):
        s = 'hello'
        b = '"hello"'

        self.assertEqual(encode(s), b)

    def test_dec_to_bytes(self):
        d = 1.098409840984
        b = '1.098409840984'

        self.assertEqual(encode(d), b)

    def test_decode_bytes_to_int(self):
        b = '1234'
        i = 1234

        self.assertEqual(decode(b), i)

    def test_decode_bytes_to_str(self):
        b = '"howdy"'
        s = 'howdy'

        self.assertEqual(decode(b), s)

    def test_decode_bytes_to_dec(self):
        b = '{"__fixed__":"0.0044997618965276"}'
        d = ContractingDecimal('0.0044997618965276')

        # _d is the actual Decimal object included in the wrapped stdlib ContractingDecimal
        self.assertEqual(decode(b)._d, d)

    def test_decode_failure(self):
        b = b'xwow'

        self.assertIsNone(decode(b))

    def test_date_encode(self):
        d = Datetime(2019, 1, 1)

        _d = encode(d)

        self.assertEqual(_d, '{"__time__":[2019,1,1,0,0,0,0]}')

    def test_date_decode(self):
        _d = '{"__time__": [2019, 1, 1, 0, 0, 0, 0]}'

        d = decode(_d)

        self.assertEqual(Datetime(2019, 1, 1), d)

    def test_timedelta_encode(self):
        t = Timedelta(weeks=1, days=1)

        _t = encode(t)

        self.assertEqual('{"__delta__":[8,0]}', _t)

    def test_timedelta_decode(self):
        _t = '{"__delta__": [8, 0]}'

        t = decode(_t)

        self.assertEqual(t, Timedelta(weeks=1, days=1))

    def test_int_encode(self):
        i = 10

        self.assertEqual(str(i), encode(i))

    def test_int_decode(self):
        i = '10'

        self.assertEqual(10, decode(i))

    def test_bigint_encode(self):
        si = MONGO_MIN_INT - 1
        bi = MONGO_MAX_INT + 1

        self.assertEqual('{"__big_int__":"' + str(bi) + '"}', encode(bi))
        self.assertEqual('{"__big_int__":"' + str(si) + '"}', encode(si))

    def test_bigint_decode(self):
        _bi = '{"__big_int__":' + str(MONGO_MAX_INT+1) + '}'

        self.assertEqual(decode(_bi), MONGO_MAX_INT+1)

    def test_encode_ints_nested_list(self):
        d = {'lists':[ {'i': 123,'bi': MONGO_MAX_INT} ]}
        expected = '{"lists":[{"i":123,"bi":{"__big_int__":"' + str(MONGO_MAX_INT) + '"}}]}'

        self.assertEqual(encode(d), expected)

    def test_encode_dict_with_list_containing_different_types(self):
        d = {'lists':[ {'i': 123,'bi': MONGO_MAX_INT}, 'hello' ]}
        expected = '{"lists":[{"i":123,"bi":{"__big_int__":"' + str(MONGO_MAX_INT) + '"}},"hello"]}'

        self.assertEqual(encode(d), expected)

    def test_encode_ints_nested_dict(self):
        d = {'d': {'bi': MONGO_MAX_INT, 'str': 'hello'}}
        expected = '{"d":{"bi":{"__big_int__":"' + str(MONGO_MAX_INT) + '"},"str":"hello"}}'

        self.assertEqual(encode(d), expected)

    def test_safe_repr_non_object(self):
        a = str(1)
        b = safe_repr(1)

        self.assertEqual(a, b)

    def test_safe_repr_arbitrary_object(self):
        class Object:
            pass

        a = Object()
        b = Object()

        self.assertEqual(safe_repr(a), safe_repr(b))

    def test_safe_repr_decimal_object(self):
        a = Timedelta(weeks=1, days=1)
        b = Timedelta(weeks=1, days=1)

        self.assertEqual(safe_repr(a), safe_repr(b))

    def test_safe_repr_decimal_object_different_not_equal(self):
        a = Timedelta(weeks=1, days=1)
        b = Timedelta(weeks=2, days=1)

        self.assertNotEqual(safe_repr(a), safe_repr(b))

    def test_safe_repr_assertion_error_string(self):
        a = AssertionError('Hello')
        b = AssertionError('Hello')

        self.assertEqual(safe_repr(a), safe_repr(b))

    def test_contracting_decimal(self):
        c = ContractingDecimal(a=123.456)
        b = '{"__fixed__":"123.456"}'

        self.assertEqual(encode(c), b)

    def test_decode_fixed_trailing_doesnt_get_rid_of_zeros_properly(self):
        b = '{"__fixed__":"1.10"}'

        d = decode(b)

    def test_encoding_fixed_trailing_zeros(self):
        b = ContractingDecimal('123.000000')

        e = encode(b)

        print(e)

    def test_convert_returns_normal_dict(self):
        d = {
            1: 2,
            "a": "b"
        }

        d2 = convert_dict(d)
        self.assertEqual(d, d2)

    def test_convert_bigint(self):
        d = {'bigint': {'__big_int__': str(2**65)}}
        expected = {'bigint': 2**65}

        self.assertDictEqual(convert_dict(d), expected)

    def test_convert_contracting_decimal(self):
        d = {
            'kwargs': {
                '__fixed__': '0.1234'
            }
        }

        expected = {
            'kwargs': ContractingDecimal('0.1234')
        }

        self.assertEqual(expected, convert_dict(d))

    def test_convert_contracting_datetime(self):
        d = {
            'kwargs': {
                    "__time__": [
                      2021,
                      4,
                      29,
                      21,
                      30,
                      54,
                      0
                    ]
                  }
        }

        expected = {
            'kwargs': Datetime(2021, 4, 29, 21, 30, 54, 0)
        }

        self.assertEqual(expected, convert_dict(d))

    def test_convert_contracting_timedelta(self):
        d = {
            'kwargs': {
                    "__delta__": [8, 0]
            }
        }

        expected = {
            'kwargs': Timedelta(days=8, seconds=0)
        }

        self.assertEqual(expected, convert_dict(d))

    def test_convert_contracting_bytes(self):
        d = {
            'kwargs': {
                    "__bytes__": "123456"
            }
        }

        expected = {
            'kwargs': b'\x124V'
        }

        self.assertEqual(expected, convert_dict(d))

    def test_multiple_conversions(self):
        d = {
            'kwargs': {
                '__fixed__': '0.1234'
            },
            'kwargs2': {
                "__time__": [
                      2021,
                      4,
                      29,
                      21,
                      30,
                      54,
                      0
                    ]
                  },
            'kwargs3': {
                "__delta__": [8, 0]
            },
            'kwargs4': {
                "__bytes__": "123456"
            }
        }

        expected = {
            'kwargs': ContractingDecimal('0.1234'),
            'kwargs2': Datetime(2021, 4, 29, 21, 30, 54, 0),
            'kwargs3': Timedelta(days=8, seconds=0),
            'kwargs4': b'\x124V',
        }

        self.assertEqual(expected, convert_dict(d))

    def test_nested_dictionaries(self):
        d = {
            'kwargs': {
                '__fixed__': '0.1234'
            },
            'thing': {
                'thing2': {
                    "__time__": [
                        2021,
                        4,
                        29,
                        21,
                        30,
                        54,
                        0
                    ]
                },
            }
        }

        expected = {
            'kwargs': ContractingDecimal('0.1234'),
            'thing': {
                'thing2': Datetime(2021, 4, 29, 21, 30, 54, 0),
            }
        }

        d2 = convert_dict(d)

        self.assertEqual(expected, d2)

    def test_lists(self):
        d = {
            'kwargs': [
                {
                    '__fixed__': '0.1234'
                },
                {
                    '__fixed__': '0.1235'
                },
                {
                    '__fixed__': '0.1236'
                },
                {
                    '__fixed__': '0.1237'
                },
                {
                    '__fixed__': '0.1238'
                },
            ]
        }

        expected = {
            'kwargs': [
                ContractingDecimal('0.1234'),
                ContractingDecimal('0.1235'),
                ContractingDecimal('0.1236'),
                ContractingDecimal('0.1237'),
                ContractingDecimal('0.1238'),
            ]
        }

        d2 = convert_dict(d)

        self.assertEqual(expected, d2)
