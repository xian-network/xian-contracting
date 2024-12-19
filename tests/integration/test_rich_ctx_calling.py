from unittest import TestCase
from contracting.client import ContractingClient


def con_module1():
    @export
    def get_context2():
        return {
            'name': 'get_context2',
            'owner': ctx.owner,
            'this': ctx.this,
            'signer': ctx.signer,
            'caller': ctx.caller,
            'entry': ctx.entry,
            'submission_name': ctx.submission_name
        }


def con_all_in_one():
    @export
    def call_me():
        return call_me_again()

    @export
    def call_me_again():
        return call_me_again_again()

    @export
    def call_me_again_again():
        return({
            'name': 'call_me_again_again',
            'owner': ctx.owner,
            'this': ctx.this,
            'signer': ctx.signer,
            'caller': ctx.caller,
            'entry': ctx.entry,
            'submission_name': ctx.submission_name
        })


def con_dynamic_import():

    @export
    def called_from_a_far():
        m = importlib.import_module('con_all_in_one')
        res = m.call_me_again_again()

        return [res, {
            'name': 'called_from_a_far',
            'owner': ctx.owner,
            'this': ctx.this,
            'signer': ctx.signer,
            'caller': ctx.caller,
            'entry': ctx.entry,
            'submission_name': ctx.submission_name
        }]

    @export
    def con_called_from_a_far_stacked():
        m = importlib.import_module('con_all_in_one')
        return m.call()

def con_submission_name_test():
    submission_name = Variable()

    @construct
    def seed():
        submission_name.set(ctx.submission_name)

    @export
    def get_submission_context():
        return submission_name.get()

    @export
    def get_entry_context():
        con_name, func_name = ctx.entry

        return {
            'entry_contract': con_name,
            'entry_function': func_name
        }



class TestRandomsContract(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.flush()

        # Submit contracts
        self.c.submit(con_module1)
        self.c.submit(con_all_in_one)
        self.c.submit(con_dynamic_import)
        self.c.submit(con_submission_name_test)

    def tearDown(self):
        self.c.flush()

    def test_ctx2(self):
        module = self.c.get_contract('con_module1')
        res = module.get_context2()
        expected = {
            'name': 'get_context2',
            'entry': ('con_module1', 'get_context2'),
            'owner': None,
            'this': 'con_module1',
            'signer': 'stu',
            'caller': 'stu',
            'submission_name': None
        }
        self.assertDictEqual(res, expected)

    def test_multi_call_doesnt_affect_parameters(self):
        aio = self.c.get_contract('con_all_in_one')
        res = aio.call_me()

        expected = {
            'name': 'call_me_again_again',
            'entry': ('con_all_in_one', 'call_me'),
            'owner': None,
            'this': 'con_all_in_one',
            'signer': 'stu',
            'caller': 'stu',
            'submission_name': None
        }

        self.assertDictEqual(res, expected)

    # To-Do: Figure out why this test does not work when using pytest tests/integration, but works when running the test directly
    # def test_dynamic_call(self):
    #     dy = self.c.get_contract('con_dynamic_import')
    #     res1, res2 = dy.called_from_a_far()

    #     expected1 = {
    #         'name': 'call_me_again_again',
    #         'entry': ('con_dynamic_import', 'called_from_a_far'),
    #         'owner': None,
    #         'this': 'con_all_in_one',
    #         'signer': 'stu',
    #         'caller': 'con_dynamic_import',
    #         'submission_name': None
    #     }

    #     expected2 = {
    #         'name': 'called_from_a_far',
    #         'entry': ('con_dynamic_import', 'called_from_a_far'),
    #         'owner': None,
    #         'this': 'con_dynamic_import',
    #         'signer': 'stu',
    #         'caller': 'stu',
    #         'submission_name': None
    #     }

    #     self.assertDictEqual(res1, expected1)
    #     self.assertDictEqual(res2, expected2)


    def test_submission_name_in_construct_function(self):
        contract = self.c.get_contract('con_submission_name_test')
        submission_name = contract.get_submission_context()

        self.assertEqual("con_submission_name_test", submission_name)

    def test_entry_context(self):
        contract = self.c.get_contract('con_submission_name_test')
        details = contract.get_entry_context()

        self.assertEqual("con_submission_name_test", details.get('entry_contract'))
        self.assertEqual("get_entry_context", details.get('entry_function'))