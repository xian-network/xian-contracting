from unittest import TestCase
from contracting.stdlib.bridge import imports
from types import ModuleType
from contracting.storage.orm import Hash, Variable
import os

class TestImports(TestCase):
    def setUp(self):
        scope = {}
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        compiled_token_file_path = os.path.join(self.script_dir, "precompiled", "compiled_token.py")

        with open(compiled_token_file_path) as f:
            code = f.read()

        exec(code, scope)

        m = ModuleType('testing')

        vars(m).update(scope)
        del vars(m)['__builtins__']

        self.module = m

    def test_func_correct_type(self):
        def sup(x, y):
            return x + y

        s = imports.Func(name='sup', args=('x', 'y'))

        self.assertTrue(s.is_of(sup))

    def test_func_incorrect_name(self):
        def sup(x, y):
            return x + y

        s = imports.Func(name='not_much', args=('x', 'y'))

        self.assertFalse(s.is_of(sup))

    def test_func_incorrect_args(self):
        def sup(a, b):
            return a + b

        s = imports.Func(name='sup', args=('x', 'y'))

        self.assertFalse(s.is_of(sup))

    def test_func_correct_with_kwargs(self):
        def sup(x=100, y=200):
            return x + y

        s = imports.Func(name='sup', args=('x', 'y'))

        self.assertTrue(s.is_of(sup))

    def test_func_correct_with_annotations(self):
        def sup(x: int, y: int):
            return x + y

        s = imports.Func(name='sup', args=('x', 'y'))

        self.assertTrue(s.is_of(sup))

    def test_func_correct_with_kwargs_and_annotations(self):
        def sup(x: int=100, y: int=100):
            return x + y

        s = imports.Func(name='sup', args=('x', 'y'))

        self.assertTrue(s.is_of(sup))

    def test_func_correct_private(self):
        def __sup(a, b):
            return a + b

        s = imports.Func(name='sup', args=('a', 'b'), private=True)

        self.assertTrue(s.is_of(__sup))

    def test_func_false_private(self):
        def __sup(a, b):
            return a + b

        s = imports.Func(name='sup', args=('x', 'y'), private=True)

        self.assertFalse(s.is_of(__sup))

    def test_var_fails_if_type_not_of_datum(self):
        with self.assertRaises(AssertionError):
            imports.Var('blah', str)

    def test_enforce_interface_works_all_public_funcs(self):
        interface = [
            imports.Func('transfer', args=('amount', 'to')),
            imports.Func('balance_of', args=('account',)),
            imports.Func('total_supply'),
            imports.Func('allowance', args=('owner', 'spender')),
            imports.Func('approve', args=('amount', 'to')),
            imports.Func('transfer_from', args=('amount', 'to', 'main_account'))
        ]

        self.assertTrue(imports.enforce_interface(self.module, interface))

    def test_enforce_interface_works_on_subset_funcs(self):
        interface = [
            imports.Func('transfer', args=('amount', 'to')),
            imports.Func('balance_of', args=('account',)),
            imports.Func('total_supply'),
            imports.Func('allowance', args=('owner', 'spender')),
            imports.Func('transfer_from', args=('amount', 'to', 'main_account'))
        ]

        self.assertTrue(imports.enforce_interface(self.module, interface))

    def test_enforce_interface_fails_on_wrong_funcs(self):
        interface = [
            imports.Func('transfer', args=('amount', 'to')),
            imports.Func('balance_of', args=('account',)),
            imports.Func('spooky'),
            imports.Func('allowance', args=('owner', 'spender')),
            imports.Func('transfer_from', args=('amount', 'to', 'main_account'))
        ]

        self.assertFalse(imports.enforce_interface(self.module, interface))

    def test_enforce_interface_on_resources(self):
        interface = [
            imports.Var('supply', Variable),
            imports.Var('balances', Hash),
        ]

        self.assertTrue(imports.enforce_interface(self.module, interface))

    def test_complete_enforcement(self):
        interface = [
            imports.Func('transfer', args=('amount', 'to')),
            imports.Func('balance_of', args=('account',)),
            imports.Func('total_supply'),
            imports.Func('allowance', args=('owner', 'spender')),
            imports.Func('approve', args=('amount', 'to')),
            imports.Func('transfer_from', args=('amount', 'to', 'main_account')),
            imports.Var('supply', Variable),
            imports.Var('balances', Hash)
        ]

        self.assertTrue(imports.enforce_interface(self.module, interface))

    def test_private_function_enforcement(self):
        interface = [
            imports.Func('private_func', private=True),
        ]

        self.assertTrue(imports.enforce_interface(self.module, interface))

    def test_complete_enforcement_with_private_func(self):
        interface = [
            imports.Func('transfer', args=('amount', 'to')),
            imports.Func('balance_of', args=('account',)),
            imports.Func('total_supply'),
            imports.Func('allowance', args=('owner', 'spender')),
            imports.Func('approve', args=('amount', 'to')),
            imports.Func('private_func', private=True),
            imports.Func('transfer_from', args=('amount', 'to', 'main_account')),
            imports.Var('supply', Variable),
            imports.Var('balances', Hash)
        ]

        self.assertTrue(imports.enforce_interface(self.module, interface))