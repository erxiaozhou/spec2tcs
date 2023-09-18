
from random import randint
from Value_util import Value
from Value_util import ImmValue
from se_inst_env_util.se_inst_encoding_util import generate_random_encoding_for_imm, generate_encoding_for_one_ty
from value_encoder import candidate_values


def generate_random_vals(stack_vals, imm_vals, val_num):
    # check_type
    for v in stack_vals:
        assert isinstance(v, Value)
    for v in imm_vals:
        assert isinstance(v, ImmValue)
    # 
    stack_concrete_vals = []
    for v in stack_vals:
        ty_str = v.type._type
        print(v)
        if v.type._type == 'other' and v.type.detail_info == 'reference value':
            assert 0
            concrete_vals = candidate_values.from_raw_data_list('ref_null',  [randint(0, 2**32-1) for i in range(val_num)], add_special=False)
        elif v.type._type == 'any':
            concrete_vals = generate_encoding_for_one_ty('i32', val_num, add_special=False)
        else:
            concrete_vals = generate_encoding_for_one_ty(ty_str, val_num, add_special=False)
        stack_concrete_vals.append(concrete_vals)
    #
    imm_concrete_vals = []
    for v in imm_vals:
        concrete_vals = generate_random_encoding_for_imm(v, val_num, add_sepcial=False)
        imm_concrete_vals.append(concrete_vals)
    return stack_concrete_vals, imm_concrete_vals
