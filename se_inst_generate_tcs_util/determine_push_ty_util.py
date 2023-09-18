import random
from value_encoder import value_holder


def determine_push_ty(template_config, inst_name, inferred_push_ty, cur_stack_vs, cur_imm_vs):
    if inst_name == 'call':
        push_ty = 'i32'
    elif inst_name in ['br', 'return']:
        push_ty = 'i32'
    elif inferred_push_ty == 'any':
        if inst_name in ['select', 'select_1C~t']: 
            push_ty = infer_push_ty_for_select(cur_stack_vs)
        elif len(cur_imm_vs) == 1:
            push_ty = infer_push_py_for_imm_idx(template_config, cur_imm_vs)
    else:
        push_ty = inferred_push_ty
    if inst_name == 'ref.null':
        push_ty = infer_push_ty_for_ref_null(cur_imm_vs)
    return push_ty


def infer_push_ty_for_ref_null(cur_imm_vs):
    if cur_imm_vs[0].constant == 0x70:
        push_ty = 'funcref'
    elif cur_imm_vs[0].constant == 0x6F:
        push_ty = 'externref'
    else:
        assert 0, print(cur_imm_vs[0].constant)
    return push_ty


def infer_push_ty_for_select(cur_stack_vs):
    if len(cur_stack_vs) == 1:
        push_ty = cur_stack_vs[0].type_str
    elif cur_stack_vs[0].constant == 0:
        push_ty = cur_stack_vs[2].type_str
    else:
        push_ty = cur_stack_vs[1].type_str
    return push_ty


def infer_push_py_for_imm_idx(template_config, cur_imm_vs):
    vh = cur_imm_vs[0]
    assert isinstance(vh, value_holder)
    type_str = vh.type_str
    assert type_str in ['globalidx', 'localidx', 'tableidx']
    if type_str == 'tableidx':
        push_ty = 'funcref'
    else:
        constant_idx = vh.constant
        if type_str == 'globalidx':
            ty_relation = template_config['global_type']
        elif type_str =='localidx':
            ty_relation = template_config['local_type']
        if constant_idx < len(ty_relation):
            push_ty = ty_relation[constant_idx]
        else:
            push_ty = random.choice(ty_relation)
    return push_ty
