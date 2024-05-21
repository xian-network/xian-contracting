from contracting.client import ContractingClient
from unittest import TestCase


def con_coin():
    supply = Variable()
    balances = Hash(default_value=0)
    owner = Variable()

    @construct
    def seed():
        balances[ctx.caller] = 1000000
        owner.set(ctx.caller)
        supply.set(1000000)

    @export
    def transfer(amount: int, to: str):
        sender = ctx.caller
        assert balances[sender] >= amount, 'Not enough coins to send!'

        balances[sender] -= amount
        balances[to] += amount

    @export
    def balance_of(account: str):
        return balances[account]

    @export
    def total_supply():
        return supply.get()

    @export
    def allowance(main: str, spender: str):
        return balances[main, spender]

    @export
    def approve(amount: int, to: str):
        sender = ctx.caller
        balances[sender, to] += amount
        return balances[sender, to]

    @export
    def transfer_from(amount: int, to: str, main_account: str):
        sender = ctx.caller

        assert balances[main_account, sender] >= amount, 'Not enough coins approved to send! You have {} and are trying to spend {}'\
            .format(balances[main_account, sender], amount)
        assert balances[main_account] >= amount, 'Not enough coins to send!'

        balances[main_account, sender] -= amount
        balances[main_account] -= amount

        balances[to] += amount

    @export
    def mint(amount: int, to: str):
        assert ctx.caller == owner.get(), 'Only the owner can mint!'

        balances[to] += amount

        s = supply.get()
        supply.set(s + amount)

    @export
    def change_ownership(new_owner: str):
        assert ctx.caller == owner.get(), 'Only the owner can change ownership!'

        owner.set(new_owner)


class TestCoinContract(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.flush()

        self.c.submit(con_coin)
        self.coin = self.c.get_contract('con_coin')

    def tearDown(self):
        self.c.flush()

    def test_coin_construction(self):
        self.assertEqual(self.coin.balances['stu'], 1000000)

    def test_transfer_not_enough(self):
        with self.assertRaises(AssertionError):
            self.coin.transfer(amount=9999999, to='raghu')

    def test_transfer_enough(self):
        self.coin.transfer(amount=123, to='raghu')
        self.assertEqual(self.coin.balances['raghu'], 123)

    def test_balance_of_works(self):
        self.coin.transfer(amount=123, to='raghu')
        self.assertEqual(self.coin.balance_of(account='raghu'), 123)

    def test_total_supply_pre_mint(self):
        self.assertEqual(self.coin.total_supply(), 1000000)
        self.assertEqual(self.coin.supply.get(), 1000000)

    def test_approve_modified_balances(self):
        self.coin.approve(amount=100, to='raghu')
        self.assertEqual(self.coin.balances['stu', 'raghu'], 100)

    def test_allowance_returns_approve(self):
        self.coin.approve(amount=100, to='raghu')
        self.assertEqual(self.coin.allowance(main='stu', spender='raghu'), 100)

    def test_transfer_from_failure_not_enough_allowance(self):
        self.coin.approve(amount=100, to='raghu')
        with self.assertRaises(AssertionError):
            self.coin.transfer_from(amount=101, to='colin', main_account='stu', signer='raghu')

    def test_transfer_from_failure_not_enough_in_main_account(self):
        self.coin.approve(amount=1000000000, to='raghu')
        with self.assertRaises(AssertionError):
            self.coin.transfer_from(amount=1000000000, to='colin', main_account='stu', signer='raghu')

    def test_transfer_from_success_modified_balance_to_and_allowance(self):
        self.coin.approve(amount=100, to='raghu')
        self.coin.transfer_from(amount=33, to='colin', main_account='stu', signer='raghu')

        self.assertEqual(self.coin.balances['colin'], 33)
        self.assertEqual(self.coin.balances['stu'], 1000000 - 33)
        self.assertEqual(self.coin.balances['stu', 'raghu'], 67)

    def test_mint_fails_if_not_owner(self):
        with self.assertRaises(AssertionError):
            self.coin.mint(amount=1000000, to='raghu', signer='raghu')

    def test_mint_succeeds_if_owner_and_modifies_balance_and_supply(self):
        self.coin.mint(amount=999, to='raghu')

        self.assertEqual(self.coin.balances['raghu'], 999)
        self.assertEqual(self.coin.supply.get(), 1000000 + 999)

    def test_change_ownership_modifies_owner(self):
        self.coin.change_ownership(new_owner='raghu')
        self.assertEqual(self.coin.owner.get(), 'raghu')

    def test_change_ownership_only_prior_owner(self):
        with self.assertRaises(AssertionError):
            self.coin.change_ownership(new_owner='colin', signer='raghu')

    def test_change_ownership_then_mint_succeeds(self):
        self.coin.change_ownership(new_owner='raghu')
        self.coin.mint(amount=999, to='raghu', signer='raghu')

        self.assertEqual(self.coin.balances['raghu'], 999)
        self.assertEqual(self.coin.supply.get(), 1000000 + 999)


def con_pixel_game():
    import con_coin

    plots = Hash()
    landlord = Variable()

    max_x = 256
    max_y = 256

    decay = 0.02
    tax_period = datetime.DAYS * 1

    def assert_in_bounds(x: int, y: int):
        assert 0 <= x < max_x, 'X coordinate out of bounds.'
        assert 0 <= y < max_y, 'Y coordinate out of bounds.'

    def assert_is_hex(color_string):
        assert len(color_string) == 256, 'Invalid color string passed.'
        assert int(color_string, 16), 'Color string is not a hex string.'

    @construct
    def seed():
        landlord.set(ctx.caller)

    @export
    def buy_plot(x: int, y: int, amount: float, price: float):
        assert_in_bounds(x, y)

        plot = plots[x, y]
        if plot is None:
            plot = {
                'colors': '0' * 256,
                'owner': ctx.caller,
                'price': price,
                'purchase_time': now
            }
            plots[x. y] = plot
        else:
            assert plot['price'] <= amount
            assert amount <= coin.allowance(owner=ctx.caller, spender=ctx.this)

            coin.transfer_from(amount=plot['price'], to=plot['owner'], main_account=ctx.sender)

            plot.update({
                'owner': ctx.caller,
                'price': price,
                'purchase_time': now
            })
            plots[x, y] = plot

    @export
    def set_plot(x: int, y: int, color_string: str):
        assert_is_hex(color_string)

        plot = plots[x, y]

        assert plot['owner'] == ctx.caller, 'You do not own this plot!'

        plot['colors'] = color_string

        plots[x, y] = plot


class TestPixelGame(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.flush()

        self.c.submit(con_coin)
        self.c.submit(con_pixel_game)
        self.pixel = self.c.get_contract('con_pixel_game')

    def tearDown(self):
        self.c.flush()

    def test_init(self):
        self.assertEqual(1, 1)
