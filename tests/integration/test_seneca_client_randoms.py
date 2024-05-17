from unittest import TestCase
from contracting.client import ContractingClient
import random

def con_random_contract():
    random.seed()

    cards = [1, 2, 3, 4, 5, 6, 7, 8]

    cardinal_values = ['A', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    suits = ['S', 'C', 'H', 'D']

    cities = ['Cleveland', 'Detroit', 'Chicago', 'New York', 'San Francisco']

    @export
    def shuffle_cards(**kwargs: dict):
        random.shuffle(cards)
        return cards

    @export
    def random_number(k: int):
        return random.randrange(k)

    @export
    def random_number_2(k: int):
        # adjust the random state by calling another random function
        shuffle_cards()
        return random.randrange(k)

    @export
    def random_bits(k: int):
        shuffle_cards()
        shuffle_cards()
        shuffle_cards()
        return random.getrandbits(k)

    @export
    def int_in_range(a: int, b: int):
        shuffle_cards()
        shuffle_cards()
        return random.randint(a, b)

    @export
    def deal_card():
        random.shuffle(cardinal_values)
        random.shuffle(cardinal_values)
        random.shuffle(cardinal_values)

        random.shuffle(suits)
        random.shuffle(suits)
        random.shuffle(suits)

        c = ''
        c += random.choice(cardinal_values)
        c += random.choice(suits)

        return c

    @export
    def pick_cities(k: int):
        return random.choices(cities, k)


class TestRandomsContract(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.flush()
        self.c.submit(con_random_contract)

        self.random_contract = self.c.get_contract('con_random_contract')

    def tearDown(self):
        self.c.flush()

    def test_basic_shuffle(self):
        cards_1 = self.random_contract.shuffle_cards()
        cards_2 = self.random_contract.shuffle_cards()

        self.assertEqual(cards_1, cards_2)

    def test_basic_shuffle_different_with_different_seeds(self):
        cards_1 = self.random_contract.shuffle_cards(environment={'block_num': 999})
        cards_2 = self.random_contract.shuffle_cards(environment={'block_num': 998})

        self.assertNotEqual(cards_1, cards_2)

    def test_random_num_one_vs_two(self):
        k = self.random_contract.random_number(k=1000)
        k2 = self.random_contract.random_number_2(k=1000)

        self.assertNotEqual(k, k2)

        random.seed('000')

        self.assertEqual(k, random.randrange(1000))

        random.seed('000')
        cards = [1, 2, 3, 4, 5, 6, 7, 8]
        random.shuffle(cards)

        self.assertEqual(k2, random.randrange(1000))
    '''' TEST CASE IS IRRELEVANT as getrandbits will never sync with system random.
    def test_random_getrandbits(self):
        b = self.random_contract.random_bits(k=20)

        random.seed('000')

        cards = [1, 2, 3, 4, 5, 6, 7, 8]
        random.shuffle(cards)
        random.shuffle(cards)
        random.shuffle(cards)

        self.assertEqual(b, random.getrandbits(20))
    '''

    def test_random_range_int(self):
        a = self.random_contract.int_in_range(a=100, b=50000)

        random.seed('000')

        cards = [1, 2, 3, 4, 5, 6, 7, 8]
        random.shuffle(cards)
        random.shuffle(cards)

        self.assertEqual(a, random.randint(a=100, b=50000))

    def test_random_choice(self):
        cities = self.random_contract.pick_cities(k=2)

        random.seed('000')
        c = ['Cleveland', 'Detroit', 'Chicago', 'New York', 'San Francisco']
        cc = random.choices(c, k=2)

        self.assertListEqual(cities, cc)

    def test_auxiliary_salt(self):
        cards_1 = self.random_contract.shuffle_cards(environment={
            'AUXILIARY_SALT': 'ffd8ded9ced929a41dae83b1f22a6a31b52f79bbf4cdabe6a27d9646dd2bd725fc29c8bc122cb9e37a2904da00e34df499ee7a897505d1de3f0511f9f9c1150c'})
        cards_2 = self.random_contract.shuffle_cards(environment={
            'AUXILIARY_SALT': 'ffd8ded9ced929a41dae83b1f22a6a31b52f79bbf4cdabe6a27d9646dd2bd725fc29c8bc122cb9e37a2904da00e34df499ee7a897505d1de3f0511f9f9c1150c'})
        cards_3 = self.random_contract.shuffle_cards(environment={
            'AUXILIARY_SALT': 'f79bbded9ced929a41dae83b1f22a6a31b52f79bbf4cdabe6a27d9646dd2bd725fc29c8bc122cb9e37a2904da00e34df499ee7a897505d1de3f0511f9f9c1150c'})

        self.assertEqual(cards_1, cards_2)
        self.assertNotEqual(cards_1, cards_3)