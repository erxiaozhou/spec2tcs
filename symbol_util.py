import claripy
ref_null_constant = 0
type_str2val = {
    'i32': 0,
    'i64': 1,
    'f32': 2,
    'f64': 3,
    'v128': 4,
    'ref': 5,
    'ref_null':6
}


val2type_str = [
    'i32',
    'i64',
    'f32',
    'f64',
    'v128',
    'ref',
    'ref_null'
]

type_combination = {
    'reference type': ['ref', 'ref_null'],
    'value type': val2type_str[:],
    'operand type': ['i32', 'i64', 'f32', 'f64', 'v128']
}

def get_ty_combination_constraint(combination_type, symbol):
    assert combination_type in type_combination
    ty_strs = type_combination[combination_type]
    constraints = []
    for ty_str in ty_strs:
        constraints.append(symbol == type_str2val[ty_str])
    is_unconstrained = (len(val2type_str) == len(ty_strs))
    return claripy.Or(*constraints), is_unconstrained


def get_traditional_type(ty, name):
    type_str = ty._type
    self_constraints = []
    # value
    assert type_str != 'ref'
    assert type_str != 'i128'
    if type_str in ['i32', 'i64', 'f32', 'f64', 'v128']:
        if type_str in ['i32', 'i64']:
            v_value = claripy.BVS(name, 64)
            if type_str == 'i32':
                self_constraints.append(v_value < 2 ** 32)
        elif type_str == 'f32':
            v_value = claripy.FPS(name, claripy.FSORT_FLOAT)
        elif type_str == 'f64':
            v_value = claripy.FPS(name, claripy.FSORT_DOUBLE)
        elif type_str == 'v128':
            v_value = claripy.BVS(name, 128)
    elif type_str == 'other' and ty.detail_info == 'reference value':
        v_value = claripy.BVS(name, 64)
    else:
        v_value = 'any'
    # type
    if type_str in type_str2val:
        vt_value = type_str2val[type_str]
    elif (type_str == 'any') or (type_str == 'other' and ty.detail_info == 'reference value'):
        vt_value = claripy.BVS(name+'ty', 4)
    else:
        raise Exception('Unexpected situation')
    return v_value, self_constraints, vt_value
