from importlib.abc import Loader
from importlib import invalidate_caches, __import__
from importlib.machinery import ModuleSpec
from contracting.storage.driver import Driver
from contracting.stdlib import env
from contracting.execution.runtime import rt

import marshal
import builtins
import sys
import importlib.util

def is_valid_import(name):
    spec = importlib.util.find_spec(name)
    if not isinstance(spec.loader, DatabaseLoader):
        raise ImportError("module {} cannot be imported in a smart contract.".format(name))

def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    if globals is not None and globals.get('__contract__') is True:
        spec = importlib.util.find_spec(name)
        if spec is None or not isinstance(spec.loader, DatabaseLoader):
            raise ImportError("module {} cannot be imported in a smart contract.".format(name))

    return __import__(name, globals, locals, fromlist, level)

def enable_restricted_imports():
    builtins.__import__ = restricted_import

def disable_restricted_imports():
    builtins.__import__ = __import__

def uninstall_builtins():
    sys.meta_path.clear()
    sys.path_hooks.clear()
    sys.path.clear()
    sys.path_importer_cache.clear()
    invalidate_caches()

def install_database_loader(driver=Driver()):
    DatabaseFinder.driver = driver
    if DatabaseFinder() not in sys.meta_path:
        sys.meta_path.insert(0, DatabaseFinder())

def uninstall_database_loader():
    sys.meta_path = list(set(sys.meta_path))
    if DatabaseFinder() in sys.meta_path:
        sys.meta_path.remove(DatabaseFinder())

def install_system_contracts(directory=''):
    pass

class DatabaseFinder:
    driver = Driver()

    def find_spec(self, fullname, path=None, target=None):
        if self.driver.get_contract(fullname) is None:
            return None
        return ModuleSpec(fullname, DatabaseLoader(self.driver))

    def __eq__(self, other):
        return isinstance(other, DatabaseFinder)

    def __hash__(self):
        return hash('DatabaseFinder')

class DatabaseLoader(Loader):
    module_cache = {}

    def __init__(self, d=Driver()):
        self.d = d

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        # fetch the individual contract
        code = self.module_cache.get(module.__name__)

        if code is None:
            code = self.d.get_compiled(module.__name__)
            if code is None:
                raise ImportError("Module {} not found".format(module.__name__))

            if type(code) != bytes:
                code = bytes.fromhex(code)

            code = marshal.loads(code)
            self.module_cache[module.__name__] = code

        if code is None:
            raise ImportError("Module {} not found".format(module.__name__))

        scope = env.gather()
        scope.update(rt.env)

        scope.update({'__contract__': True})

        # execute the module with the std env and update the module to pass forward
        exec(code, scope)

        # Update the module's attributes with the new scope
        vars(module).update(scope)
        del vars(module)['__builtins__']

        rt.loaded_modules.append(module.__name__)

    def module_repr(self, module):
        return '<module {!r} (smart contract)>'.format(module.__name__)

    def __eq__(self, other):
        return isinstance(other, DatabaseLoader) and self.d == other.d

    def __hash__(self):
        return hash(('DatabaseLoader', self.d))
