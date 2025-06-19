from unittest import TestCase
from contracting.stdlib.bridge.time import Datetime, Timedelta
from contracting.stdlib.bridge.decimal import ContractingDecimal
from datetime import datetime as dt
from datetime import timedelta


class TestDatetime(TestCase):
    def test_datetime_variables_set(self):
        now = dt.now()

        d = Datetime(now.year, now.month, now.day)

        self.assertEqual(0, d.microsecond)
        self.assertEqual(0, d.second)
        self.assertEqual(0, d.minute)
        self.assertEqual(0, d.hour)
        self.assertEqual(now.day, d.day)
        self.assertEqual(now.month, d.month)
        self.assertEqual(now.year, d.year)

    ###
    # ==
    ###
    def test_datetime_eq_true(self):
        now = dt.now()

        d = Datetime(now.year, now.month, now.day)
        e = Datetime(now.year, now.month, now.day)

        self.assertTrue(d == e)

    def test_datetime_eq_false(self):
        now = dt.now()
        d = Datetime(now.year, now.month, now.day)

        then = now + timedelta(days=1)
        e = Datetime(then.year, then.month, then.day)

        self.assertFalse(d == e)

    ###
    # !=
    ###
    def test_datetime_ne_false(self):
        now = dt.now()

        d = Datetime(now.year, now.month, now.day)
        e = Datetime(now.year, now.month, now.day)

        self.assertFalse(d != e)

    def test_datetime_ne_true(self):
        now = dt.now()
        d = Datetime(now.year, now.month, now.day)

        then = now + timedelta(days=1)
        e = Datetime(then.year, then.month, then.day)

        self.assertTrue(d != e)

    ###
    # <
    ###
    def test_datetime_lt_true(self):
        now = dt.now()
        d = Datetime(now.year, now.month, now.day)

        then = now + timedelta(days=1)
        e = Datetime(then.year, then.month, then.day)

        self.assertTrue(d < e)

    def test_datetime_lt_false(self):
        now = dt.now()
        d = Datetime(now.year, now.month, now.day)

        then = now + timedelta(days=1)
        e = Datetime(then.year, then.month, then.day)

        self.assertFalse(e < d)

    ###
    # >
    ###
    def test_datetime_gt_true(self):
        now = dt.now()
        d = Datetime(now.year, now.month, now.day)

        then = now + timedelta(days=1)
        e = Datetime(then.year, then.month, then.day)

        self.assertTrue(e > d)

    def test_datetime_gt_false(self):
        now = dt.now()
        d = Datetime(now.year, now.month, now.day)

        then = now + timedelta(days=1)
        e = Datetime(then.year, then.month, then.day)

        self.assertFalse(d > e)

    ###
    # >=
    ###
    def test_datetime_ge_true_g(self):
        now = dt.now()
        d = Datetime(now.year, now.month, now.day)

        then = now + timedelta(days=1)
        e = Datetime(then.year, then.month, then.day)

        self.assertTrue(e >= d)

    def test_datetime_ge_true_eq(self):
        now = dt.now()

        d = Datetime(now.year, now.month, now.day)
        e = Datetime(now.year, now.month, now.day)

        self.assertTrue(d >= e)

    def test_datetime_ge_false_g(self):
        now = dt.now()
        d = Datetime(now.year, now.month, now.day)

        then = now + timedelta(days=1)
        e = Datetime(then.year, then.month, then.day)

        self.assertFalse(d >= e)

    ###
    # <=
    ###
    def test_datetime_le_true(self):
        now = dt.now()
        d = Datetime(now.year, now.month, now.day)

        then = now + timedelta(days=1)
        e = Datetime(then.year, then.month, then.day)

        self.assertTrue(d <= e)

    def test_datetime_le_true_eq(self):
        now = dt.now()

        d = Datetime(now.year, now.month, now.day)
        e = Datetime(now.year, now.month, now.day)

        self.assertTrue(d <= e)

    def test_datetime_le_false(self):
        now = dt.now()
        d = Datetime(now.year, now.month, now.day)

        then = now + timedelta(days=1)
        e = Datetime(then.year, then.month, then.day)

        self.assertFalse(e <= d)

    def test_datetime_subtraction_to_proper_timedelta(self):
        d = Datetime(2019, 1, 1)
        e = Datetime(2018, 1, 1)

        self.assertEqual((d - e), Timedelta(days=365))


    def test_datetime_strptime(self):
        d = dt(2019, 1, 1)
        self.assertEqual(str(Datetime.strptime(str(d), '%Y-%m-%d %H:%M:%S')), str(d))

    
    def test_datetime_strptime_invalid_format(self):
        d = dt(2019, 1, 1)
        with self.assertRaises(ValueError):
            Datetime.strptime(str(d), '%Y-%m-%d')

    def test_datetime_strptime_invalid_date(self):
        with self.assertRaises(ValueError):
            Datetime.strptime('2019-02-30 12:00:00', '%Y-%m-%d %H:%M:%S')


    def test_datetime_strptime_invalid_date_format(self):
        with self.assertRaises(ValueError):
            Datetime.strptime('2019-02-30 12:00:00', '%Y-%m-%d %H:%M:%S')


    def test_datetime_returns_correct_datetime_cls(self):
        d = dt(2019, 1, 1)
        self.assertEqual(Datetime.strptime(str(d), '%Y-%m-%d %H:%M:%S'), Datetime(2019, 1, 1))

    ###
    # timestamp() method tests
    ###
    def test_timestamp_returns_contracting_decimal(self):
        d = Datetime(2019, 1, 1, 12, 0, 0)
        timestamp = d.timestamp()
        self.assertIsInstance(timestamp, ContractingDecimal)

    def test_timestamp_precision_with_microseconds(self):
        # Test that microseconds are preserved in the timestamp
        d = Datetime(2019, 1, 1, 12, 0, 0, 123456)
        timestamp = d.timestamp()
        
        # Convert to string to check decimal precision
        timestamp_str = str(timestamp)
        self.assertTrue('.123456' in timestamp_str)

    def test_timestamp_conversion_to_int(self):
        d = Datetime(2019, 1, 1, 12, 0, 0, 123456)
        timestamp = d.timestamp()
        
        # Test conversion to int (should truncate fractional part)
        timestamp_int = int(timestamp)
        self.assertIsInstance(timestamp_int, int)
        self.assertEqual(timestamp_int, 1546344000)  # Expected Unix timestamp for 2019-01-01 12:00:00 UTC

    def test_timestamp_conversion_to_float(self):
        d = Datetime(2019, 1, 1, 12, 0, 0, 123456)
        timestamp = d.timestamp()
        
        # Test conversion to float
        timestamp_float = float(timestamp)
        self.assertIsInstance(timestamp_float, float)
        self.assertAlmostEqual(timestamp_float, 1546344000.123456, places=6)

    def test_timestamp_consistency_with_standard_datetime(self):
        # Test that our timestamp matches Python's standard datetime.timestamp()
        year, month, day, hour, minute, second, microsecond = 2019, 1, 1, 12, 0, 0, 123456
        
        # Create both datetime objects
        contracting_dt = Datetime(year, month, day, hour, minute, second, microsecond)
        standard_dt = dt(year, month, day, hour, minute, second, microsecond)
        
        # Compare timestamps (allowing for small floating point differences)
        contracting_timestamp = float(contracting_dt.timestamp())
        standard_timestamp = standard_dt.timestamp()
        
        self.assertAlmostEqual(contracting_timestamp, standard_timestamp, places=6)

    def test_timestamp_different_dates(self):
        # Test timestamps for different dates
        d1 = Datetime(2020, 1, 1)
        d2 = Datetime(2021, 1, 1)
        
        ts1 = d1.timestamp()
        ts2 = d2.timestamp()
        
        # Later date should have larger timestamp
        self.assertTrue(ts2 > ts1)
        
        # Difference should be approximately one year in seconds
        diff = ts2 - ts1
        year_in_seconds = ContractingDecimal('31536000')  # 365 days * 24 hours * 60 minutes * 60 seconds
        self.assertAlmostEqual(float(diff), float(year_in_seconds), delta=86400)  # Allow 1 day delta for leap year

    def test_timestamp_zero_microseconds(self):
        # Test datetime with zero microseconds
        d = Datetime(2019, 1, 1, 12, 0, 0, 0)
        timestamp = d.timestamp()
        
        # Should still be a ContractingDecimal but with .0 or no fractional part
        self.assertIsInstance(timestamp, ContractingDecimal)
        timestamp_int = int(timestamp)
        self.assertEqual(timestamp_int, 1546344000)

    def test_timestamp_arithmetic_operations(self):
        # Test that ContractingDecimal timestamps can be used in arithmetic
        d = Datetime(2019, 1, 1, 12, 0, 0)
        timestamp = d.timestamp()
        
        # Add 3600 seconds (1 hour)
        future_timestamp = timestamp + ContractingDecimal('3600')
        self.assertIsInstance(future_timestamp, ContractingDecimal)
        
        # Subtract 1800 seconds (30 minutes)
        past_timestamp = timestamp - ContractingDecimal('1800')
        self.assertIsInstance(past_timestamp, ContractingDecimal)
        
        # Check the difference is correct
        diff = future_timestamp - past_timestamp
        self.assertEqual(diff, ContractingDecimal('5400'))  # 3600 + 1800

    def test_timestamp_comparison_operations(self):
        # Test timestamp comparisons
        d1 = Datetime(2019, 1, 1, 12, 0, 0)
        d2 = Datetime(2019, 1, 1, 12, 0, 1)  # 1 second later
        
        ts1 = d1.timestamp()
        ts2 = d2.timestamp()
        
        self.assertTrue(ts2 > ts1)
        self.assertTrue(ts1 < ts2)
        self.assertFalse(ts1 == ts2)
        self.assertTrue(ts1 != ts2)

    ###
    # fromtimestamp() method tests
    ###
    def test_fromtimestamp_with_int(self):
        # Test creating Datetime from integer timestamp
        timestamp = 1546344000  # 2019-01-01 12:00:00 UTC
        d = Datetime.fromtimestamp(timestamp)
        
        self.assertIsInstance(d, Datetime)
        self.assertEqual(d.year, 2019)
        self.assertEqual(d.month, 1)
        self.assertEqual(d.day, 1)

    def test_fromtimestamp_rejects_float(self):
        # Test that float timestamps are rejected for consensus safety
        timestamp = 1546344000.123456
        with self.assertRaises(TypeError):
            Datetime.fromtimestamp(timestamp)

    def test_fromtimestamp_with_contracting_decimal(self):
        # Test creating Datetime from ContractingDecimal timestamp
        timestamp = ContractingDecimal('1546344000.123456')
        d = Datetime.fromtimestamp(timestamp)
        
        self.assertIsInstance(d, Datetime)
        self.assertEqual(d.year, 2019)
        self.assertEqual(d.month, 1)
        self.assertEqual(d.day, 1)
        self.assertEqual(d.microsecond, 123456)

    def test_fromtimestamp_round_trip(self):
        # Test that timestamp() and fromtimestamp() are inverse operations
        # Use a simple UTC timestamp to avoid timezone issues
        timestamp = ContractingDecimal('1546300800')  # 2019-01-01 00:00:00 UTC
        
        # Convert to datetime and back
        datetime_obj = Datetime.fromtimestamp(timestamp)
        reconstructed_timestamp = datetime_obj.timestamp()
        
        # Should be close (accounting for potential timezone differences)
        self.assertAlmostEqual(float(timestamp), float(reconstructed_timestamp), delta=3600)  # Allow 1 hour difference for timezone

    def test_fromtimestamp_consistency_with_standard_datetime(self):
        # Test that fromtimestamp matches Python's standard datetime.fromtimestamp()
        timestamp = ContractingDecimal('1546344000.123456')
        
        contracting_dt = Datetime.fromtimestamp(timestamp)
        standard_dt = dt.fromtimestamp(float(timestamp))
        
        self.assertEqual(contracting_dt.year, standard_dt.year)
        self.assertEqual(contracting_dt.month, standard_dt.month)
        self.assertEqual(contracting_dt.day, standard_dt.day)
        self.assertEqual(contracting_dt.hour, standard_dt.hour)
        self.assertEqual(contracting_dt.minute, standard_dt.minute)
        self.assertEqual(contracting_dt.second, standard_dt.second)
        self.assertEqual(contracting_dt.microsecond, standard_dt.microsecond)

    def test_fromtimestamp_different_timestamps(self):
        # Test different timestamp values
        timestamps = [
            0,  # Unix epoch
            1000000000,  # 2001-09-09
            1577836800,  # 2020-01-01 00:00:00 UTC
            ContractingDecimal('1609459200')  # 2021-01-01 00:00:00 UTC (without fractional part)
        ]
        
        for ts in timestamps:
            d = Datetime.fromtimestamp(ts)
            self.assertIsInstance(d, Datetime)
            # Verify round-trip works (allowing for timezone differences)
            reconstructed_ts = d.timestamp()
            if isinstance(ts, ContractingDecimal):
                self.assertAlmostEqual(float(reconstructed_ts), float(ts), delta=3600)  # Allow 1 hour for timezone
            else:
                self.assertAlmostEqual(float(reconstructed_ts), float(ts), delta=3600)  # Allow 1 hour for timezone

    def test_fromtimestamp_edge_cases(self):
        # Test edge cases
        
        # Zero timestamp (Unix epoch)
        d_epoch = Datetime.fromtimestamp(0)
        self.assertEqual(d_epoch.year, 1970)
        self.assertEqual(d_epoch.month, 1)
        self.assertEqual(d_epoch.day, 1)
        
        # Large timestamp
        large_ts = 2147483647  # Max 32-bit signed integer
        d_large = Datetime.fromtimestamp(large_ts)
        self.assertIsInstance(d_large, Datetime)
        
        # ContractingDecimal with no fractional part
        cd_no_frac = ContractingDecimal('1546344000')
        d_no_frac = Datetime.fromtimestamp(cd_no_frac)
        self.assertEqual(d_no_frac.microsecond, 0)

    def test_fromtimestamp_consensus_safety(self):
        """Test that fromtimestamp produces identical results for consensus safety"""
        # Same timestamp in different safe input types should produce identical results
        timestamp_int = 1546344000
        timestamp_decimal = ContractingDecimal('1546344000')
        
        dt_int = Datetime.fromtimestamp(timestamp_int)
        dt_decimal = Datetime.fromtimestamp(timestamp_decimal)
        
        # Both should produce identical results
        self.assertEqual(dt_int.year, dt_decimal.year)
        self.assertEqual(dt_int.month, dt_decimal.month)
        self.assertEqual(dt_int.day, dt_decimal.day)
        self.assertEqual(dt_int.hour, dt_decimal.hour)
        self.assertEqual(dt_int.minute, dt_decimal.minute)
        self.assertEqual(dt_int.second, dt_decimal.second)
        self.assertEqual(dt_int.microsecond, dt_decimal.microsecond)

    def test_fromtimestamp_microsecond_precision_consensus(self):
        """Test microsecond precision without floating point issues"""
        # Test with precise decimal microseconds
        timestamp = ContractingDecimal('1546344000.123456')
        dt = Datetime.fromtimestamp(timestamp)
        
        # Should have exact microsecond precision
        self.assertEqual(dt.microsecond, 123456)
        
        # Test edge case: maximum microseconds
        timestamp_max_micro = ContractingDecimal('1546344000.999999')
        dt_max = Datetime.fromtimestamp(timestamp_max_micro)
        self.assertEqual(dt_max.microsecond, 999999)

    def test_fromtimestamp_bounds_validation(self):
        """Test that bounds validation prevents dangerous timestamps"""
        # Test negative timestamp (should fail)
        with self.assertRaises(ValueError):
            Datetime.fromtimestamp(-1)
        
        # Test too large timestamp (should fail)
        with self.assertRaises(ValueError):
            Datetime.fromtimestamp(ContractingDecimal('2147483648'))  # Beyond 32-bit limit
        
        # Test edge cases that should pass
        min_valid = Datetime.fromtimestamp(0)  # Unix epoch
        self.assertEqual(min_valid.year, 1970)
        
        max_valid = Datetime.fromtimestamp(2147483647)  # Max 32-bit
        self.assertEqual(max_valid.year, 2038)

    def test_fromtimestamp_deterministic_calculation(self):
        """Test that calculations are deterministic and repeatable"""
        timestamp = ContractingDecimal('1546344000.123456')
        
        # Multiple calls should produce identical results
        results = []
        for _ in range(10):
            dt = Datetime.fromtimestamp(timestamp)
            results.append((dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond))
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            self.assertEqual(result, first_result)

    def test_fromtimestamp_type_safety(self):
        """Test that fromtimestamp only accepts safe types for consensus"""
        # These types should be rejected
        unsafe_types = [
            1546344000.123456,  # float
            "1546344000",       # string
            [1546344000],       # list
            {"timestamp": 1546344000},  # dict
            None,               # None
            True,               # bool
        ]
        
        for unsafe_value in unsafe_types:
            with self.assertRaises(TypeError):
                Datetime.fromtimestamp(unsafe_value)
        
        # These types should be accepted
        safe_values = [
            1546344000,  # int
            ContractingDecimal('1546344000'),  # ContractingDecimal
            ContractingDecimal('1546344000.123456'),  # ContractingDecimal with precision
        ]
        
        for safe_value in safe_values:
            # Should not raise any exception
            dt = Datetime.fromtimestamp(safe_value)
            self.assertIsInstance(dt, Datetime)

