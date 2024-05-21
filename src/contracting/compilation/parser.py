import ast


def methods_for_contract(contract_code: str):
    tree = ast.parse(contract_code)

    function_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

    funcs = []
    for definition in function_defs:
        func_name = definition.name

        if func_name.startswith('__'):
            continue

        kwargs = []

        for arg in definition.args.args:
            try:
                a = arg.annotation.id
            except AttributeError:
                a = arg.annotation.value.id + '.' + arg.annotation.attr

            kwargs.append({
                'name': arg.arg,
                'type': a
            })

        funcs.append({'name': func_name, 'arguments': kwargs})

    return funcs


def variables_for_contract(contract_code: str):
    tree = ast.parse(contract_code)

    assigns = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            assigns.append(node)

        if isinstance(node, ast.FunctionDef):
            break

    variables = []
    hashes = []

    for assign in assigns:
        if type(assign.value) == ast.Call:
            if assign.value.func.id == 'Variable':
                variables.append(assign.targets[0].id.lstrip('__'))
            elif assign.value.func.id == 'Hash':
                hashes.append(assign.targets[0].id.lstrip('__'))

    return {
        'variables': variables,
        'hashes': hashes
    }
