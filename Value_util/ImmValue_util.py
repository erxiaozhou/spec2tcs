from .ImmValue import ImmValue
from .valueType import valueType
from extract_binary_inst import binEncoding


u32_imms = ['dataidx', 'elemidx', 'funcidx',
            'globalidx', 'localidx', 'tableidx', 'memarg_offset', 'memarg_align', 'labelidx']
u8_imms = ['byte', 'laneidx']


def generate_val_for_one_imm(imm_name, imm_encoding):
    assert isinstance(imm_encoding, binEncoding)
    if imm_encoding.num > 1:
        assert imm_encoding.num == 16 and imm_encoding.attr in ('laneidx', 'byte'), print(imm_encoding)
        val = ImmValue(imm_name, valueType('v128'), 'v128')
        val.simd_lane_num = imm_encoding.num
    else:
        imm_type_str = imm_encoding.attr
        if imm_encoding.attr in u32_imms:
            val =  ImmValue(imm_name, valueType('u32'), imm_type_str)
        elif imm_type_str in u8_imms + ['reftype', 'vec(valtype)']:
            val = ImmValue(imm_name, valueType('u8'), imm_type_str)
        elif imm_type_str in ['i32', 'i64', 'f32', 'f64']:
            val = ImmValue(imm_name, valueType(imm_type_str), imm_type_str)
        elif imm_type_str == 'typeidx':
            assert 0
        elif imm_type_str == 'blocktype':
            val = ImmValue(imm_name, valueType('blocktype'), imm_type_str)
        elif imm_type_str == 'instr':
            val = ImmValue(imm_name, valueType('instr'), imm_type_str)
        else:
            raise Exception('unknown imm_type_str: {}'.format(imm_type_str))
    val.generate_svalue()
    return val
