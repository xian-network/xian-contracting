import ast
import sys

from .. import constants

from ..compilation.whitelists import (
    ALLOWED_AST_TYPES,
    ALLOWED_ANNOTATION_TYPES,
    VIOLATION_TRIGGERS,
    ILLEGAL_BUILTINS,
    ILLEGAL_AST_TYPES
)


class Linter(ast.NodeVisitor):

    def __init__(self):
        self._violations = []
        self._functions = []
        self._is_one_export = False
        self._is_success = True
        self._constructor_visited = False
        self.orm_names = set()
        self.visited_args = set()
        self.return_annotation = set()
        self.arg_types = set()

        self.builtins = list(set(list(sys.stdlib_module_names) + list(sys.builtin_module_names)))

    def ast_types(self, t, lnum):
        if type(t) not in ALLOWED_AST_TYPES:
            str = "Line {}".format(lnum) + " : " + VIOLATION_TRIGGERS[0] + " : {}" .format(type(t).__name__)
            self._violations.append(str)
            self._is_success = False

    def not_system_variable(self, v, lnum):
        if v.startswith('_') or v.endswith('_'):
            str = "Line {} : ".format(lnum) + VIOLATION_TRIGGERS[1] + " : {}" .format(v)
            self._violations.append(str)
            self._is_success = False

    def no_nested_imports(self, node):
        for item in node.body:
            if type(item) in [ast.ImportFrom, ast.Import]:
                str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[2]
                self._violations.append(str)
                self._is_success = False

    def visit_Name(self, node):
        self.not_system_variable(node.id, node.lineno)

        if node.id == 'rt':# or node.id == 'Hash' or node.id == 'Variable':
            self._is_success = False
            str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[13]
            self._violations.append(str)

        if node.id in ILLEGAL_BUILTINS and node.id != 'float':
            self._is_success = False
            str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[13]
            self._violations.append(str)

        self.generic_visit(node)
        return node

    def visit_Attribute(self, node):
        self.not_system_variable(node.attr, node.lineno)
        if node.attr == 'rt':
            self._is_success = False
            str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[13]
            self._violations.append(str)
        self.generic_visit(node)
        return node

    def visit_Import(self, node):
        for n in node.names:
            if n.name in self.builtins:
                self._is_success = False
                str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[13]
                self._violations.append(str)
        return node

    def visit_ImportFrom(self, node):
        str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[3]
        self._violations.append(str)
        self._is_success = False

    # TODO: Why are we even doing any logic instead of just failing on visiting these?
    def visit_ClassDef(self, node):
        str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[5]
        self._violations.append(str)
        self._is_success = False
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[6]
        self._violations.append(str)

        self._is_success = False
        self.generic_visit(node)
        return node

    def visit_Assign(self, node):
        # resource_names, func_name = Assert.valid_assign(node, Parser.parser_scope)
        if isinstance(node.value, ast.Name):
            if node.value.id == 'Hash' or node.value.id == 'Variable' or node.value.id == 'LogEvent':
                self._is_success = False
                str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[13]
                self._violations.append(str)

        if (isinstance(node.value, ast.Call) and not
            isinstance(node.value.func, ast.Attribute) and
            node.value.func.id in constants.ORM_CLASS_NAMES):

            if node.value.func.id in ['Variable', 'Hash', 'LogEvent']:
                kwargs = [k.arg for k in node.value.keywords]
                if 'contract' in kwargs or 'name' in kwargs:
                    self._is_success = False
                    str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[10]
                    self._violations.append(str)
            if ast.Tuple in [type(t) for t in node.targets] or isinstance(node.value, ast.Tuple):
                self._is_success = False
                str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[11]
                self._violations.append(str)
            try:
                self.orm_names.add(node.targets[0].id)
            except AttributeError:
                pass

        self.generic_visit(node)

        return node

    def visit_AugAssign(self, node):
        # TODO: Checks here?
        self.generic_visit(node)
        return node

    def visit_Call(self, node: ast.Call):
        # Prevent calling of illegal builtins
        if isinstance(node.func, ast.Name):
            if node.func.id in ILLEGAL_BUILTINS:
                self._is_success = False
                str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[13]
                self._violations.append(str)

        self.generic_visit(node)
        return node

    def generic_visit(self, node):
        # Prevent calling of illegal builtins

        if type(node) in ILLEGAL_AST_TYPES:
            self._is_success = False
            s = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[0]
            self._violations.append(s)

        return super().generic_visit(node)

    def visit_Num(self, node):
        # NOTE: Integers are important for indexing and slicing so we cannot replace them.
        # They also will not suffer from rounding issues.
        # TODO: are any types we don't allow right now?
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        self.no_nested_imports(node)

        # Make sure there are no closures
        try:
            for n in node.body:
                if isinstance(n, ast.FunctionDef):
                    str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[18]
                    self._violations.append(str)
                    self._is_success = False
        except:
            pass

        # Only allow 1 decorator per function definition.
        if len(node.decorator_list) > 1:
            str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[9] + \
                  ": Detected: {} MAX limit: 1".format(len(node.decorator_list))
            self._violations.append(str)
            self._is_success = False
        export_decorator = False
        for d in node.decorator_list:
            if hasattr(d, "id"):
                # Only allow decorators from the allowed set.
                if d.id not in constants.VALID_DECORATORS:
                    str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[7] + \
                        ": valid list: {}".format(constants.VALID_DECORATORS)
                    self._violations.append(str)
                    self._is_success = False

                if d.id == constants.EXPORT_DECORATOR_STRING:
                    self._is_one_export = True
                    export_decorator = True

                if d.id == constants.INIT_DECORATOR_STRING:
                    if self._constructor_visited:
                        str = "Line {}: ".format(node.lineno) + VIOLATION_TRIGGERS[8]
                        self._violations.append(str)
                        self._is_success = False
                    self._constructor_visited = True

        # Add argument names to set to make sure that no ORM variable names are being reused in function def args
        arguments = node.args
        for a in arguments.args:
            self.visited_args.add((a.arg, node.lineno))
            if export_decorator:
                if a.annotation is not None:
                    try:
                        self.arg_types.add((a.annotation.id, node.lineno))
                    except AttributeError:
                        arg = a.annotation.value.id + '.' + a.annotation.attr
                        self.arg_types.add((arg, node.lineno))
                else:
                    self.arg_types.add((None, node.lineno))

        if export_decorator:
            if node.returns is not None:
                try:
                    self.arg_types.add((a.annotation.id, node.lineno))
                except AttributeError:
                    arg = a.annotation.value.id + '.' + a.annotation.attr
                    self.arg_types.add((arg, node.lineno))
            else:
                self.return_annotation.add((None, node.lineno))

        self.generic_visit(node)
        return node

    def annotation_types(self, t, lnum):
        if t is None:
            str = "Line {}".format(lnum) + " : " + VIOLATION_TRIGGERS[16]
            self._violations.append(str)
            self._is_success = False
        elif t not in ALLOWED_ANNOTATION_TYPES:
            str = "Line {}".format(lnum) + " : " + VIOLATION_TRIGGERS[15] + " : {}" .format(t)
            self._violations.append(str)
            self._is_success = False

    def check_return_types(self, t, lnum):
        if t is not None:
            str = "Line {}".format(lnum) + " : " + VIOLATION_TRIGGERS[17] + " : {}" .format(t)
            self._violations.append(str)
            self._is_success = False

    def _reset(self):
        self._violations = []
        self._functions = []
        self._is_one_export = False
        self._is_success = True
        self._constructor_visited = False
        self.orm_names = set()
        self.visited_args = set()
        self.return_annotation = set()
        self.arg_types = set()

    def _final_checks(self):
        for name, lineno in self.visited_args:
            if name in self.orm_names:
                str = "Line {}: ".format(lineno) + VIOLATION_TRIGGERS[14]
                self._violations.append(str)
                self._is_success = False

        if not self._is_one_export:
            str = "Line {}: ".format(lineno) + VIOLATION_TRIGGERS[12]
            self._violations.append(str)
            self._is_success = False

        for t, lineno in self.arg_types:
            self.annotation_types(t,lineno)

        for t, lineno in self.return_annotation:
            self.check_return_types(t,lineno)

    def _collect_function_defs(self, root):
        for node in ast.walk(root):
            if isinstance(node, ast.FunctionDef):
                self._functions.append(node.name)
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                for n in node.names:
                    if n.asname:
                        self._functions.append(n.asname)
                    else:
                        self._functions.append(n.name.split('.')[-1])

    def check(self, ast_tree):
        self._reset()
        # pass 1 - collect function def and imports
        self._collect_function_defs(ast_tree)
        self.visit(ast_tree)
        self._final_checks()
        if self._is_success is False:
            return sorted(self._violations, key=lambda x: int(x.split(':')[0].split()[1]))
        else:
            return None

    def dump_violations(self):
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self._violations)
