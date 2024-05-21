from contracting.compilation.compiler import ContractingCompiler
from contracting.storage.driver import Driver
from contracting.execution.runtime import rt
from contracting.stdlib import env
from contracting import constants

_driver = rt.env.get('__Driver') or Driver()


class Contract:
    def __init__(self, driver: Driver = _driver):
        self._driver = driver

    def submit(self, name, code, owner=None, constructor_args={}, developer=None):
        if self._driver.get_contract(name) is not None:
            raise Exception('Contract already exists.')

        c = ContractingCompiler(module_name=name)

        code_obj = c.parse_to_code(code, lint=True)

        scope = env.gather()
        scope.update({'__contract__': True})
        scope.update(rt.env)

        exec(code_obj, scope)

        if scope.get(constants.INIT_FUNC_NAME) is not None:
            if constructor_args is None:
                constructor_args = {}
            scope[constants.INIT_FUNC_NAME](**constructor_args)

        now = scope.get('now')
        if now is not None:
            self._driver.set_contract(
                name=name,
                code=code_obj,
                owner=owner,
                overwrite=False,
                timestamp=now,
                developer=developer
            )
        else:
            self._driver.set_contract(
                name=name,
                code=code_obj,
                owner=owner,
                overwrite=False,
                developer=developer
            )
