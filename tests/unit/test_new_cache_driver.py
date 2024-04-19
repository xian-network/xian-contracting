from unittest import TestCase
from contracting.storage.driver import Driver


class TestCacheDriver(TestCase):
    def setUp(self):
        self.d = Driver()
        # FIXME: Doesn't exist anymore
        self.d.flush()

        # FIXME: Doesn't exist anymore
        self.c = CacheDriver(self.d)

    def test_get_adds_to_read(self):
        self.c.get('thing')
        self.assertTrue('thing' in self.c.pending_reads)

    def test_set_adds_to_cache_and_pending_writes(self):
        self.c.set('thing', 1234)
        self.assertEqual(self.c.pending_writes['thing'], 1234)

    def test_object_in_cache_returns_from_cache(self):
        self.d.set('thing', 8999)
        self.c.get('thing')
        self.assertEqual(self.c.get('thing'), 8999)

    def test_commit_puts_all_objects_in_pending_writes_to_db(self):
        self.c.set('thing1', 1234)
        self.c.set('thing2', 1235)
        self.c.set('thing3', 1236)
        self.c.set('thing4', 1237)
        self.c.set('thing5', 1238)

        self.assertIsNone(self.d.get('thing1'))
        self.assertIsNone(self.d.get('thing2'))
        self.assertIsNone(self.d.get('thing3'))
        self.assertIsNone(self.d.get('thing4'))
        self.assertIsNone(self.d.get('thing5'))

        self.c.commit()

        self.assertEqual(self.d.get('thing1'), 1234)
        self.assertEqual(self.d.get('thing2'), 1235)
        self.assertEqual(self.d.get('thing3'), 1236)
        self.assertEqual(self.d.get('thing4'), 1237)
        self.assertEqual(self.d.get('thing5'), 1238)

    def test_flush_cache_resets_all_variables(self):
        self.c.set('thing1', 1234)
        self.c.set('thing2', 1235)
        self.c.get('something')

        self.assertTrue(len(self.c.pending_reads) > 0)
        self.assertTrue(len(self.c.pending_writes) > 0)

        self.c.rollback()

        self.assertFalse(len(self.c.pending_reads) > 0)
        self.assertFalse(len(self.c.pending_writes) > 0)

    def test_soft_apply_adds_changes_to_pending_deltas(self):
        self.c.driver.set('thing1', 9999)

        self.c.set('thing1', 8888)
        self.c.soft_apply('0')

        expected_deltas = {
            '0': {
                'writes': {'thing1': (9999, 8888)},
                'reads': {'thing1': 9999}
            }
        }

        self.assertDictEqual(self.c.pending_deltas, expected_deltas)

    def test_soft_apply_applies_the_changes_to_the_driver_but_not_hard_driver(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        self.c.set('thing1', 8888)
        self.c.soft_apply('0')

        res = self.c.get('thing1')

        self.assertEqual(res, 8888)
        self.assertEqual(self.c.driver.get('thing1'), 9999)

    def test_hard_apply_applies_hcl_if_exists(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        self.c.set('thing1', 8888)

        self.c.soft_apply('0')
        self.c.hard_apply('0')

        res = self.c.get('thing1')

        self.assertEqual(res, 8888)

        self.assertEqual(self.c.driver.get('thing1'), 8888)

    def test_rollback_applies_hcl_if_exists(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        self.c.set('thing1', 8888)

        self.c.soft_apply('0')
        self.c.rollback('0')

        res = self.c.get('thing1')

        self.assertEqual(res, 9999)

        self.assertEqual(self.c.driver.get('thing1'), 9999)

    def test_rollback_twice_returns(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        self.c.set('thing1', 8888)
        self.c.soft_apply('0')

        self.c.set('thing1', 7777)
        self.c.soft_apply('1')

        self.c.set('thing1', 6666)
        self.c.soft_apply('2')

        self.c.rollback('1')

        res = self.c.get('thing1')

        self.assertEqual(res, 8888)

        self.assertEqual(self.c.driver.get('thing1'), 9999)

    def test_rollback_removes_hlcs(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        self.c.set('thing1', 8888)
        self.c.soft_apply('0')

        self.c.set('thing1', 7777)
        self.c.soft_apply('1')

        self.c.set('thing1', 6666)
        self.c.soft_apply('2')

        self.c.rollback('1')

        self.assertIsNone(self.c.pending_deltas.get('2'))
        self.assertIsNone(self.c.pending_deltas.get('1'))

    def test_hard_apply_only_applies_changes_up_to_delta(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        self.c.set('thing1', 8888)
        self.c.soft_apply('0')

        self.c.set('thing1', 7777)
        self.c.soft_apply('1')

        self.c.set('thing1', 6666)
        self.c.soft_apply('2')

        self.c.set('thing1', 5555)
        self.c.soft_apply('3')

        self.c.hard_apply('1')

        res = self.c.get('thing1')

        self.assertEqual(res, 5555)

        self.assertEqual(self.c.driver.get('thing1'), 7777)

    def test_hard_apply_removes_hcls(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        self.c.set('thing1', 8888)
        self.c.soft_apply('0')

        self.c.set('thing1', 7777)
        self.c.soft_apply('1')

        self.c.set('thing1', 6666)
        self.c.soft_apply('2')

        self.c.hard_apply('0')

        hlcs = {'1':
                    {'writes': {'thing1': (8888, 7777)}, 'reads': {'thing1': 8888}},
                '2':
                    {'writes': {'thing1': (7777, 6666)}, 'reads': {'thing1': 7777}}
                }

        self.assertDictEqual(self.c.pending_deltas, hlcs)

    def test_rollback_returns_to_initial_state(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        self.c.set('thing1', 8888)
        self.c.soft_apply('0')
        self.assertEqual(self.c.get('thing1'), 8888)

        self.c.set('thing1', 7777)
        self.c.soft_apply('1')
        self.assertEqual(self.c.get('thing1'), 7777)

        self.c.set('thing1', 6666)
        self.c.soft_apply('2')
        self.assertEqual(self.c.get('thing1'), 6666)

        self.c.rollback()

        self.assertEqual(self.c.get('thing1'), 9999)
        self.assertEqual(self.c.driver.get('thing1'), 9999)

    def test_rollback_removes_hlcs(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        self.c.set('thing1', 8888)
        self.c.soft_apply('0')
        self.assertEqual(self.c.get('thing1'), 8888)

        self.c.set('thing1', 7777)
        self.c.soft_apply('1')
        self.assertEqual(self.c.get('thing1'), 7777)

        self.c.set('thing1', 6666)
        self.c.soft_apply('2')
        self.assertEqual(self.c.get('thing1'), 6666)

        self.c.rollback()

        self.assertDictEqual(self.c.pending_deltas, {})

    def test_find_returns_none(self):
        x = self.c.find('none')
        self.assertIsNone(x)

    def test_find_returns_driver(self):
        self.c.driver.set('none', 123)

        x = self.c.find('none')

        self.assertEqual(x, 123)

    def test_find_returns_cache(self):
        self.c.driver.set('none', 123)
        self.c.cache['none'] = 999

        x = self.c.find('none')

        self.assertEqual(x, 999)

    def test_find_returns_pending_writes(self):
        self.c.driver.set('none', 123)
        self.c.cache['none'] = 999
        self.c.pending_writes['none'] = 5555

        x = self.c.find('none')
        
        self.assertEqual(x, 5555)
