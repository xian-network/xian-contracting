from contracting.execution.executor import Executor
from contracting.storage.driver import Driver
from contracting.compilation.compiler import ContractingCompiler
from contracting.stdlib.bridge.time import Datetime
from datetime import datetime
from functools import partial
from types import FunctionType

import ast
import inspect
import astor
import autopep8
import os

from . import constants

from .storage.orm import Variable
from .storage.orm import Hash


class AbstractContract:
    def __init__(self, name, signer, environment, executor: Executor, funcs, return_full_output=False):
        self.name = name
        self.signer = signer
        self.environment = environment
        self.executor = executor
        self.functions = funcs

        # set up virtual functions
        for f in funcs:
            # unpack tuple packed in SenecaClient
            func, kwargs = f

            # set the kwargs to None. these will fail if they are not provided
            default_kwargs = {}
            for kwarg in kwargs:
                default_kwargs[kwarg] = None

            # each function is a partial that allows kwarg overloading and overriding
            setattr(self, func, partial(self._abstract_function_call,
                                        signer=self.signer,
                                        contract_name=self.name,
                                        executor=self.executor,
                                        func=func,
                                        return_full_output=return_full_output,
                                        # environment=self.environment,
                                        **default_kwargs))

    def keys(self):
        return self.executor.driver.keys(self.name)

    # a variable contains a DOT, but no __, and no :
    # a hash contains a DOT, no __, and a :
    # a constant contains __, a DOT, and :

    def quick_read(self, variable, key=None, args=None):
        a = []

        if key is not None:
            a.append(key)

        if args is not None and isinstance(args, list):
            for arg in args:
                a.append(arg)

        k = self.executor.driver.make_key(contract=self.name, variable=variable, args=a)
        return self.executor.driver.get(k)

    def quick_write(self, variable, key=None, value=None, args=None):
        if key is not None:
            a = [key]
        else:
            a = []

        if args is not None and isinstance(args, list):
            for arg in args:
                a.append(arg)

        k = self.executor.driver.make_key(contract=self.name, variable=variable, args=a)

        self.executor.driver.set(k, value)
        self.executor.driver.commit()

    def run_private_function(self, f, signer=None, environment=None, **kwargs):
        # Override kwargs if provided
        signer = signer or self.signer
        environment = environment or self.environment

        # Let executor access private functions
        self.executor.bypass_privates = True

        # Append private method prefix to function name if it isn't there already
        if not f.startswith(constants.PRIVATE_METHOD_PREFIX):
            f = '{}{}'.format(constants.PRIVATE_METHOD_PREFIX, f)

        # Execute
        result = self._abstract_function_call(
            signer=signer,
            executor=self.executor,
            contract_name=self.name,
            environment=environment,
            func=f,
            metering=None,
            now=None,
            **kwargs
        )

        # Set executor back to restricted mode
        self.executor.bypass_privates = False

        return result

    def __getattr__(self, item):
        try:
            # return the attribute if it exists on the instance
            return self.__getattribute__(item)
        except AttributeError as e:

            # otherwise, attempt to resolve it. full name is contract.item
            fullname = '{}.{}'.format(self.name, item)

            # if the raw name exists, it is a __protected__ or a variable, so prepare for those
            if fullname in self.keys():
                variable = Variable(contract=self.name, name=item, driver=self.executor.driver)

                # return just the value if it is __protected__ to prevent sets
                if item.startswith('__'):
                    return variable.get()

                # otherwise, return the variable object with allows sets
                return variable

            # otherwise, see if contract.items: has more than one entry
            if len(self.executor.driver.values(prefix=self.name + '.' + item + ':')) > 0:

                # if so, it is a hash. return the hash object
                return Hash(contract=self.name, name=item, driver=self.executor.driver)

            # otherwise, the attribut does not exist, so throw the error.
            raise e

    def now(self):
        d = datetime.today()
        return Datetime(d.year, d.month, d.day, hour=d.hour, minute=d.minute)

    def _abstract_function_call(
            self,
            signer,
            executor,
            contract_name,
            func,
            environment=None,
            stamps=constants.DEFAULT_STAMPS,
            metering=None,
            now=None,
            return_full_output=False,
            **kwargs
    ):

        # for k, v in kwargs.items():
        #     assert v is not None, 'Keyword "{}" not provided. Must not be None.'.format(k)
        environment = environment or self.environment

        if now is None:
            now = self.now()

        if environment.get('now') is None:
            environment.update({'now': now})

        output = executor.execute(
            sender=signer,
            contract_name=contract_name,
            function_name=func,
            kwargs=kwargs,
            stamps=stamps,
            environment=environment,
            metering=metering
        )

        if executor.production:
            executor.sandbox.terminate()

        if output['status_code'] == 1:
            raise output['result'] if not return_full_output else output
        return output['result'] if not return_full_output else output


