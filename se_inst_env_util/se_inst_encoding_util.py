import random
from random import randint
from Value_util import ImmValue
from .get_random_value_util import generate_value_by_type_str
from value_encoder import candidate_values
from Value_util import u8_imms
from random import choices


def generate_encoding_for_one_ty(ty_str, val_num, add_special=True):
    assert isinstance(ty_str, str), print(ty_str)
    if ty_str in ['i32', 'f32', 'f64', 'i64', 'v128']:
        random_vals = [generate_value_by_type_str(ty_str) for i in range(val_num)]
    elif ty_str == 'ref':
        random_vals = [randint(0, 1024) for i in range(val_num)]
    elif ty_str == 'ref_null':
        random_vals = [0x70, 0x6F]
        if val_num < 2:
            random_vals = choices(random_vals, k=val_num)
    else:
        assert 0, print(ty_str)

    vals = candidate_values.from_raw_data_list(ty_str, random_vals, add_special=add_special)
    return vals


def generate_random_encoding_for_imm(val, val_num, add_sepcial=True, template_config_for_special_val=None):
    assert isinstance(val, ImmValue), print(val)
    if val.type._type in ['i32', 'i64', 'f32', 'f64', 'v128']:
        val = generate_encoding_for_one_ty(val.type._type, val_num, add_special=add_sepcial)
        return val
    elif val.imm_type == 'u8':
        random_ints =  [randint(0, 255) for i in range(val_num)]
        val = candidate_values.from_raw_data_list(val.imm_type, random_ints, add_special=add_sepcial)
        return val
    elif val.imm_type in u8_imms:
        random_ints =  [randint(0, 255) for i in range(val_num)]
        val = candidate_values.from_raw_data_list(val.imm_type, random_ints, add_special=add_sepcial)
        return val
    elif val.imm_type == 'reftype':
        random_ints =  [random.choice([0x70, 0x6F]) for i in range(val_num)]
        val = candidate_values.from_raw_data_list(val.imm_type, random_ints, add_special=add_sepcial)
        return val
    elif val.imm_type == 'vec(valtype)':
        random_ints =  [random.choice([0x70, 0x6F, 0x7B, 0x7C, 0x7D, 0x7E, 0x7F]) for i in range(val_num)]
        val = candidate_values.from_raw_data_list(val.imm_type, random_ints, add_special=add_sepcial)
        return val
    elif val.type._type == 'u32':
        random_ints = [randint(0, 2**32-1) for i in range(val_num)]
        val = candidate_values.from_raw_data_list(val.imm_type, random_ints, add_special=add_sepcial, template_config_for_special_val=template_config_for_special_val)
        return val
    elif val.type._type == 'blocktype':
        val = candidate_values.from_blocktype_raw_list([val], add_special=add_sepcial)
        return val
    elif val.type._type == 'instr':
        val = candidate_values.from_blocktype_raw_list([val], add_special=add_sepcial)
        return val
    else:
        assert 0, print(val.imm_type, val, val.type._type)
