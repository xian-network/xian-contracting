from unittest import TestCase
from contracting.compilation.compiler import ContractingCompiler
from contracting.stdlib import env
from contracting import constants

import re
import astor
import os

class TestSenecaCompiler(TestCase):
    def test_visit_assign_variable(self):
        code = '''
v = Variable()
'''
        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        scope = env.gather()

        exec(code_str, scope)

        v = scope['__v']

        self.assertEqual(v._key, '__main__.v')

    def test_visit_assign_foreign_variable(self):
        code = '''
fv = ForeignVariable(foreign_contract='scoob', foreign_name='kumbucha')
        '''
        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        scope = env.gather()

        exec(code_str, scope)

        fv = scope['__fv']

        self.assertEqual(fv._key, 'scoob.kumbucha')

    def test_assign_hash_variable(self):
        code = '''
h = Hash()
        '''
        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        scope = env.gather()

        exec(code_str, scope)

        h = scope['__h']

        self.assertEqual(h._key, '__main__.h')

    def test_assign_foreign_hash(self):
        code = '''
fv = ForeignHash(foreign_contract='scoob', foreign_name='kumbucha')
        '''

        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        scope = env.gather()

        exec(code_str, scope)

        fv = scope['__fv']

        self.assertEqual(fv._key, 'scoob.kumbucha')
        # self.assertEqual(fv.foreign_key, 'scoob.kumbucha')
#
#     def test_export_decorator_pops(self):
#         code = '''
# @export
# def funtimes():
#     print('cool')
#         '''
#
#         c = ContractingCompiler()
#         comp = c.parse(code, lint=False)
#         code_str = astor.to_source(comp)
#
#         self.assertNotIn('@export', code_str)

    def test_private_function_prefixes_properly(self):
        code = '''
def private():
    print('cool')
        '''

        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        self.assertIn('__private', code_str)

    def test_private_func_call_in_public_func_properly_renamed(self):
        code = '''
@export
def public():
    private('hello')
    
def private(message):
    print(message)
'''

        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        # there should be two private occurances of the method call
        self.assertEqual(len([m.start() for m in re.finditer('__private', code_str)]), 2)

    def test_private_func_call_in_other_private_functions(self):
        code = '''
def a():
    b()
    
def b():
    c()
    
def c():
    e()
    
def d():
    print('hello')
    
def e():
    d()        
'''
        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        self.assertEqual(len([m.start() for m in re.finditer(constants.PRIVATE_METHOD_PREFIX, code_str)]), 9)

    def test_construct_renames_properly(self):
        code = '''
@construct
def seed():
    print('yes')

@export
def hello():
    print('no')
    
def goodbye():
    print('idk')
        '''

        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

    def test_token_contract_parses_correctly(self):
        currency_path = os.path.join(os.path.dirname(__file__), "test_contracts", "currency.s.py")

        with open(currency_path) as f:
            code = f.read()


        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

    def test_export_decorator_argument_is_added(self):
        code = '''
@export
def test():
    pass        
'''
        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)
        print(code_str)
