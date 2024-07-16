from unittest import TestCase


def foundation():
    import currency

    owner = Variable()

    @construct
    def seed(vk):
        owner.set(vk)

    @export
    def withdraw(amount):
        if ctx.caller == owner.get():
            currency.transfer(ctx.caller, amount)

    @export
    def change_owner(vk):
        if ctx.caller == owner.get():
            owner.set(vk)


class TestFoundation(TestCase):
    def test_init(self):
        pass