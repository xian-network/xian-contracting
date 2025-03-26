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

    def test_call_function_works_with_public_function(self):
        # Should successfully call a public function
        result = imports.call_function(self.module, 'transfer', {'amount': 100, 'to': 'someone'})
        self.assertIsNotNone(result)

    def test_call_function_fails_with_private_function(self):
        # Should raise ImportError when trying to call a private function
        with self.assertRaises(ImportError):
            imports.call_function(self.module, '__private_func', {})

    def test_call_function_fails_with_nonexistent_function(self):
        # Should raise ImportError when function doesn't exist
        with self.assertRaises(ImportError):
            imports.call_function(self.module, 'nonexistent_function', {})

    def test_call_function_fails_with_non_function_attribute(self):
        # Should raise ImportError when trying to call a variable/non-function
        with self.assertRaises(ImportError):
            imports.call_function(self.module, 'supply', {})

    def test_call_function_fails_with_system_attribute(self):
        # Should raise ImportError when trying to access system attributes
        with self.assertRaises(ImportError):
            imports.call_function(self.module, '__name__', {})

    def test_call_function_fails_with_dunder_prefix(self):
        # Should raise ImportError when function name starts with __
        with self.assertRaises(ImportError):
            imports.call_function(self.module, '__dict__', {})

    def test_call_function_with_correct_arguments(self):
        # Should successfully call function with correct arguments
        result = imports.call_function(self.module, 'balance_of', {'account': 'someone'})
        self.assertIsNotNone(result)

    def test_call_function_with_incorrect_arguments(self):
        # Should raise TypeError when wrong arguments are provided
        with self.assertRaises(TypeError):
            imports.call_function(self.module, 'transfer', {'wrong_arg': 'value'})

    def test_call_function_with_empty_arguments(self):
        # Should successfully call function that expects no arguments
        result = imports.call_function(self.module, 'total_supply', {})
        self.assertIsNotNone(result)

    def test_call_function_fails_with_invalid_module(self):
        # Should raise ImportError when module is None
        with self.assertRaises(ImportError):
            imports.call_function(None, 'some_function', {})