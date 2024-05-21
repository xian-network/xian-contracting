from unittest import TestCase
from contracting.storage.driver import Driver


class TestCacheDriver(TestCase):
    def setUp(self):
        self.d = Driver()
        self.d.flush_full()

    def test_get_adds_to_read(self):
        self.d.get('thing', save=True)
        self.assertTrue('thing' in self.d.pending_reads)

    def test_set_adds_to_cache_and_pending_writes(self):
        self.d.set('thing', 1234)
        self.assertEqual(self.d.pending_writes['thing'], 1234)

    def test_object_in_cache_returns_from_cache(self):
        self.d.set('thing', 8999)
        self.d.pending_writes.get('thing')
        self.assertEqual(self.d.pending_writes.get('thing'), 8999)

    def test_commit_puts_all_objects_in_pending_writes_to_db(self):
        self.d.set('thing1', 1234)
        self.d.set('thing2', 1235)
        self.d.set('thing3', 1236)
        self.d.set('thing4', 1237)
        self.d.set('thing5', 1238)

        self.assertEqual(self.d.pending_writes.get('thing1'), 1234)
        self.assertEqual(self.d.pending_writes.get('thing2'), 1235)
        self.assertEqual(self.d.pending_writes.get('thing3'), 1236)
        self.assertEqual(self.d.pending_writes.get('thing4'), 1237)
        self.assertEqual(self.d.pending_writes.get('thing5'), 1238)

    def test_flush_cache_resets_all_variables(self):
        self.d.set('thing1', 1234)
        self.d.set('thing2', 1235)
        self.d.pending_writes.get('something')

        self.assertTrue(len(self.d.pending_reads) > 0)
        self.assertTrue(len(self.d.pending_writes) > 0)

        self.d.rollback()

        self.assertFalse(len(self.d.pending_reads) > 0)
        self.assertFalse(len(self.d.pending_writes) > 0)

    def test_soft_apply_adds_changes_to_pending_deltas(self):
        self.d.driver.set('thing1', 9999)

        self.d.set('thing1', 8888)
        self.d.soft_apply('0')

        expected_deltas = {
            '0': {
                'writes': {'thing1': (9999, 8888)},
                'reads': {'thing1': 9999}
            }
        }

        self.assertDictEqual(self.d.pending_deltas, expected_deltas)

    def test_soft_apply_applies_the_changes_to_the_driver_but_not_hard_driver(self):
        self.d.set('thing1', 9999)
        self.d.commit()

        self.d.set('thing1', 8888)
        self.d.soft_apply('0')

        res = self.d.pending_writes.get('thing1')

        self.assertEqual(res, 8888)
        self.assertEqual(self.d.driver.get('thing1'), 9999)

    def test_hard_apply_applies_hcl_if_exists(self):
        self.d.set('thing1', 9999)
        self.d.commit()

        self.d.set('thing1', 8888)

        self.d.hard_apply('0')

        res = self.d.pending_writes.get('thing1')
        breakpoint()
        self.assertEqual(res, 8888)

        self.assertEqual(self.d.driver.get('thing1'), 8888)

    def test_rollback_applies_hcl_if_exists(self):
        self.d.set('thing1', 9999)
        self.d.commit()

        self.d.set('thing1', 8888)

        self.d.soft_apply('0')
        self.d.rollback('0')

        res = self.d.pending_writes.get('thing1')

        self.assertEqual(res, 9999)

        self.assertEqual(self.d.driver.get('thing1'), 9999)

    def test_rollback_twice_returns(self):
        self.d.set('thing1', 9999)
        self.d.commit()

        self.d.set('thing1', 8888)
        self.d.soft_apply('0')

        self.d.set('thing1', 7777)
        self.d.soft_apply('1')

        self.d.set('thing1', 6666)
        self.d.soft_apply('2')

        self.d.rollback('1')

        res = self.d.pending_writes.get('thing1')

        self.assertEqual(res, 8888)

        self.assertEqual(self.d.driver.get('thing1'), 9999)

    def test_rollback_removes_hlcs(self):
        self.d.set('thing1', 9999)
        self.d.commit()

        self.d.set('thing1', 8888)
        self.d.soft_apply('0')

        self.d.set('thing1', 7777)
        self.d.soft_apply('1')

        self.d.set('thing1', 6666)
        self.d.soft_apply('2')

        self.d.rollback('1')

        self.assertIsNone(self.d.pending_deltas.get('2'))
        self.assertIsNone(self.d.pending_deltas.get('1'))

    def test_hard_apply_only_applies_changes_up_to_delta(self):
        self.d.set('thing1', 9999)
        self.d.commit()

        self.d.set('thing1', 8888)
        self.d.soft_apply('0')

        self.d.set('thing1', 7777)
        self.d.soft_apply('1')

        self.d.set('thing1', 6666)
        self.d.soft_apply('2')

        self.d.set('thing1', 5555)
        self.d.soft_apply('3')

        self.d.hard_apply('1')

        res = self.d.pending_writes.get('thing1')

        self.assertEqual(res, 5555)

        self.assertEqual(self.d.driver.get('thing1'), 7777)

    def test_hard_apply_removes_hcls(self):
        self.d.set('thing1', 9999)
        self.d.commit()

        self.d.set('thing1', 8888)
        self.d.soft_apply('0')

        self.d.set('thing1', 7777)
        self.d.soft_apply('1')

        self.d.set('thing1', 6666)
        self.d.soft_apply('2')

        self.d.hard_apply('0')

        hlcs = {'1':
                    {'writes': {'thing1': (8888, 7777)}, 'reads': {'thing1': 8888}},
                '2':
                    {'writes': {'thing1': (7777, 6666)}, 'reads': {'thing1': 7777}}
                }

        self.assertDictEqual(self.d.pending_deltas, hlcs)

    def test_rollback_returns_to_initial_state(self):
        self.d.set('thing1', 9999)
        self.d.commit()

        self.d.set('thing1', 8888)
        self.d.soft_apply('0')
        self.assertEqual(self.d.pending_writes.get('thing1'), 8888)

        self.d.set('thing1', 7777)
        self.d.soft_apply('1')
        self.assertEqual(self.d.pending_writes.get('thing1'), 7777)

        self.d.set('thing1', 6666)
        self.d.soft_apply('2')
        self.assertEqual(self.d.pending_writes.get('thing1'), 6666)

        self.d.rollback()

        self.assertEqual(self.d.pending_writes.get('thing1'), 9999)
        self.assertEqual(self.d.driver.get('thing1'), 9999)

    def test_rollback_removes_hlcs(self):
        self.d.set('thing1', 9999)
        self.d.commit()

        self.d.set('thing1', 8888)
        self.d.soft_apply('0')
        self.assertEqual(self.d.pending_writes.get('thing1'), 8888)

        self.d.set('thing1', 7777)
        self.d.soft_apply('1')
        self.assertEqual(self.d.pending_writes.get('thing1'), 7777)

        self.d.set('thing1', 6666)
        self.d.soft_apply('2')
        self.assertEqual(self.d.pending_writes.get('thing1'), 6666)

        self.d.rollback()

        self.assertDictEqual(self.d.pending_deltas, {})

    def test_find_returns_none(self):
        x = self.d.find('none')
        self.assertIsNone(x)

    def test_find_returns_driver(self):
        self.d.set('none', 123)

        x = self.d.find('none')

        self.assertEqual(x, 123)
