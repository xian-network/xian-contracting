from unittest import TestCase
from contracting.compilation.linter import Linter
import ast
from contracting.compilation.whitelists import ALLOWED_AST_TYPES, ALLOWED_ANNOTATION_TYPES, VIOLATION_TRIGGERS


class TestLinter(TestCase):
    def setUp(self):
        self.l = Linter()

    def test_linter(self):
        # log = get_logger("TestSenecaLinter")
        data = '''
@export
def a():
    b = 10
    return b
    '''

        print("stu code: \n{}".format(data))
        ptree = ast.parse(data)
        status = self.l.check(ptree)
        self.l.dump_violations()
        if status is None:
            print("Success!")
        else:
            print("Failed!")

        self.assertEqual(status, None)

    # TODO - Verify this tetst is working as expected.
    def test_good_ast_type(self):
        # Dictionary to handle special cases of AST nodes that require arguments
        special_cases = {
            ast.Index: lambda: ast.Index(value=ast.Str(s='test')),
        }

        for t in ALLOWED_AST_TYPES:
            if t in special_cases:
                _t = special_cases[t]()
            else:
                _t = t()

            self.l.ast_types(_t, 1)
            self.assertListEqual([], self.l._violations)

    def test_bad_ast_type(self):
        err = 'Line 1 : S1- Illegal contracting syntax type used : AsyncFunctionDef'
        t = ast.AsyncFunctionDef()
        self.l.ast_types(t, 1)
        self.l.dump_violations()
        self.assertMultiLineEqual(err, self.l._violations[0])

    def test_not_system_variable(self):
        v = 'package'
        self.l.not_system_variable(v, 1)
        self.l.dump_violations()
        self.assertListEqual([], self.l._violations)

    def test_system_variable(self):
        v = '__package__'
        err = "Line 1 : S2- Illicit use of '_' before variable : __package__"
        self.l.not_system_variable(v, 1)
        self.l.dump_violations()
        self.assertMultiLineEqual(err, self.l._violations[0])

    '''
    Is blocking all underscore variables really the solution to preventing access to system variables?
    '''
    def test_not_system_variable_ast(self):
        code = '''
@export
def a():
    __ruh_roh__ = 'shaggy'
        '''
        err = "Line 4 : S2- Illicit use of '_' before variable : __ruh_roh__"

        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        self.assertMultiLineEqual(err, self.l._violations[0])

    def test_not_system_variable_ast_success(self):
        code = '''
@export
def a():
    ruh_roh = 'shaggy'
        '''
        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        self.assertEqual(chk, None)
        self.assertListEqual([], self.l._violations)

    # def test_visit_async_func_def_fail(self):
    #     err = 'Error : Illegal AST type: AsyncFunctionDef'
    #     n = compilation.AsyncFunctionDef()
    #
    #     self.l.visit_AsyncFunctionDef(n)
    #     self.l.dump_violations()
    #     self.assertMultiLineEqual(err, self.l._violations[0])

    def test_visit_async_func_def_fail_code(self):
        code = '''
@export
async def a():
    ruh_roh = 'shaggy'
def b():
    c = 1 + 2
'''
        err = 'Line 3: S7- Illicit use of Async functions'

        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        self.assertEqual(len(chk), 3)
        self.assertMultiLineEqual(err, self.l._violations[0])

#TODO failing
    # def test_visit_class_fail(self):
    #     err = 'Error : Illegal AST type: ClassDef'
    #     n = compilation.ClassDef()
    #     self.l.visit_ClassDef(n)
    #     self.l.dump_violations()

        # self.assertMultiLineEqual(err, self.l._violations[0])

    def test_visit_class_fail_code(self):
        code = '''
class Scooby:
    pass
        '''
        err = 'Line 2: S6- Illicit use of classes'

        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        self.assertEqual(len(chk), 3)
        self.assertMultiLineEqual(err, self.l._violations[0])

    def test_visit_try_except_fail_code(self):
        code = '''
@export
def try_it():
    try:
        a = 0
    except:
        a = 1
'''
        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()

        print(self.l._violations)

    def test_accessing_system_vars(self):
        code = '''
@export
def a():
    ruh_roh = 'shaggy'
    ruh_roh.__dir__()
'''
        err = "Line 5 : S2- Illicit use of '_' before variable : __dir__"
        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        self.assertMultiLineEqual(err, self.l._violations[0])

    def test_accessing_attribute(self):
        code = '''
@export
def a():
    ruh_roh = 'shaggy'
    ruh_roh.capitalize()
    '''

        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        self.assertEqual(chk, None)
        self.assertListEqual([], self.l._violations)

#TODO failed test case

    def test_no_nested_imports(self):
        code = '''
@export
def a():
    import something
        '''

        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        self.assertEqual(chk, ['Line 3: S3- Illicit use of Nested imports'])

    def test_no_nested_imports_works(self):
        code = '''
@export
def a():
    ruh_roh = 'shaggy'
    ruh_roh.capitalize()
            '''

        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        self.assertEqual(chk, None)
        self.assertListEqual([], self.l._violations)

    def test_augassign(self):
        code = '''
@export
def a():
    b = 0
    b += 1
'''
        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        self.assertEqual(chk, None)
        self.assertListEqual([], self.l._violations)

    def test_no_import_from(self):
        code = '''
from something import a
@export
def a():
    b = 0
    b += 1
'''
        err = 'Line 2: S4- ImportFrom compilation nodes not yet supported'

        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        self.assertMultiLineEqual(err, self.l._violations[0])

# disabling import check it would be done by compiler

