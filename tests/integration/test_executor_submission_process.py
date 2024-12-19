from unittest import TestCase
from contracting.storage.driver import Driver
from contracting.execution.executor import Executor
from contracting.compilation.compiler import ContractingCompiler
import os

def submission_kwargs_for_file(f):
    # Get the file name only by splitting off directories
    split = f.split('/')
    split = split[-1]

    # Now split off the .s
    split = split.split('.')
    contract_name = split[0]

    with open(f) as file:
        contract_code = file.read()

    return {
        'name': f'con_{contract_name}',
        'code': contract_code,
    }


TEST_SUBMISSION_KWARGS = {
    'sender': 'stu',
    'contract_name': 'submission',
    'function_name': 'submit_contract'
}


class TestExecutor(TestCase):
    def setUp(self):
        self.d = Driver()
        self.d.flush_full()

        submission_path = os.path.join(os.path.dirname(__file__), "test_contracts", "submission.s.py")

        with open(submission_path) as f:
            contract = f.read()

        self.d.set_contract(name='submission',
                            code=contract)
        self.d.commit()

        self.compiler = ContractingCompiler()

    def tearDown(self):
        self.d.flush_full()

    def test_submission(self):
        e = Executor(metering=False)

        code = '''@export
def d():
    a = 1
    return 1            
'''

        kwargs = {
            'name': 'con_stubucks',
            'code': code
        }

        e.execute(**TEST_SUBMISSION_KWARGS, kwargs=kwargs, auto_commit=True)

        self.compiler.module_name = 'con_stubucks'
        new_code = self.compiler.parse_to_code(code)

        self.assertEqual(self.d.get_contract('con_stubucks'), new_code)

    def test_submission_then_function_call(self):
        e = Executor(metering=False)

        code = '''@export
def d():
    return 1            
'''

        kwargs = {
            'name': 'con_stubuckz',
            'code': code
        }

        e.execute(**TEST_SUBMISSION_KWARGS, kwargs=kwargs)
        output = e.execute(sender='stu', contract_name='con_stubuckz', function_name='d', kwargs={})

        self.assertEqual(output['result'], 1)
        self.assertEqual(output['status_code'], 0)

    def test_kwarg_helper(self):
        test_orm_variable_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_variable_contract.s.py")

        k = submission_kwargs_for_file(test_orm_variable_contract_path)

        code = '''v = Variable()

@export
def set_v(i: int):
    v.set(i)

@export
def get_v():
    return v.get()
'''

        self.assertEqual(k['name'], 'con_orm_variable_contract')
        self.assertEqual(k['code'], code)

    def test_orm_variable_sets_in_contract(self):
        e = Executor(metering=False)

        test_orm_variable_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_variable_contract.s.py")

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(test_orm_variable_contract_path), auto_commit=True)

        e.execute('stu', 'con_orm_variable_contract', 'set_v', kwargs={'i': 1000}, auto_commit=True)

        i = self.d.get('con_orm_variable_contract.v')
        self.assertEqual(i, 1000)

    def test_orm_variable_gets_in_contract(self):
        e = Executor(metering=False)

        test_orm_variable_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_variable_contract.s.py")

        e.execute(**TEST_SUBMISSION_KWARGS,
                    kwargs=submission_kwargs_for_file(test_orm_variable_contract_path))

        res = e.execute('stu', 'con_orm_variable_contract', 'get_v', kwargs={})

        self.assertEqual(res['result'], None)

    def test_orm_variable_gets_and_sets_in_contract(self):
        e = Executor(metering=False)

        test_orm_variable_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_variable_contract.s.py")

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(test_orm_variable_contract_path))

        e.execute('stu', 'con_orm_variable_contract', 'set_v', kwargs={'i': 1000})
        res = e.execute('stu', 'con_orm_variable_contract', 'get_v', kwargs={})

        self.assertEqual(res['result'], 1000)

    def test_orm_hash_sets_in_contract(self):
        e = Executor(metering=False)

        test_orm_hash_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_hash_contract.s.py")

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(test_orm_hash_contract_path), auto_commit=True)

        e.execute('stu', 'con_orm_hash_contract', 'set_h', kwargs={'k': 'key1', 'v': 1234}, auto_commit=True)
        e.execute('stu', 'con_orm_hash_contract', 'set_h', kwargs={'k': 'another_key', 'v': 9999}, auto_commit=True)

        key1 = self.d.get('con_orm_hash_contract.h:key1')
        another_key = self.d.get('con_orm_hash_contract.h:another_key')

        self.assertEqual(key1, 1234)
        self.assertEqual(another_key, 9999)

    def test_orm_hash_gets_in_contract(self):
        e = Executor(metering=False)

        test_orm_hash_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_hash_contract.s.py")

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(test_orm_hash_contract_path))

        res = e.execute('stu', 'con_orm_hash_contract', 'get_h', kwargs={'k': 'test'})

        self.assertEqual(res['result'], None)

    def test_orm_hash_gets_and_sets_in_contract(self):
        e = Executor(metering=False)

        test_orm_hash_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_hash_contract.s.py")

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(test_orm_hash_contract_path))

        e.execute('stu', 'con_orm_hash_contract', 'set_h', kwargs={'k': 'key1', 'v': 1234})
        e.execute('stu', 'con_orm_hash_contract', 'set_h', kwargs={'k': 'another_key', 'v': 9999})

        key1 = e.execute('stu', 'con_orm_hash_contract', 'get_h', kwargs={'k': 'key1'})
        another_key = e.execute('stu', 'con_orm_hash_contract', 'get_h', kwargs={'k': 'another_key'})

        self.assertEqual(key1['result'], 1234)
        self.assertEqual(another_key['result'], 9999)

    def test_orm_foreign_variable_sets_in_contract_doesnt_work(self):
        e = Executor(metering=False)

        test_orm_variable_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_variable_contract.s.py")
        test_orm_foreign_key_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_foreign_key_contract.s.py")

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(test_orm_variable_contract_path))
        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(test_orm_foreign_key_contract_path))

        e.execute('stu', 'con_orm_variable_contract', 'set_v', kwargs={'i': 1000})

        # this should fail
        status = e.execute('stu', 'con_orm_foreign_key_contract', 'set_fv', kwargs={'i': 999})

        self.assertEqual(status['status_code'], 1)

        i = e.execute('stu', 'con_orm_variable_contract', 'get_v', kwargs={})
        self.assertEqual(i['result'], 1000)

    def test_orm_foreign_variable_gets_in_contract(self):
        e = Executor(metering=False)

        test_orm_variable_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_variable_contract.s.py")
        test_orm_foreign_key_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_foreign_key_contract.s.py")

        e.execute(**TEST_SUBMISSION_KWARGS, 
                  kwargs=submission_kwargs_for_file(test_orm_variable_contract_path))
        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(test_orm_foreign_key_contract_path))

        e.execute('stu', 'con_orm_variable_contract', 'set_v', kwargs={'i': 424242})
        # this should fail
        i = e.execute('stu', 'con_orm_foreign_key_contract', 'get_fv', kwargs={})

        self.assertEqual(i['result'], 424242)

    def test_orm_foreign_hash_sets_in_contract_doesnt_work(self):
        e = Executor(metering=False)

        test_orm_hash_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_hash_contract.s.py")
        test_orm_foreign_hash_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_foreign_hash_contract.s.py")  

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(test_orm_hash_contract_path), auto_commit=True)
        e.execute(**TEST_SUBMISSION_KWARGS, 
                  kwargs=submission_kwargs_for_file(test_orm_foreign_hash_contract_path), auto_commit=True)

        e.execute('stu', 'con_orm_hash_contract', 'set_h', kwargs={'k': 'key1', 'v': 1234}, auto_commit=True)
        e.execute('stu', 'con_orm_hash_contract', 'set_h', kwargs={'k': 'another_key', 'v': 9999}, auto_commit=True)

        status_1 = e.execute('stu', 'con_orm_foreign_hash_contract', 'set_fh', kwargs={'k': 'key1', 'v': 5555}, auto_commit=True)
        status_2 = e.execute('stu', 'con_orm_foreign_hash_contract', 'set_fh', kwargs={'k': 'another_key', 'v': 1000}, auto_commit=True)

        key1 = self.d.get('con_orm_hash_contract.h:key1')
        another_key = self.d.get('con_orm_hash_contract.h:another_key')

        self.assertEqual(key1, 1234)
        self.assertEqual(another_key, 9999)
        self.assertEqual(status_1['status_code'], 1)
        self.assertEqual(status_2['status_code'], 1)

    def test_orm_foreign_hash_gets_and_sets_in_contract(self):
        e = Executor(metering=False)

        test_orm_hash_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_hash_contract.s.py")
        test_orm_foreign_hash_contract_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_foreign_hash_contract.s.py")  

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(test_orm_hash_contract_path))

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(test_orm_foreign_hash_contract_path))

        e.execute('stu', 'con_orm_hash_contract', 'set_h', kwargs={'k': 'key1', 'v': 1234})
        e.execute('stu', 'con_orm_hash_contract', 'set_h', kwargs={'k': 'another_key', 'v': 9999})

        key1 = e.execute('stu', 'con_orm_foreign_hash_contract', 'get_fh', kwargs={'k': 'key1'})
        another_key = e.execute('stu', 'con_orm_foreign_hash_contract', 'get_fh', kwargs={'k': 'another_key'})

        self.assertEqual(key1['result'], 1234)
        self.assertEqual(another_key['result'], 9999)

    def test_orm_contract_not_accessible(self):
        e = Executor(metering=False)

        test_orm_no_contract_access_path = os.path.join(os.path.dirname(__file__), "test_contracts", "orm_no_contract_access.s.py")

        output = e.execute(**TEST_SUBMISSION_KWARGS,
            kwargs=submission_kwargs_for_file(test_orm_no_contract_access_path))

        self.assertEqual(str(output['result']) , '["Line 1 : S2- Illicit use of \'_\' before variable : __Contract"]')

    def test_construct_function_sets_properly(self):
        e = Executor(metering=False)

        test_construct_function_works_path = os.path.join(os.path.dirname(__file__), "test_contracts", "construct_function_works.s.py")

        r = e.execute(**TEST_SUBMISSION_KWARGS,
            kwargs=submission_kwargs_for_file(test_construct_function_works_path))

        output = e.execute('stu', 'con_construct_function_works', 'get', kwargs={})

        self.assertEqual(output['result'], 42)

    def test_import_exported_function_works(self):
        e = Executor(metering=False)

        import_this_path = os.path.join(os.path.dirname(__file__), "test_contracts", "import_this.s.py")
        importing_that_path = os.path.join(os.path.dirname(__file__), "test_contracts", "importing_that.s.py")

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(import_this_path))

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(importing_that_path))

        output = e.execute('stu', 'con_importing_that', 'test', kwargs={})
        self.assertEqual(output['result'], 12345 - 1000)

    def test_arbitrary_environment_passing_works_via_executor(self):
        e = Executor(metering=False)

        i_use_env_path = os.path.join(os.path.dirname(__file__), "test_contracts", "i_use_env.s.py")

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(i_use_env_path))

        this_is_a_passed_in_variable = 555

        env = {'this_is_a_passed_in_variable': this_is_a_passed_in_variable}

        output = e.execute('stu', 'con_i_use_env', 'env_var', kwargs={}, environment=env)

        self.assertEqual(output['result'], this_is_a_passed_in_variable)

    def test_arbitrary_environment_passing_fails_if_not_passed_correctly(self):
        e = Executor(metering=False)

        i_use_env_path = os.path.join(os.path.dirname(__file__), "test_contracts", "i_use_env.s.py")

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file(i_use_env_path))

        this_is_a_passed_in_variable = 555

        env = {'this_is_another_passed_in_variable': this_is_a_passed_in_variable}

        output = e.execute('stu', 'i_use_env', 'env_var', kwargs={}, environment=env)

        self.assertEqual(output['status_code'], 1)
