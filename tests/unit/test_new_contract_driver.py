from unittest import TestCase
from contracting.db.driver import ContractDriver, Driver
from contracting.stdlib.bridge.time import Datetime

import marshal
from datetime import datetime


class TestContractDriver(TestCase):
    def setUp(self):
        self.d = Driver()
        self.d.flush()

        self.c = ContractDriver(self.d)
        self.c.flush_cache()

    def test_values_returns_values_for_keys(self):
        kvs = [('899af0b15aa0f227e658c96a24fa890e', 'ece22e0f19e822908b136e391d488ba5'),
               ('fd556e848073c754c48f07c96b460f42', '09af42359ef2be582203259e4919ce46'),
               ('7cf326d5efaf6699a4910960448ea9d2', '4c591f2e61097ba70da20abbf06e6bb2'),
               ('c481cc9f36576211e53a1c1b46d11fb8', '040cd915a382c169a24a12d843bb4cf4'),
               ('1f43b3c044dae3f3e32d89ed92285bf0', '38739b29fd4ee6cd7e27c69cc7832dd8'),
               ('6dab790f8c8e710f18e7c37417050bef', '2e28e7ebca069c4c577fd187b2f10a4d'),
               ('8a60834e92a513caa8282528d353e856', '6222c85f25d1a07dd58675ebba399dfb'),
               ('e04fdc0f3e7fb72c15de97e8500de314', '67fcb589f5f164019f395baa41864f94'),
               ('0691ccd1ee4d60e32e030a51a7751695', 'a3c9e2b7e08ca31ae0d06369c966f405'),
               ('5bf713c0713a3a1e24e7620fe884164e', '8690981810a100d80132fd22c63b6c15'),
               ('e42885e2af741c1d0008435809cdef34', 'f7f404a61f615b748fa0df6727769387'),
               ('77276db2ade4828775d182bb07a4351e', 'dedc6d5869b85a8e6f83b7aaf62be896'),
               ('e433b42847cc35091467a1accae2d6da', 'd7084251eddafadf1aeaf98fdee2a67a'),
               ('f420ccf1f0fd1b7342346f04342e50a8', 'd7bfc0c6cd62ac769e406911cd6c4be7'),
               ('163317155517d347c414a6085903588e', '40af65a30356375ee64a5459c99905f9'),
               ('16c380229f60017ae6f96b352e01e1c4', '87f66f3113f9f75c231aacfa8c6821cd'),
               ('c38f9c34ac9a5823df15c89da27a3b38', '5dad274ed444fb0b8b4dcd5747b65219'),
               ('f48123a394da4ba71a5555bd15f152b5', '51cbdc1c76e0202c3f4cbc84039c9cce'),
               ('7da2edaf903f6ca547f982b3eebfc7c4', '5c8f4644b207a87c6b5a22b04acaf9ee'),
               ('f2e46a3d29b934c8ef4fbedfbb6a825b', '2bb489bdad3155095c4c5b873744a3d5')
               ]

        for kv in kvs:
            self.c.set(kv[0], kv[1])

        vs = self.c.values()
        vs.sort()

        expected = [kv[1] for kv in kvs]
        expected.sort()

        self.assertListEqual(vs, expected)

    def test_items_only_in_cache_works(self):
        kvs = {'899af0b15aa0f227e658c96a24fa890e': 'ece22e0f19e822908b136e391d488ba5',
               'fd556e848073c754c48f07c96b460f42': '09af42359ef2be582203259e4919ce46',
               '7cf326d5efaf6699a4910960448ea9d2': '4c591f2e61097ba70da20abbf06e6bb2',
               'c481cc9f36576211e53a1c1b46d11fb8': '040cd915a382c169a24a12d843bb4cf4',
               '1f43b3c044dae3f3e32d89ed92285bf0': '38739b29fd4ee6cd7e27c69cc7832dd8',
               '6dab790f8c8e710f18e7c37417050bef': '2e28e7ebca069c4c577fd187b2f10a4d',
               '8a60834e92a513caa8282528d353e856': '6222c85f25d1a07dd58675ebba399dfb',
               'e04fdc0f3e7fb72c15de97e8500de314': '67fcb589f5f164019f395baa41864f94',
               '0691ccd1ee4d60e32e030a51a7751695': 'a3c9e2b7e08ca31ae0d06369c966f405',
               '5bf713c0713a3a1e24e7620fe884164e': '8690981810a100d80132fd22c63b6c15',
               'e42885e2af741c1d0008435809cdef34': 'f7f404a61f615b748fa0df6727769387',
               '77276db2ade4828775d182bb07a4351e': 'dedc6d5869b85a8e6f83b7aaf62be896',
               'e433b42847cc35091467a1accae2d6da': 'd7084251eddafadf1aeaf98fdee2a67a',
               'f420ccf1f0fd1b7342346f04342e50a8': 'd7bfc0c6cd62ac769e406911cd6c4be7',
               '163317155517d347c414a6085903588e': '40af65a30356375ee64a5459c99905f9',
               '16c380229f60017ae6f96b352e01e1c4': '87f66f3113f9f75c231aacfa8c6821cd',
               'c38f9c34ac9a5823df15c89da27a3b38': '5dad274ed444fb0b8b4dcd5747b65219',
               'f48123a394da4ba71a5555bd15f152b5': '51cbdc1c76e0202c3f4cbc84039c9cce',
               '7da2edaf903f6ca547f982b3eebfc7c4': '5c8f4644b207a87c6b5a22b04acaf9ee',
               'f2e46a3d29b934c8ef4fbedfbb6a825b': '2bb489bdad3155095c4c5b873744a3d5'}

        for k, v in kvs.items():
            self.c.set(k, v)

        items = self.c.items()
        self.assertDictEqual(items, kvs)

    def test_items_only_in_db_works(self):
        kvs = {'899af0b15aa0f227e658c96a24fa890e': 'ece22e0f19e822908b136e391d488ba5',
               'fd556e848073c754c48f07c96b460f42': '09af42359ef2be582203259e4919ce46',
               '7cf326d5efaf6699a4910960448ea9d2': '4c591f2e61097ba70da20abbf06e6bb2',
               'c481cc9f36576211e53a1c1b46d11fb8': '040cd915a382c169a24a12d843bb4cf4',
               '1f43b3c044dae3f3e32d89ed92285bf0': '38739b29fd4ee6cd7e27c69cc7832dd8',
               '6dab790f8c8e710f18e7c37417050bef': '2e28e7ebca069c4c577fd187b2f10a4d',
               '8a60834e92a513caa8282528d353e856': '6222c85f25d1a07dd58675ebba399dfb',
               'e04fdc0f3e7fb72c15de97e8500de314': '67fcb589f5f164019f395baa41864f94',
               '0691ccd1ee4d60e32e030a51a7751695': 'a3c9e2b7e08ca31ae0d06369c966f405',
               '5bf713c0713a3a1e24e7620fe884164e': '8690981810a100d80132fd22c63b6c15',
               'e42885e2af741c1d0008435809cdef34': 'f7f404a61f615b748fa0df6727769387',
               '77276db2ade4828775d182bb07a4351e': 'dedc6d5869b85a8e6f83b7aaf62be896',
               'e433b42847cc35091467a1accae2d6da': 'd7084251eddafadf1aeaf98fdee2a67a',
               'f420ccf1f0fd1b7342346f04342e50a8': 'd7bfc0c6cd62ac769e406911cd6c4be7',
               '163317155517d347c414a6085903588e': '40af65a30356375ee64a5459c99905f9',
               '16c380229f60017ae6f96b352e01e1c4': '87f66f3113f9f75c231aacfa8c6821cd',
               'c38f9c34ac9a5823df15c89da27a3b38': '5dad274ed444fb0b8b4dcd5747b65219',
               'f48123a394da4ba71a5555bd15f152b5': '51cbdc1c76e0202c3f4cbc84039c9cce',
               '7da2edaf903f6ca547f982b3eebfc7c4': '5c8f4644b207a87c6b5a22b04acaf9ee',
               'f2e46a3d29b934c8ef4fbedfbb6a825b': '2bb489bdad3155095c4c5b873744a3d5'}

        for k, v in kvs.items():
            self.c.driver.set(k, v)

        items = self.c.items()
        self.assertDictEqual(items, kvs)

    def test_items_in_both_cache_and_db_works(self):
        kvs_1 = {'899af0b15aa0f227e658c96a24fa890e': 'ece22e0f19e822908b136e391d488ba5',
                 'fd556e848073c754c48f07c96b460f42': '09af42359ef2be582203259e4919ce46',
                 '7cf326d5efaf6699a4910960448ea9d2': '4c591f2e61097ba70da20abbf06e6bb2',
                 'c481cc9f36576211e53a1c1b46d11fb8': '040cd915a382c169a24a12d843bb4cf4',
                 '1f43b3c044dae3f3e32d89ed92285bf0': '38739b29fd4ee6cd7e27c69cc7832dd8',
                 '6dab790f8c8e710f18e7c37417050bef': '2e28e7ebca069c4c577fd187b2f10a4d',
                 '8a60834e92a513caa8282528d353e856': '6222c85f25d1a07dd58675ebba399dfb',
                 'e04fdc0f3e7fb72c15de97e8500de314': '67fcb589f5f164019f395baa41864f94',
                 '0691ccd1ee4d60e32e030a51a7751695': 'a3c9e2b7e08ca31ae0d06369c966f405',
                 '5bf713c0713a3a1e24e7620fe884164e': '8690981810a100d80132fd22c63b6c15',
                 'e42885e2af741c1d0008435809cdef34': 'f7f404a61f615b748fa0df6727769387'}

        kvs_2 = {'77276db2ade4828775d182bb07a4351e': 'dedc6d5869b85a8e6f83b7aaf62be896',
                 'e433b42847cc35091467a1accae2d6da': 'd7084251eddafadf1aeaf98fdee2a67a',
                 'f420ccf1f0fd1b7342346f04342e50a8': 'd7bfc0c6cd62ac769e406911cd6c4be7',
                 '163317155517d347c414a6085903588e': '40af65a30356375ee64a5459c99905f9',
                 '16c380229f60017ae6f96b352e01e1c4': '87f66f3113f9f75c231aacfa8c6821cd',
                 'c38f9c34ac9a5823df15c89da27a3b38': '5dad274ed444fb0b8b4dcd5747b65219',
                 'f48123a394da4ba71a5555bd15f152b5': '51cbdc1c76e0202c3f4cbc84039c9cce',
                 '7da2edaf903f6ca547f982b3eebfc7c4': '5c8f4644b207a87c6b5a22b04acaf9ee',
                 'f2e46a3d29b934c8ef4fbedfbb6a825b': '2bb489bdad3155095c4c5b873744a3d5'}

        for k, v in kvs_1.items():
            self.c.set(k, v)

        self.c.commit()

        for k, v in kvs_2.items():
            self.c.driver.set(k, v)

        kvs = {'899af0b15aa0f227e658c96a24fa890e': 'ece22e0f19e822908b136e391d488ba5',
               'fd556e848073c754c48f07c96b460f42': '09af42359ef2be582203259e4919ce46',
               '7cf326d5efaf6699a4910960448ea9d2': '4c591f2e61097ba70da20abbf06e6bb2',
               'c481cc9f36576211e53a1c1b46d11fb8': '040cd915a382c169a24a12d843bb4cf4',
               '1f43b3c044dae3f3e32d89ed92285bf0': '38739b29fd4ee6cd7e27c69cc7832dd8',
               '6dab790f8c8e710f18e7c37417050bef': '2e28e7ebca069c4c577fd187b2f10a4d',
               '8a60834e92a513caa8282528d353e856': '6222c85f25d1a07dd58675ebba399dfb',
               'e04fdc0f3e7fb72c15de97e8500de314': '67fcb589f5f164019f395baa41864f94',
               '0691ccd1ee4d60e32e030a51a7751695': 'a3c9e2b7e08ca31ae0d06369c966f405',
               '5bf713c0713a3a1e24e7620fe884164e': '8690981810a100d80132fd22c63b6c15',
               'e42885e2af741c1d0008435809cdef34': 'f7f404a61f615b748fa0df6727769387',
               '77276db2ade4828775d182bb07a4351e': 'dedc6d5869b85a8e6f83b7aaf62be896',
               'e433b42847cc35091467a1accae2d6da': 'd7084251eddafadf1aeaf98fdee2a67a',
               'f420ccf1f0fd1b7342346f04342e50a8': 'd7bfc0c6cd62ac769e406911cd6c4be7',
               '163317155517d347c414a6085903588e': '40af65a30356375ee64a5459c99905f9',
               '16c380229f60017ae6f96b352e01e1c4': '87f66f3113f9f75c231aacfa8c6821cd',
               'c38f9c34ac9a5823df15c89da27a3b38': '5dad274ed444fb0b8b4dcd5747b65219',
               'f48123a394da4ba71a5555bd15f152b5': '51cbdc1c76e0202c3f4cbc84039c9cce',
               '7da2edaf903f6ca547f982b3eebfc7c4': '5c8f4644b207a87c6b5a22b04acaf9ee',
               'f2e46a3d29b934c8ef4fbedfbb6a825b': '2bb489bdad3155095c4c5b873744a3d5'}

        items = self.c.items()
        self.assertDictEqual(items, kvs)

    def test_items_prefix_in_cache(self):
        kvs_1 = {
            'pref1_899af0b15aa0f227e658c96a24fa890e': 'ece22e0f19e822908b136e391d488ba5',
            'pref1_fd556e848073c754c48f07c96b460f42': '09af42359ef2be582203259e4919ce46',
            'pref1_7cf326d5efaf6699a4910960448ea9d2': '4c591f2e61097ba70da20abbf06e6bb2',
            'pref1_c481cc9f36576211e53a1c1b46d11fb8': '040cd915a382c169a24a12d843bb4cf4',
            'pref1_1f43b3c044dae3f3e32d89ed92285bf0': '38739b29fd4ee6cd7e27c69cc7832dd8',
            'pref1_6dab790f8c8e710f18e7c37417050bef': '2e28e7ebca069c4c577fd187b2f10a4d',
            'pref1_8a60834e92a513caa8282528d353e856': '6222c85f25d1a07dd58675ebba399dfb',
            'pref1_e04fdc0f3e7fb72c15de97e8500de314': '67fcb589f5f164019f395baa41864f94',
            'pref1_0691ccd1ee4d60e32e030a51a7751695': 'a3c9e2b7e08ca31ae0d06369c966f405',
            'pref1_5bf713c0713a3a1e24e7620fe884164e': '8690981810a100d80132fd22c63b6c15',
            'pref1_e42885e2af741c1d0008435809cdef34': 'f7f404a61f615b748fa0df6727769387'
        }

        kvs_2 = {
            'pref2_77276db2ade4828775d182bb07a4351e': 'dedc6d5869b85a8e6f83b7aaf62be896',
            'pref2_e433b42847cc35091467a1accae2d6da': 'd7084251eddafadf1aeaf98fdee2a67a',
            'pref2_f420ccf1f0fd1b7342346f04342e50a8': 'd7bfc0c6cd62ac769e406911cd6c4be7',
            'pref2_163317155517d347c414a6085903588e': '40af65a30356375ee64a5459c99905f9',
            'pref2_16c380229f60017ae6f96b352e01e1c4': '87f66f3113f9f75c231aacfa8c6821cd',
            'pref2_c38f9c34ac9a5823df15c89da27a3b38': '5dad274ed444fb0b8b4dcd5747b65219',
            'pref2_f48123a394da4ba71a5555bd15f152b5': '51cbdc1c76e0202c3f4cbc84039c9cce',
            'pref2_7da2edaf903f6ca547f982b3eebfc7c4': '5c8f4644b207a87c6b5a22b04acaf9ee',
            'pref2_f2e46a3d29b934c8ef4fbedfbb6a825b': '2bb489bdad3155095c4c5b873744a3d5'
        }

        for k, v in kvs_1.items():
            self.c.set(k, v)

        for k, v in kvs_2.items():
            self.c.set(k, v)

        items = self.c.items('pref1_')
        self.assertDictEqual(items, kvs_1)

    def test_items_prefix_in_db(self):
        kvs_1 = {
            'pref1_899af0b15aa0f227e658c96a24fa890e': 'ece22e0f19e822908b136e391d488ba5',
            'pref1_fd556e848073c754c48f07c96b460f42': '09af42359ef2be582203259e4919ce46',
            'pref1_7cf326d5efaf6699a4910960448ea9d2': '4c591f2e61097ba70da20abbf06e6bb2',
            'pref1_c481cc9f36576211e53a1c1b46d11fb8': '040cd915a382c169a24a12d843bb4cf4',
            'pref1_1f43b3c044dae3f3e32d89ed92285bf0': '38739b29fd4ee6cd7e27c69cc7832dd8',
            'pref1_6dab790f8c8e710f18e7c37417050bef': '2e28e7ebca069c4c577fd187b2f10a4d',
            'pref1_8a60834e92a513caa8282528d353e856': '6222c85f25d1a07dd58675ebba399dfb',
            'pref1_e04fdc0f3e7fb72c15de97e8500de314': '67fcb589f5f164019f395baa41864f94',
            'pref1_0691ccd1ee4d60e32e030a51a7751695': 'a3c9e2b7e08ca31ae0d06369c966f405',
            'pref1_5bf713c0713a3a1e24e7620fe884164e': '8690981810a100d80132fd22c63b6c15',
            'pref1_e42885e2af741c1d0008435809cdef34': 'f7f404a61f615b748fa0df6727769387'
        }

        kvs_2 = {
            'pref2_77276db2ade4828775d182bb07a4351e': 'dedc6d5869b85a8e6f83b7aaf62be896',
            'pref2_e433b42847cc35091467a1accae2d6da': 'd7084251eddafadf1aeaf98fdee2a67a',
            'pref2_f420ccf1f0fd1b7342346f04342e50a8': 'd7bfc0c6cd62ac769e406911cd6c4be7',
            'pref2_163317155517d347c414a6085903588e': '40af65a30356375ee64a5459c99905f9',
            'pref2_16c380229f60017ae6f96b352e01e1c4': '87f66f3113f9f75c231aacfa8c6821cd',
            'pref2_c38f9c34ac9a5823df15c89da27a3b38': '5dad274ed444fb0b8b4dcd5747b65219',
            'pref2_f48123a394da4ba71a5555bd15f152b5': '51cbdc1c76e0202c3f4cbc84039c9cce',
            'pref2_7da2edaf903f6ca547f982b3eebfc7c4': '5c8f4644b207a87c6b5a22b04acaf9ee',
            'pref2_f2e46a3d29b934c8ef4fbedfbb6a825b': '2bb489bdad3155095c4c5b873744a3d5'
        }

        for k, v in kvs_1.items():
            self.c.driver.set(k, v)

        for k, v in kvs_2.items():
            self.c.driver.set(k, v)

        items = self.c.items('pref2_')
        self.assertDictEqual(items, kvs_2)

    def test_items_prefix_mix(self):
        kvs_1 = {
            'pref1_899af0b15aa0f227e658c96a24fa890e': 'ece22e0f19e822908b136e391d488ba5',
            'pref1_fd556e848073c754c48f07c96b460f42': '09af42359ef2be582203259e4919ce46',
            'pref1_7cf326d5efaf6699a4910960448ea9d2': '4c591f2e61097ba70da20abbf06e6bb2',
            'pref1_c481cc9f36576211e53a1c1b46d11fb8': '040cd915a382c169a24a12d843bb4cf4',
            'pref1_1f43b3c044dae3f3e32d89ed92285bf0': '38739b29fd4ee6cd7e27c69cc7832dd8',
        }

        kvs_2 = {
            'pref2_77276db2ade4828775d182bb07a4351e': 'dedc6d5869b85a8e6f83b7aaf62be896',
            'pref2_e433b42847cc35091467a1accae2d6da': 'd7084251eddafadf1aeaf98fdee2a67a',
            'pref2_f420ccf1f0fd1b7342346f04342e50a8': 'd7bfc0c6cd62ac769e406911cd6c4be7',
            'pref2_163317155517d347c414a6085903588e': '40af65a30356375ee64a5459c99905f9',
            'pref2_16c380229f60017ae6f96b352e01e1c4': '87f66f3113f9f75c231aacfa8c6821cd',
        }

        for k, v in kvs_1.items():
            self.c.driver.set(k, v)

        for k, v in kvs_2.items():
            self.c.driver.set(k, v)

        kvs_3 = {
            'pref1_6dab790f8c8e710f18e7c37417050bef': '2e28e7ebca069c4c577fd187b2f10a4d',
            'pref1_8a60834e92a513caa8282528d353e856': '6222c85f25d1a07dd58675ebba399dfb',
            'pref1_e04fdc0f3e7fb72c15de97e8500de314': '67fcb589f5f164019f395baa41864f94',
            'pref1_0691ccd1ee4d60e32e030a51a7751695': 'a3c9e2b7e08ca31ae0d06369c966f405',
            'pref1_5bf713c0713a3a1e24e7620fe884164e': '8690981810a100d80132fd22c63b6c15',
            'pref1_e42885e2af741c1d0008435809cdef34': 'f7f404a61f615b748fa0df6727769387'
        }

        kvs_4 = {
            'pref2_c38f9c34ac9a5823df15c89da27a3b38': '5dad274ed444fb0b8b4dcd5747b65219',
            'pref2_f48123a394da4ba71a5555bd15f152b5': '51cbdc1c76e0202c3f4cbc84039c9cce',
            'pref2_7da2edaf903f6ca547f982b3eebfc7c4': '5c8f4644b207a87c6b5a22b04acaf9ee',
            'pref2_f2e46a3d29b934c8ef4fbedfbb6a825b': '2bb489bdad3155095c4c5b873744a3d5'
        }

        for k, v in kvs_3.items():
            self.c.set(k, v)

        for k, v in kvs_4.items():
            self.c.set(k, v)

        kvs_2.update(kvs_4)

        items = self.c.items('pref2_')

        self.assertDictEqual(items, kvs_2)

    def test_make_key_no_args(self):
        c = 'stubucks'
        v = 'balances'

        expected = 'stubucks.balances'

        self.assertEqual(self.c.make_key(c, v), expected)

    def test_make_key_args(self):
        c = 'stubucks'
        v = 'balances'
        a = ['1', '2', '3']

        expected = 'stubucks.balances:1:2:3'

        self.assertEqual(self.c.make_key(c, v, a), expected)

    def test_get_var(self):
        self.c.set('stubucks.balances', 123)

        self.assertEqual(self.c.get_var('stubucks', 'balances'), 123)

    def test_set_var(self):
        self.c.set_var('stubucks', 'balances', value=123)
        self.assertEqual(self.c.get_var('stubucks', 'balances'), 123)

    def test_get_multi_hash_var(self):
        self.c.set_var('stubucks', 'balances', ['1', '2', '3'], value=123)
        self.assertEqual(self.c.get_var('stubucks', 'balances', ['1', '2', '3']), 123)

    def test_get_keys(self):
        kvs_1 = {
            'pref1_899af0b15aa0f227e658c96a24fa890e': 'ece22e0f19e822908b136e391d488ba5',
            'pref1_fd556e848073c754c48f07c96b460f42': '09af42359ef2be582203259e4919ce46',
            'pref1_7cf326d5efaf6699a4910960448ea9d2': '4c591f2e61097ba70da20abbf06e6bb2',
            'pref1_c481cc9f36576211e53a1c1b46d11fb8': '040cd915a382c169a24a12d843bb4cf4',
            'pref1_1f43b3c044dae3f3e32d89ed92285bf0': '38739b29fd4ee6cd7e27c69cc7832dd8',
        }

        kvs_2 = {
            'pref2_77276db2ade4828775d182bb07a4351e': 'dedc6d5869b85a8e6f83b7aaf62be896',
            'pref2_e433b42847cc35091467a1accae2d6da': 'd7084251eddafadf1aeaf98fdee2a67a',
            'pref2_f420ccf1f0fd1b7342346f04342e50a8': 'd7bfc0c6cd62ac769e406911cd6c4be7',
            'pref2_163317155517d347c414a6085903588e': '40af65a30356375ee64a5459c99905f9',
            'pref2_16c380229f60017ae6f96b352e01e1c4': '87f66f3113f9f75c231aacfa8c6821cd',
        }

        for k, v in kvs_1.items():
            self.c.driver.set(k, v)

        for k, v in kvs_2.items():
            self.c.driver.set(k, v)

        kvs_3 = {
            'pref1_6dab790f8c8e710f18e7c37417050bef': '2e28e7ebca069c4c577fd187b2f10a4d',
            'pref1_8a60834e92a513caa8282528d353e856': '6222c85f25d1a07dd58675ebba399dfb',
            'pref1_e04fdc0f3e7fb72c15de97e8500de314': '67fcb589f5f164019f395baa41864f94',
            'pref1_0691ccd1ee4d60e32e030a51a7751695': 'a3c9e2b7e08ca31ae0d06369c966f405',
            'pref1_5bf713c0713a3a1e24e7620fe884164e': '8690981810a100d80132fd22c63b6c15',
            'pref1_e42885e2af741c1d0008435809cdef34': 'f7f404a61f615b748fa0df6727769387'
        }

        kvs_4 = {
            'pref2_c38f9c34ac9a5823df15c89da27a3b38': '5dad274ed444fb0b8b4dcd5747b65219',
            'pref2_f48123a394da4ba71a5555bd15f152b5': '51cbdc1c76e0202c3f4cbc84039c9cce',
            'pref2_7da2edaf903f6ca547f982b3eebfc7c4': '5c8f4644b207a87c6b5a22b04acaf9ee',
            'pref2_f2e46a3d29b934c8ef4fbedfbb6a825b': '2bb489bdad3155095c4c5b873744a3d5'
        }

        for k, v in kvs_3.items():
            self.c.set(k, v)

        for k, v in kvs_4.items():
            self.c.set(k, v)

        kvs_2.update(kvs_4)

        keys = self.c.keys('pref2_')
        keys.sort()

        expected = list(kvs_2.keys())
        expected.sort()

        self.assertListEqual(keys, expected)

    def test_set_contract(self):
        code = '''
print('hello, world!')
        '''

        time = Datetime._from_datetime(datetime.now())

        self.c.set_contract(name='test', code=code, owner='something', timestamp=time)

        code_obj = compile(code, '', 'exec')
        code_blob = marshal.dumps(code_obj)

        self.assertEqual(self.c.get_contract('test'), code)
        self.assertEqual(self.c.get_compiled('test'), code_blob)
        self.assertEqual(self.c.get_owner('test'), 'something')
        self.assertEqual(self.c.get_time_submitted('test'), time)