#     def test_import_non_existent_contract(self):
#         code = '''
# import something
# @export
# def a():
#     b = 0
#     b += 1
# '''
#         err = 'Line 2: S5- Contract not found in lib: something'
#
#         c = compilation.parse(code)
#         self.l.check(c)
#         self.l.dump_violations()
#         self.assertMultiLineEqual(err, self.l._violations[0])

    def test_final_checks_set_properly(self):
        code = '''
def a():
    b = 0
    b += 1
        '''

        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        self.assertEqual(chk, ['Line 0: S13- No valid contracting decorator found'])
        self.assertFalse(self.l._is_one_export)

    def test_collect_function_defs(self):
        code = '''
@export
def a():
    return 42

@export
def b():
    return 1000000

@export
def x():
    return 64

@export
def y():
    return 24
'''
        c = ast.parse(code)
        self.l._collect_function_defs(c)
        self.l.dump_violations()
        self.assertEqual(self.l._functions, ['a', 'b', 'x', 'y'])

    def test_assignment_of_import(self):
        code = '''
import import_this

@export
def test():
    a = import_this.howdy()
    a -= 1000
    return a        
'''
        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()

    def test_good_orm_initialization(self):
        code = '''
v = Variable()

@export
def set(i: int):
    v.set(i)
'''
        c = ast.parse(code)
        chk = self.l.check(c)
        self.assertEqual(self.l._violations, [])

    def test_bad_orm_initialization(self):
        code = '''
v = Variable(contract='currency', name='stus_balance')

@export
def set(i: int):
    v.set(i)
'''
        c = ast.parse(code)
        chk = self.l.check(c)
        self.assertEqual(chk[0], 'Line 2: S11- Illicit keyword overloading for ORM assignments')

    def test_multi_targets_orm_fails(self):
        code = '''
v, x = Variable()

@export
def set(i):
    v.set(i)
    '''
        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        print(chk)
        self.assertEqual(chk[0], 'Line 2: S12- Multiple targets to ORM definition detected')

    def test_multi_decorator_fails(self):
        code = '''
@construct
@export
def kaboom():
    print('i like to break things')
'''
        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        self.assertEqual(chk[0], 'Line 4: S10- Illicit use of multiple decorators: Detected: 2 MAX limit: 1')

    def test_invalid_decorator_fails(self):
        code = '''
@contracting_invalid
def wont_work():
    print('i hope')
'''
        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        self.assertEqual(chk[1], 'Line 3: S8- Invalid decorator used: valid list: contracting_invalid')

    def test_multiple_constructors_fails(self):
        code = '''
@construct
def seed_1():
    pass
    
@construct
def seed_1():
    pass
    
@export
def seed_5():
    pass
'''

        c = ast.parse(code)
        chk = self.l.check(c)
        self.l.dump_violations()
        self.assertEqual(len(chk),1)
        self.assertEqual(self.l._violations, ['Line 7: S9- Multiple use of constructors detected'])

    def test_function_str_annotation(self):
        code = '''
@export
def greeting(name: str):
    return 'Hello ' + name
'''
        c = ast.parse(code)
        chk = self.l.check(c)

        self.assertEqual(chk, None)

    def test_function_dict_annotation(self):
        code = '''
@export
def greeting(name: dict):
    return 'Hello ' + name
'''
        c = ast.parse(code)
        chk = self.l.check(c)

        self.assertEqual(chk, None)

    def test_function_bad_annotation(self):
        code = '''
@export
def greeting(name: mytype):
    return 'Hello ' + name
'''
        c = ast.parse(code)
        chk = self.l.check(c)

        self.assertEqual(chk, ['Line 3 : S16- Illegal argument annotation used : mytype'])


    def test_function_none_annotation(self):
        code = '''
@export
def greeting(name):
    return 'Hello ' + name
'''
        c = ast.parse(code)
        chk = self.l.check(c)

        self.assertEqual(chk, ['Line 3 : S17- No valid argument annotation found'])


    def test_none_return_annotation(self):
        code = '''
@export
def greeting(name: str):
    return 'Hello ' + name
'''
        c = ast.parse(code)
        chk = self.l.check(c)

        self.assertEqual(self.l._violations, [])


    def test_contract_annotation(self):
        code ='''
@export
def transfer(amount, to):
    sender = ctx.caller
    assert balances[sender] >= amount, 'Not enough coins to send!'

    balances[sender] -= amount
    balances[to] += amount

def greeting(name):
    return 'Hello ' + name
'''
        c = ast.parse(code)
        chk = self.l.check(c)

        self.assertEqual(chk, ['Line 3 : S17- No valid argument annotation found'])


## ANNOTATIONS ARE OKAY
#   def test_function_return_annotation(self):
#       code = '''
#@export
#def greeting(name: str) -> str:
#    return 'Hello ' + name
#'''
#        c = ast.parse(code)
#        chk = self.l.check(c)
#
#        self.assertEqual(['Line 2 : S18- Illegal use of return annotation : str'], chk)

    def test_violations_sorted_by_line_number(self):
        code = '''
class Illegal1:  # Line 2
    pass

@export
def good_function():
    pass

from something import stuff  # Line 8

class Illegal2:  # Line 10
    pass
    '''

        c = ast.parse(code)
        violations = self.l.check(c)

        self.assertIsNotNone(violations)
        self.assertEqual(len(violations), 5)

        line_numbers = [int(v.split(':')[0].split()[1]) for v in violations]
        

        self.assertEqual(line_numbers, sorted(line_numbers))

        self.assertTrue(violations[0].startswith('Line 2'))  # No export decorator
        self.assertTrue(violations[1].startswith('Line 2'))  # First class definition
        self.assertTrue(violations[2].startswith('Line 9'))  # ImportFrom
        self.assertTrue(violations[3].startswith('Line 11'))  # Second class definition
        self.assertTrue(violations[4].startswith('Line 11'))  # Second class definition