class ContractingClient:
    def __init__(
            self,
            signer='sys',
            submission_filename=os.path.join(os.path.dirname(__file__), 'contracts/submission.s.py'),
            storage_home=constants.STORAGE_HOME,
            driver:Driver=None,
            metering=False,
            compiler=ContractingCompiler(),
            environment={},
    ):
        driver = driver if driver is not None else Driver(storage_home=storage_home)
        self.executor = Executor(metering=metering, driver=driver)
        self.raw_driver = driver
        self.signer = signer
        self.compiler = compiler
        self.submission_filename = submission_filename
        self.environment = environment
        # Get submission contract from file
        if submission_filename is not None:
            # Seed the genesis contracts into the instance
            with open(self.submission_filename) as f:
                contract = f.read()

            self.raw_driver.set_contract(name='submission', code=contract)
            self.raw_driver.commit()

        # Get submission contract from state
        self.submission_contract = self.get_contract('submission')

    def set_submission_contract(self, filename=None, commit=True):
        state_contract = self.get_contract('submission')

        if filename is None:
            filename = self.submission_filename

        if filename is None and state_contract is None:
            raise AssertionError("No submission contract provided or found in state.")

        if filename is not None:
            with open(filename) as f:
                contract = f.read()

            self.raw_driver.delete_contract(name='submission')
            self.raw_driver.set_contract(name='submission', code=contract)

            if commit:
                self.raw_driver.commit()

        self.submission_contract = self.get_contract('submission')

    def flush(self):
        # flushes storage and resubmits genesis contracts
        self.raw_driver.flush_full()
        self.raw_driver.flush_cache()

        if self.submission_filename is not None:
            self.set_submission_contract()

    # Returns abstract contract which has partial methods mapped to each exported function.
    def get_contract(self, name):
        contract = self.raw_driver.get_contract(name)

        if contract is None:
            return None

        tree = ast.parse(contract)

        function_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

        funcs = []
        for definition in function_defs:
            func_name = definition.name
            kwargs = [arg.arg for arg in definition.args.args]

            funcs.append((func_name, kwargs))

        return AbstractContract(
            name=name,
            signer=self.signer,
            environment=self.environment,
            executor=self.executor,
            funcs=funcs,
        )

    def closure_to_code_string(self, f):
        closure_code = inspect.getsource(f)
        closure_code = autopep8.fix_code(closure_code)
        closure_tree = ast.parse(closure_code)

        # Remove the enclosing function by swapping out the function def node with its children
        assert len(closure_tree.body) == 1, 'Module has multiple body nodes.'
        assert isinstance(closure_tree.body[0], ast.FunctionDef), 'Function definition not found at root.'

        func_def_body = closure_tree.body[0]
        closure_tree.body = func_def_body.body

        contract_code = astor.to_source(closure_tree)
        name = func_def_body.name

        return contract_code, name

    def lint(self, f, raise_errors=False):
        if isinstance(f, FunctionType):
            f, _ = self.closure_to_code_string(f)

        tree = ast.parse(f)
        violations = self.compiler.linter.check(tree)

        if violations is None:
            return None
        else:
            if raise_errors:
                for v in violations:
                    raise Exception(v)
            else:
                return violations

    def compile(self, f):
        if isinstance(f, FunctionType):
            f, _ = self.closure_to_code_string(f)

        code = self.compiler.parse_to_code(f)
        return code

    def submit(self, f, name=None, metering=None, owner=None, constructor_args={}, signer=None):

        assert self.submission_contract is not None, "No submission contract set. Try set_submission_contract first."

        if isinstance(f, FunctionType):
            f, n = self.closure_to_code_string(f)
            if name is None:
                name = n

        assert name is not None, 'No name provided.'

        if signer is None:
            signer = self.signer

        self.submission_contract.submit_contract(
            name=name,
            code=f,
            owner=owner,
            constructor_args=constructor_args,
            metering=metering,
            signer=signer
        )

    def get_contracts(self):
        contracts = []
        for key in self.raw_driver.keys():
            if key.endswith('.__code__'):
                contracts.append(key.replace('.__code__', ''))
        return contracts

    def get_var(self, contract, variable, arguments=[], mark=False):
        return self.raw_driver.get_var(contract, variable, arguments, mark)

    def set_var(self, contract, variable, arguments=[], value=None, mark=False):
        self.raw_driver.set_var(contract, variable, arguments, value, mark)
