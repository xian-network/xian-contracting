# from unittest import TestCase
# from contracting.storage.driver import RedisDriver, ContractDriver, DBMDriver, RocksDriver
# from contracting import config
# import random
#
# class TestAbstractDatabaseDriver(TestCase):
#     pass
#
# '''
# class TestLevelDBDriver(TestCase):
#     # Flush this sucker every test
#     def setUp(self):
#         self.d = LevelDBDriver(storage=1)
#         self.d.flush()
#
#     def tearDown(self):
#         self.d.flush()
#
#     def test_get_set(self):
#         a = 'a'
#         self.d.set('b', a)
#
#         b = self.d.get('b')
#         b = b.decode()
#         self.assertEqual(a, b)
#
#     def test_delete(self):
#         a = 'a'
#         self.d.set('b', a)
#
#         b = self.d.get('b')
#         b = b.decode()
#         self.assertEqual(a, b)
#
#         self.d.delete('b')
#
#         b = self.d.get('b')
#         self.assertIsNone(b)
#
#     def test_incrby(self):
#         self.d.set('inc', str(0))
#         inc = int(self.d.get('inc'))
#         self.assertEqual(inc, 0)
#         self.d.incrby('inc')
#         inc = int(self.d.get('inc'))
#         self.assertEqual(inc, 1)
#
#
#     def test_iter(self):
#
#         prefix_1_keys = [
#             'b77aa343e339bed781c7c2be1267cd597',
#             'bc22ede6e6fb4046d78bf2f9d1f8afdb6',
#             'b93dbb37d993846d70b8a92779cbfbfe9',
#             'be1a2783019de6ea7ef169cc55e48a3ae',
#             'b1fe8db32b9185d628f4c346f0455023e',
#             'bef918f83b6a0d1e4f980013342807cf8',
#             'b004cb9235acb5f689d20904692bc026e',
#             'b869ff9519d67354816af90867f4a5425',
#             'bcd8e9100dcb601f65e849c147e3e972e',
#             'b0111919a698f9816862b4ae662a6ed06',
#         ]
#
#         prefix_2_keys = [
#             'x37fbab0bd2e60563c79469e5be41e515',
#             'x30c6eb2ad176773b5ce6d590d2472dfe',
#             'x3d4fc9480f0a07b28aa7646d5066b54d',
#             'x387c3d4ab7f0c1c6ef549198fc14b525',
#             'x5c74dc83e132e435e8512599e1075bc0',
#             'x1472425d0d9bb5ff511e132896d54b13',
#             'x2cedb5c52163c22a0b5f179001959dd2',
#             'x6223f65e553280cd25cadeac6657555c',
#             'xeae18af37c223dde92a71fef55e64afe',
#             'xb8810784ffb360cd3ffc57b1d088e537',
#         ]
#
#         keys = prefix_1_keys + prefix_2_keys
#         random.shuffle(keys)
#
#         for k in keys:
#             self.d.set(k, k)
#
#         p1 = []
#
#         for k in self.d.iter(prefix='b'):
#             p1.append(k.decode())
#
#         prefix_1_keys.sort()
#         p1.sort()
#
#         self.assertListEqual(prefix_1_keys, p1)
#
#         p2 = []
#
#         for k in self.d.iter(prefix='x'):
#             p2.append(k.decode())
#
#         prefix_2_keys.sort()
#         p2.sort()
#
#         self.assertListEqual(prefix_2_keys, p2)
#
#     def test_keys(self):
#         prefix_1_keys = [
#             'b77aa343e339bed781c7c2be1267cd597',
#             'bc22ede6e6fb4046d78bf2f9d1f8afdb6',
#             'b93dbb37d993846d70b8a92779cbfbfe9',
#             'be1a2783019de6ea7ef169cc55e48a3ae',
#             'b1fe8db32b9185d628f4c346f0455023e',
#             'bef918f83b6a0d1e4f980013342807cf8',
#             'b004cb9235acb5f689d20904692bc026e',
#             'b869ff9519d67354816af90867f4a5425',
#             'bcd8e9100dcb601f65e849c147e3e972e',
#             'b0111919a698f9816862b4ae662a6ed06',
#         ]
#
#         prefix_2_keys = [
#             'x37fbab0bd2e60563c79469e5be41e515',
#             'x30c6eb2ad176773b5ce6d590d2472dfe',
#             'x3d4fc9480f0a07b28aa7646d5066b54d',
#             'x387c3d4ab7f0c1c6ef549198fc14b525',
#             'x5c74dc83e132e435e8512599e1075bc0',
#             'x1472425d0d9bb5ff511e132896d54b13',
#             'x2cedb5c52163c22a0b5f179001959dd2',
#             'x6223f65e553280cd25cadeac6657555c',
#             'xeae18af37c223dde92a71fef55e64afe',
#             'xb8810784ffb360cd3ffc57b1d088e537',
#         ]
#
#         keys = prefix_1_keys + prefix_2_keys
#         random.shuffle(keys)
#
#         for k in keys:
#             self.d.set(k, k)
#
#         ks = []
#
#         for k in self.d.keys():
#             ks.append(k.decode())
#
#         ks.sort()
#         keys.sort()
#
#         self.assertListEqual(keys, ks)
# '''
#
# class TestRedisDatabaseDriver(TestCase):
#     # Flush this sucker every test
#     def setUp(self):
#         self.d = RedisDriver(storage=1)
#         self.d.flush()
#
#     def tearDown(self):
#         self.d.flush()
#
#     def test_get_set(self):
#         a = 'a'
#         self.d.set('b', a)
#
#         b = self.d.get('b')
#         b = b.decode()
#         self.assertEqual(a, b)
#
#     def test_delete(self):
#         a = 'a'
#         self.d.set('b', a)
#
#         b = self.d.get('b')
#         b = b.decode()
#         self.assertEqual(a, b)
#
#         self.d.delete('b')
#
#         b = self.d.get('b')
#         self.assertIsNone(b)
#
#     def test_iter(self):
#
#         prefix_1_keys = [
#             'b77aa343e339bed781c7c2be1267cd597',
#             'bc22ede6e6fb4046d78bf2f9d1f8afdb6',
#             'b93dbb37d993846d70b8a92779cbfbfe9',
#             'be1a2783019de6ea7ef169cc55e48a3ae',
#             'b1fe8db32b9185d628f4c346f0455023e',
#             'bef918f83b6a0d1e4f980013342807cf8',
#             'b004cb9235acb5f689d20904692bc026e',
#             'b869ff9519d67354816af90867f4a5425',
#             'bcd8e9100dcb601f65e849c147e3e972e',
#             'b0111919a698f9816862b4ae662a6ed06',
#         ]
#
#         prefix_2_keys = [
#             'x37fbab0bd2e60563c79469e5be41e515',
#             'x30c6eb2ad176773b5ce6d590d2472dfe',
#             'x3d4fc9480f0a07b28aa7646d5066b54d',
#             'x387c3d4ab7f0c1c6ef549198fc14b525',
#             'x5c74dc83e132e435e8512599e1075bc0',
#             'x1472425d0d9bb5ff511e132896d54b13',
#             'x2cedb5c52163c22a0b5f179001959dd2',
#             'x6223f65e553280cd25cadeac6657555c',
#             'xeae18af37c223dde92a71fef55e64afe',
#             'xb8810784ffb360cd3ffc57b1d088e537',
#         ]
#
#         keys = prefix_1_keys + prefix_2_keys
#         random.shuffle(keys)
#
#         for k in keys:
#             self.d.set(k, k)
#
#         p1 = []
#
#         for k in self.d.iter(prefix='b'):
#             p1.append(k.decode())
#
#         prefix_1_keys.sort()
#         p1.sort()
#
#         self.assertListEqual(prefix_1_keys, p1)
#
#         p2 = []
#
#         for k in self.d.iter(prefix='x'):
#             p2.append(k.decode())
#
#         prefix_2_keys.sort()
#         p2.sort()
#
#         self.assertListEqual(prefix_2_keys, p2)
#
#     def test_keys(self):
#         prefix_1_keys = [
#             'b77aa343e339bed781c7c2be1267cd597',
#             'bc22ede6e6fb4046d78bf2f9d1f8afdb6',
#             'b93dbb37d993846d70b8a92779cbfbfe9',
#             'be1a2783019de6ea7ef169cc55e48a3ae',
#             'b1fe8db32b9185d628f4c346f0455023e',
#             'bef918f83b6a0d1e4f980013342807cf8',
#             'b004cb9235acb5f689d20904692bc026e',
#             'b869ff9519d67354816af90867f4a5425',
#             'bcd8e9100dcb601f65e849c147e3e972e',
#             'b0111919a698f9816862b4ae662a6ed06',
#         ]
#
#         prefix_2_keys = [
#             'x37fbab0bd2e60563c79469e5be41e515',
#             'x30c6eb2ad176773b5ce6d590d2472dfe',
#             'x3d4fc9480f0a07b28aa7646d5066b54d',
#             'x387c3d4ab7f0c1c6ef549198fc14b525',
#             'x5c74dc83e132e435e8512599e1075bc0',
#             'x1472425d0d9bb5ff511e132896d54b13',
#             'x2cedb5c52163c22a0b5f179001959dd2',
#             'x6223f65e553280cd25cadeac6657555c',
#             'xeae18af37c223dde92a71fef55e64afe',
#             'xb8810784ffb360cd3ffc57b1d088e537',
#         ]
#
#         keys = prefix_1_keys + prefix_2_keys
#         random.shuffle(keys)
#
#         for k in keys:
#             self.d.set(k, k)
#
#         ks = []
#
#         for k in self.d.keys():
#             ks.append(k.decode())
#
#         ks.sort()
#         keys.sort()
#
#         self.assertListEqual(keys, ks)
#
#
# class TestRocksDriver(TestCase):
#     # Flush this sucker every test
#     def setUp(self):
#         self.d = RocksDriver()
#         self.d.flush()
#
#     def tearDown(self):
#         self.d.flush()
#
#     def test_get_set(self):
#         a = 'a'
#         self.d.set('b', a)
#
#         b = self.d.get('b')
#         b = b.decode()
#         self.assertEqual(a, b)
#
#     def test_delete(self):
#         a = 'a'
#         self.d.set('b', a)
#
#         b = self.d.get('b')
#         b = b.decode()
#         self.assertEqual(a, b)
#
#         self.d.delete('b')
#
#         b = self.d.get('b')
#         self.assertIsNone(b)
#
#     def test_iter(self):
#
#         prefix_1_keys = [
#             'b77aa343e339bed781c7c2be1267cd597',
#             'bc22ede6e6fb4046d78bf2f9d1f8afdb6',
#             'b93dbb37d993846d70b8a92779cbfbfe9',
#             'be1a2783019de6ea7ef169cc55e48a3ae',
#             'b1fe8db32b9185d628f4c346f0455023e',
#             'bef918f83b6a0d1e4f980013342807cf8',
#             'b004cb9235acb5f689d20904692bc026e',
#             'b869ff9519d67354816af90867f4a5425',
#             'bcd8e9100dcb601f65e849c147e3e972e',
#             'b0111919a698f9816862b4ae662a6ed06',
#         ]
#
#         prefix_2_keys = [
#             'x37fbab0bd2e60563c79469e5be41e515',
#             'x30c6eb2ad176773b5ce6d590d2472dfe',
#             'x3d4fc9480f0a07b28aa7646d5066b54d',
#             'x387c3d4ab7f0c1c6ef549198fc14b525',
#             'x5c74dc83e132e435e8512599e1075bc0',
#             'x1472425d0d9bb5ff511e132896d54b13',
#             'x2cedb5c52163c22a0b5f179001959dd2',
#             'x6223f65e553280cd25cadeac6657555c',
#             'xeae18af37c223dde92a71fef55e64afe',
#             'xb8810784ffb360cd3ffc57b1d088e537',
#         ]
#
#         keys = prefix_1_keys + prefix_2_keys
#         random.shuffle(keys)
#
#         for k in keys:
#             self.d.set(k, k)
#
#         p1 = []
#
#         for k in self.d.iter(prefix='b'):
#             p1.append(k.decode())
#
#         prefix_1_keys.sort()
#         p1.sort()
#
#         self.assertListEqual(prefix_1_keys, p1)
#
#         p2 = []
#
#         for k in self.d.iter(prefix='x'):
#             p2.append(k.decode())
#
#         prefix_2_keys.sort()
#         p2.sort()
#
#         self.assertListEqual(prefix_2_keys, p2)
#
#     def test_keys(self):
#         prefix_1_keys = [
#             'b77aa343e339bed781c7c2be1267cd597',
#             'bc22ede6e6fb4046d78bf2f9d1f8afdb6',
#             'b93dbb37d993846d70b8a92779cbfbfe9',
#             'be1a2783019de6ea7ef169cc55e48a3ae',
#             'b1fe8db32b9185d628f4c346f0455023e',
#             'bef918f83b6a0d1e4f980013342807cf8',
#             'b004cb9235acb5f689d20904692bc026e',
#             'b869ff9519d67354816af90867f4a5425',
#             'bcd8e9100dcb601f65e849c147e3e972e',
#             'b0111919a698f9816862b4ae662a6ed06',
#         ]
#
#         prefix_2_keys = [
#             'x37fbab0bd2e60563c79469e5be41e515',
#             'x30c6eb2ad176773b5ce6d590d2472dfe',
#             'x3d4fc9480f0a07b28aa7646d5066b54d',
#             'x387c3d4ab7f0c1c6ef549198fc14b525',
#             'x5c74dc83e132e435e8512599e1075bc0',
#             'x1472425d0d9bb5ff511e132896d54b13',
#             'x2cedb5c52163c22a0b5f179001959dd2',
#             'x6223f65e553280cd25cadeac6657555c',
#             'xeae18af37c223dde92a71fef55e64afe',
#             'xb8810784ffb360cd3ffc57b1d088e537',
#         ]
#
#         keys = prefix_1_keys + prefix_2_keys
#         random.shuffle(keys)
#
#         for k in keys:
#             self.d.set(k, k)
#
#         ks = []
#
#         for k in self.d.keys():
#             ks.append(k.decode())
#
#         ks.sort()
#         keys.sort()
#
#         self.assertListEqual(keys, ks)
#
#     def test_keys_fixed_length_returns_correct_number(self):
#         prefix_1_keys = [
#             'b77aa343e339bed781c7c2be1267cd597',
#             'bc22ede6e6fb4046d78bf2f9d1f8afdb6',
#             'b93dbb37d993846d70b8a92779cbfbfe9',
#             'be1a2783019de6ea7ef169cc55e48a3ae',
#             'b1fe8db32b9185d628f4c346f0455023e',
#             'bef918f83b6a0d1e4f980013342807cf8',
#             'b004cb9235acb5f689d20904692bc026e',
#             'b869ff9519d67354816af90867f4a5425',
#             'bcd8e9100dcb601f65e849c147e3e972e',
#             'b0111919a698f9816862b4ae662a6ed06',
#         ]
#
#         prefix_2_keys = [
#             'x37fbab0bd2e60563c79469e5be41e515',
#             'x30c6eb2ad176773b5ce6d590d2472dfe',
#             'x3d4fc9480f0a07b28aa7646d5066b54d',
#             'x387c3d4ab7f0c1c6ef549198fc14b525',
#             'x5c74dc83e132e435e8512599e1075bc0',
#             'x1472425d0d9bb5ff511e132896d54b13',
#             'x2cedb5c52163c22a0b5f179001959dd2',
#             'x6223f65e553280cd25cadeac6657555c',
#             'xeae18af37c223dde92a71fef55e64afe',
#             'xb8810784ffb360cd3ffc57b1d088e537',
#         ]
#
#         keys = prefix_1_keys + prefix_2_keys
#         random.shuffle(keys)
#
#         for k in keys:
#             self.d.set(k, k)
#
#         ks = []
#
#         for k in self.d.iter('', length=5):
#             ks.append(k.decode())
#
#         ks.sort()
#         keys.sort()
#
#         self.assertListEqual(keys[:5], ks)
#
#
# class TestDBMDatabaseDriver(TestCase):
#     # Flush this sucker every test
#     def setUp(self):
#         self.d = DBMDriver(storage=1)
#         self.d.flush()
#
#     def tearDown(self):
#         self.d.flush()
#
#     def test_get_set(self):
#         a = 'a'
#         self.d.set('b', a)
#
#         b = self.d.get('b')
#         b = b.decode()
#         self.assertEqual(a, b)
#
#     def test_delete(self):
#         a = 'a'
#         self.d.set('b', a)
#
#         b = self.d.get('b')
#         b = b.decode()
#         self.assertEqual(a, b)
#
#         self.d.delete('b')
#
#         b = self.d.get('b')
#         self.assertIsNone(b)
#
#     def test_iter(self):
#
#         prefix_1_keys = [
#             'b77aa343e339bed781c7c2be1267cd597',
#             'bc22ede6e6fb4046d78bf2f9d1f8afdb6',
#             'b93dbb37d993846d70b8a92779cbfbfe9',
#             'be1a2783019de6ea7ef169cc55e48a3ae',
#             'b1fe8db32b9185d628f4c346f0455023e',
#             'bef918f83b6a0d1e4f980013342807cf8',
#             'b004cb9235acb5f689d20904692bc026e',
#             'b869ff9519d67354816af90867f4a5425',
#             'bcd8e9100dcb601f65e849c147e3e972e',
#             'b0111919a698f9816862b4ae662a6ed06',
#         ]
#
#         prefix_2_keys = [
#             'x37fbab0bd2e60563c79469e5be41e515',
#             'x30c6eb2ad176773b5ce6d590d2472dfe',
#             'x3d4fc9480f0a07b28aa7646d5066b54d',
#             'x387c3d4ab7f0c1c6ef549198fc14b525',
#             'x5c74dc83e132e435e8512599e1075bc0',
#             'x1472425d0d9bb5ff511e132896d54b13',
#             'x2cedb5c52163c22a0b5f179001959dd2',
#             'x6223f65e553280cd25cadeac6657555c',
#             'xeae18af37c223dde92a71fef55e64afe',
#             'xb8810784ffb360cd3ffc57b1d088e537',
#         ]
#
#         keys = prefix_1_keys + prefix_2_keys
#         random.shuffle(keys)
#
#         for k in keys:
#             self.d.set(k, k)
#
#         p1 = []
#
#         for k in self.d.iter(prefix='b'):
#             p1.append(k.decode())
#
#         prefix_1_keys.sort()
#         p1.sort()
#
#         self.assertListEqual(prefix_1_keys, p1)
#
#         p2 = []
#
#         for k in self.d.iter(prefix='x'):
#             p2.append(k.decode())
#
#         prefix_2_keys.sort()
#         p2.sort()
#
#         self.assertListEqual(prefix_2_keys, p2)
#
#     def test_keys(self):
#         prefix_1_keys = [
#             'b77aa343e339bed781c7c2be1267cd597',
#             'bc22ede6e6fb4046d78bf2f9d1f8afdb6',
#             'b93dbb37d993846d70b8a92779cbfbfe9',
#             'be1a2783019de6ea7ef169cc55e48a3ae',
#             'b1fe8db32b9185d628f4c346f0455023e',
#             'bef918f83b6a0d1e4f980013342807cf8',
#             'b004cb9235acb5f689d20904692bc026e',
#             'b869ff9519d67354816af90867f4a5425',
#             'bcd8e9100dcb601f65e849c147e3e972e',
#             'b0111919a698f9816862b4ae662a6ed06',
#         ]
#
#         prefix_2_keys = [
#             'x37fbab0bd2e60563c79469e5be41e515',
#             'x30c6eb2ad176773b5ce6d590d2472dfe',
#             'x3d4fc9480f0a07b28aa7646d5066b54d',
#             'x387c3d4ab7f0c1c6ef549198fc14b525',
#             'x5c74dc83e132e435e8512599e1075bc0',
#             'x1472425d0d9bb5ff511e132896d54b13',
#             'x2cedb5c52163c22a0b5f179001959dd2',
#             'x6223f65e553280cd25cadeac6657555c',
#             'xeae18af37c223dde92a71fef55e64afe',
#             'xb8810784ffb360cd3ffc57b1d088e537',
#         ]
#
#         keys = prefix_1_keys + prefix_2_keys
#         random.shuffle(keys)
#
#         for k in keys:
#             self.d.set(k, k)
#
#         ks = []
#
#         for k in self.d.keys():
#             ks.append(k.decode())
#
#         ks.sort()
#         keys.sort()
#
#         self.assertListEqual(keys, ks)
#
#
# class TestContractDriver(TestCase):
#     # Flush this sucker every test
#     def setUp(self):
#         self.d = ContractDriver(storage=1)
#         self.d.flush()
#
#     def tearDown(self):
#         self.d.flush()
#
#     def test_make_key(self):
#         contract = 'token.balances'
#
#         name = 'token'
#         func = 'balances'
#
#         self.assertEqual(contract, self.d.make_key(name, func))
#
#     def test_hget_hset(self):
#         name = 'token'
#         func = 'balances'
#         million = 1_000_000
#
#         self.d.hset(name, func, million)
#
#         m = self.d.hget(name, func)
#
#         self.assertEqual(million, m)
#
#     def test_get_set_contract(self):
#         contract = '''
# def stu():
#     print('howdy partner')
# '''
#
#         name = 'stustu'
#         _t = 'test'
#
#         self.d.set_contract(name, contract)
#
#         self.assertEqual(self.d.get_contract(name), contract)
#
#     def test_get_contract_keys(self):
#         contract = '''
# def stu():
#     print('howdy partner')
# '''
#
#         name = 'stustu'
#         _t = 'test'
#
#         self.d.set_contract(name, contract)
#
#         keys = [
#             '{}{}{}'.format(name, self.d.delimiter, config.CODE_KEY),
#             '{}{}{}'.format(name, self.d.delimiter, '__compiled__'),
#             '{}{}{}'.format(name, self.d.delimiter, config.TIME_KEY)
#         ]
#
#         self.d.commit()
#
#         k = self.d.get_contract_keys(name)
#
#         keys.sort()
#         k.sort()
#
#         self.assertListEqual(keys, k)
#
#     def test_delete_contract(self):
#             contract = '''
# def stu():
#     print('howdy partner')
# '''
#
#             name = 'stustu'
#             _t = 'test'
#
#             self.d.set_contract(name, contract)
#
#             self.d.commit()
#
#             self.d.delete_contract(name)
#
#             self.d.commit()
#
#             self.assertIsNone(self.d.get_contract(name))
#
#     def test_is_contract_no(self):
#         self.assertFalse(self.d.is_contract('stustu'))
#
#     def test_is_contract_yes(self):
#         contract = '''
# def stu():
#     print('howdy partner')
# '''
#
#         name = 'stustu'
#         _t = 'test'
#
#         self.d.set_contract(name, contract)
#         self.d.commit()
#         self.assertTrue(self.d.is_contract('stustu'))