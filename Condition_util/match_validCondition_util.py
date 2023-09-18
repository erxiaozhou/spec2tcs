import re
from Value_util import constantValue
from Value_util import StackValue
from Value_util import generate_Value_from_common_line
from Value_util import FormulaValue
from process_text import unwrap_math, raw_processor, process_char_bracket_fmt
from .match_Condition_util import extract_bool
from Value_util import constType
from Value_util import StackValue
from Value_util import valueType
from Value_util.ValueFactory import _is_val_ref_name

_type_sgs = ['\\V128', '\\I32', '\\I64', '\\F32', '\\F64',  '\\FUNCREF', '\\EXTERNREF']


def match_must_ty_direct_cond(line):
    elems = []
    p = re.compile(r'^:math:`\[(.*?)\] \\to \[(.*?)\]`$')
    r = p.findall(line)
    if r:
        r = r[0]
        input_str = r[0]
        output_str = r[1]
        elems.append('inst_ty_direct_cond')
        input_ty_strs = [x for x in input_str.split('~') if x]
        output_ty_strs = [x for x in output_str.split('~') if x]
        input_vals = [_ty_str2val(ty_str) for ty_str in input_ty_strs]
        output_vals = [_ty_str2val(ty_str) for ty_str in output_ty_strs]
        elems.append(input_vals)
        elems.append(output_vals)
    return elems


def match_must_ty_from_store_cond(line):
    elems = []
    p = re.compile(r'^(:math:`[^\[][^,]*\[.\]`)$')
    r = p.findall(line)
    if r:
        elems.append('inst_ty_direct_cond')
        val = generate_Value_from_common_line(r[0])
        elems.append(val)
    return elems

def match_must_ty_infered_cond(line):
    elems = []
    p = re.compile(r'^:math:`\[(.*?)\] \\to \[(.*?)\]`,')
    r = p.findall(line)
    assert r

    r = r[0]
    input_str = r[0]
    output_str = r[1]
    input_ty_strs = [x for x in input_str.split('~') if x]
    output_ty_strs = [x for x in output_str.split('~') if x]

    type_part = re.compile(r"(?<=for\s)(?!that\b)[\s\S]+?(?=\bthat\b|$)").findall(line)[0]
    types = re.compile(r':ref:`(.*? type)[^`]*`').findall(type_part)
    refered_ty_str_p = re.compile(r':math:`([^`]*?)`')
    is_seq = 'any sequence' in type_part
    referred_ty_strs = refered_ty_str_p.findall(type_part)
    assert len(types) == 1
    types = types[0]
    input_vals = [_ty_str2val(ty_str) for ty_str in input_ty_strs]
    output_vals = [_ty_str2val(ty_str) for ty_str in output_ty_strs]
    elems = ['inst_ty_infered_cond', 
             input_vals,
             output_vals,
             is_seq,
             types,
             referred_ty_strs
             ]
    return elems

def _ty_str2val(ty_str):
    if ty_str in _type_sgs:
        ty_str = process_char_bracket_fmt(raw_processor._process_macro(ty_str))
        ty = valueType(ty_str)
    elif _is_val_ref_name(ty_str):
        ty = valueType('any', type_sig=ty_str)
    else:
        ty =  valueType('other', 'type', ty_str)
    val = StackValue('any', ty)
    return val
