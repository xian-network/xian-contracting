from types import FunctionType, ModuleType
from contracting.constants import PRIVATE_METHOD_PREFIX
from contracting.storage.orm import Datum
from contracting.storage.driver import Driver, OWNER_KEY
from contracting.execution.runtime import rt

import importlib
import sys


def extract_closure(fn):
    closure = fn.__closure__[0]
    return closure.cell_contents


class Func:
    def __init__(self, name, args=(), private=False):
        self.name = name

        if private:
            self.name = PRIVATE_METHOD_PREFIX + self.name

        self.args = args

    def is_of(self, f: FunctionType):

        if f.__closure__ is not None:
            f = extract_closure(f)

        num_args = f.__code__.co_argcount

        if f.__code__.co_name == self.name and f.__code__.co_varnames[:num_args] == self.args:
            return True

        return False


class Var:
    def __init__(self, name, t):
        self.name = PRIVATE_METHOD_PREFIX + name
        assert issubclass(t, Datum), 'Cannot enforce a variable that is not a Variable, Hash, or Foreign type!'
        self.type = t

    def is_of(self, v):
        if isinstance(v, self.type):
            return True
        return False


def import_module(name):
    assert not name.isdigit() and all(c.isalnum() or c == '_' for c in name), 'Invalid contract name!'
    assert name.islower(), 'Name must be lowercase!'

    _driver = rt.env.get('__Driver') or Driver()

    if name in set(list(sys.stdlib_module_names) + list(sys.builtin_module_names)):
        raise ImportError

    if name.startswith('_'):
        raise ImportError

    if _driver.get_contract(name) is None:
        raise ImportError

    return importlib.import_module(name, package=None)


def enforce_interface(m: ModuleType, interface: list):
    implemented = vars(m)

    for i in interface:
        attribute = implemented.get(i.name)
        if attribute is None:
            return False

        # Branch for data types
        if isinstance(attribute, Datum):
            if not i.is_of(attribute):
                return False

        if isinstance(attribute, FunctionType):
            if not i.is_of(attribute):
                return False

    return True


def owner_of(m: ModuleType):
    _driver = rt.env.get('__Driver') or Driver()
    owner = _driver.get_var(m.__name__, OWNER_KEY)
    return owner


def call_function(module_name: str, function_name: str, kwargs: dict):
    """
    Securely calls a function on an imported contract
    - module_name: Name of the contract to call
    - function_name: Name of the function to call
    - kwargs: Arguments to pass to the function
    """
    # Validate function name first
    if function_name.startswith(PRIVATE_METHOD_PREFIX):
        raise ImportError('Access to internal functions is forbidden')
    
    # Reuse existing import logic to get the module
    module = importlib.import_module(module_name)

    # Get all attributes
    implemented = vars(module)

    # Validate the function exists
    if function_name not in implemented:
        raise ImportError(f"Function {function_name} not found in contract {module_name}")

    # Get and validate the function
    fn = implemented[function_name]

    # Additional security checks
    if not isinstance(fn, FunctionType):
        raise ImportError(f"{function_name} is not a callable function")

    if fn.__name__.startswith(PRIVATE_METHOD_PREFIX):
        raise ImportError('Access to internal functions is forbidden')

    # Call the function with provided arguments
    return fn(**kwargs)


imports_module = ModuleType('importlib')
imports_module.import_module = import_module
imports_module.enforce_interface = enforce_interface
imports_module.Func = Func
imports_module.Var = Var
imports_module.owner_of = owner_of
imports_module.call_function = call_function

exports = {
    'importlib': imports_module,
}
