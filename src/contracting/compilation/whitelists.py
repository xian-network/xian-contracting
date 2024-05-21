import ast, builtins

ALLOWED_BUILTINS = {'Exception', 'False', 'None', 'True', 'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray',
                    'bytes', 'chr', 'dict', 'divmod', 'filter', 'format', 'frozenset', 'hex', 'int', 'isinstance',
                    'issubclass', 'import', 'len', 'list', 'map', 'max', 'min', 'oct', 'ord', 'pow', 'range', 'reversed',
                    'round', 'set', 'sorted', 'str', 'sum', 'tuple', 'zip'}

ILLEGAL_BUILTINS = set(dir(builtins)) - ALLOWED_BUILTINS

ALLOWED_AST_TYPES = {ast.Module, ast.Eq, ast.Call, ast.Dict, ast.Attribute, ast.Pow, ast.Index, ast.Not, ast.alias,
                     ast.If, ast.FunctionDef, ast.Global, ast.GtE, ast.LtE, ast.Load, ast.arg, ast.Add, ast.Import,
                     ast.ImportFrom, ast.Name, ast.Num, ast.BinOp, ast.Store, ast.Assert, ast.Assign, ast.AugAssign,
                     ast.Subscript, ast.Compare, ast.Return, ast.NameConstant, ast.Expr, ast.keyword, ast.Sub,
                     ast.arguments, ast.List, ast.Set, ast.Str, ast.UnaryOp, ast.Pass, ast.Tuple, ast.Div, ast.In,
                     ast.NotIn, ast.Gt, ast.Lt, ast.Starred, ast.Mod, ast.NotEq, ast.For, ast.While, ast.ListComp,
                     ast.comprehension, ast.Slice, ast.USub, ast.BoolOp, ast.And, ast.Or, ast.Mult, ast.IsNot, ast.Is, ast.Constant}

ILLEGAL_AST_TYPES = {
    ast.AsyncFor,
    ast.AsyncFunctionDef,
    ast.AsyncWith,
    ast.Await,
    ast.ClassDef,
    ast.Ellipsis,
    ast.GeneratorExp,
    ast.Global,
    ast.ImportFrom,
    ast.Interactive,
    ast.Lambda,
    ast.MatMult,
    ast.Nonlocal,
    ast.Suite,
    ast.Try,
    ast.With,
    ast.Yield,
    ast.YieldFrom,
}

ALLOWED_ANNOTATION_TYPES = {'dict', 'list', 'str', 'int', 'float', 'bool', 'datetime.timedelta', 'datetime.datetime', 'Any'}

VIOLATION_TRIGGERS = [
    "S1- Illegal contracting syntax type used",
    "S2- Illicit use of '_' before variable",
    "S3- Illicit use of Nested imports",
    "S4- ImportFrom compilation nodes not yet supported",
    "S5- Contract not found in lib",
    "S6- Illicit use of classes",
    "S7- Illicit use of Async functions",
    "S8- Invalid decorator used",
    "S9- Multiple use of constructors detected",
    "S10- Illicit use of multiple decorators",
    "S11- Illicit keyword overloading for ORM assignments",
    "S12- Multiple targets to ORM definition detected",
    "S13- No valid contracting decorator found",
    "S14- Illegal use of a builtin",
    "S15- Reuse of ORM name definition in a function definition argument name",
    "S16- Illegal argument annotation used",
    "S17- No valid argument annotation found",
    "S18- Illegal use of return annotation",
    "S19- Illegal use of a nested function definition."
]
