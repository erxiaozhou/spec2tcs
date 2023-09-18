import re
from file_util import group_ps
from Value_util import valueType
from process_text import process_char_bracket_fmt, raw_processor, unwrap_math

_type_sgs = ['\\V128', '\\I32', '\\I64', '\\F32', '\\F64']


def get_name_type_from_p(content):
    content = content.rstrip('.')
    ty = None
    name = None
    num = 1
    idx = None
    # example: :math:`\\I32.\\CONST~i`
    ty, name = match_value_from_math(content)
    # p1.1
    # example: :math:`\\unop_t(c_1)`
    if not type_and_name_determined(ty, name):
        ty, name = match_value_from_notv_op_math(content)
    # p1.2
    # example: :math:`\\vvbinop_{\\I128}(c_1, c_2)`
    if not type_and_name_determined(ty, name):
        ty, name = match_value_from_v_op_math(content)
    if not type_and_name_determined(ty, name):
        ty, name = match_cvtop_math(content)
    # 1.3
    if not type_and_name_determined(ty, name):
        ty, name = match_value_from_ref_op_math(content)
    # 1.7
    if not type_and_name_determined(ty, name):
        ty, name = match_value_from_bool_math(content)
    # 1.8
    if not type_and_name_determined(ty, name):
        ty, name = match_ine_math(content)
    # p2
    if not type_and_name_determined(ty, name):
        ty, name, num = math_value_from_val_math(content)
    # p3
    if not type_and_name_determined(ty, name):
        ty, name = match_the_label(content)

    if not type_and_name_determined(ty, name):
        ty, name = match_single_nonmath(content)
    # p4.1
    if not type_and_name_determined(ty, name):
        ty, name = match_function_describe_math(content)
    # p4.3
    if not type_and_name_determined(ty, name):
        ty, name, num = match_cur_frame_describe_math(content)
    # example: the :ref:`global address <syntax-globaladdr>` :math:`F.\\AMODULE.\\MIGLOBALS[x]`
    if not type_and_name_determined(ty, name):
        ty, name = match_value_from_ref_math(content)
    # p4.5
    if not type_and_name_determined(ty, name):
        ty, name = match_concatenation_describe_math(content)
    # example: the type :math:`\\unpacked(\\shape)`
    if not type_and_name_determined(ty, name):
        ty, name = match_type_unpacked_math(content)
    # p8
    # p9 length
    if not type_and_name_determined(ty, name):
        ty, name = match_value_from_length_pattern(content)
    # p11 example: the integer :math:`\\dim(\\shape)`
    if not type_and_name_determined(ty, name):
        ty, name = match_value_from_integer_math(content)
    # p11 memory which
    if not type_and_name_determined(ty, name):
        ty, name = match_value_from_for_which_pattern(content)
    # p12
    if not type_and_name_determined(ty, name):
        ty, name = match_element_math(content)
    if not type_and_name_determined(ty, name):
        ty, name = match_bytes_math(content)
    if not type_and_name_determined(ty, name):
        ty, name = match_value_from_arity_pattern(content)
    # p7
    if not type_and_name_determined(ty, name):
        ty, name = match_value_from_lanes_math(content)
    # example:
    if not type_and_name_determined(ty, name):
        ty, name = match_non_math_sg(content)
    if not type_and_name_determined(ty, name):
        ty, name, num = match_num_type_pattern(content)
    if not type_and_name_determined(ty, name):
        ty, name, num = match_value_with_ref_pattern(content)
    if not type_and_name_determined(ty, name):
        ty, name, num = match_num_ref_pattern(content)
    # p4.2
    if not type_and_name_determined(ty, name):
        ty, name = match_sequence_extend_math(content)
    if not type_and_name_determined(ty, name):
        ty, name = match_common_math(content)
    # p4.6
    if not type_and_name_determined(ty, name):
        ty, name, num, idx = match_label_idx_pattern(content)
    # p 5.1
    if not type_and_name_determined(ty, name):
        ty, name = math_type_pattern(content)
    # p 5.2
    if not type_and_name_determined(ty, name):
        ty, name = match_mutability_pattern(content)
    # p 5.3
    if not type_and_name_determined(ty, name):
        ty, name = match_special_macro(content)
    # p 5.4
    if not type_and_name_determined(ty, name):
        ty, name = match_context_pattern(content)
    # p 5.5
    if not type_and_name_determined(ty, name):
        ty, name = match_value_from_type_of_pattern(content)
    assert name is not None, print('-{}-'.format(content))
    assert ty is not None, print('-{}-'.format(content))
    if num is None:
        num = 1
    return (name, ty, num, idx)


def detect_number(content):
    number_strs = ['a', 'an', 'one', 'two', 'three']
    p_start = group_ps(('^', ' '))
    p_end = group_ps((' ', '$'))
    p_center = group_ps(number_strs, just_search=False)
    p = ''.join((p_start, p_center, p_end))
    r = re.compile(p).findall(content)
    number = None
    if r:
        number = r[0]
        number = get_int_from_str(number)
    return number


def get_int_from_str(number_str):
    number_str = number_str.lower()
    _relation = {
        'a': 1,
        'an': 1,
        'one': 1,
        'two': 2,
        'three': 3,
    }
    return _relation[number_str]


def infer_type_from_ref(content):
    ty = None
    p = r'^:ref:`(.*?) *<syntax\-.*?>`$'
    r = re.compile(p).findall(content)
    if r:
        ty = valueType(_type='other', detail_info=r[0])
    return ty


def _process_type_content(content):
    content = raw_processor._process_macro(content)
    content = process_char_bracket_fmt(content)
    return content


def _process_type(type_content):
    type_content = process_char_bracket_fmt(type_content)
    ori_type_content = type_content
    if type_content.startswith('t'):
        ty = valueType('any', type_sig=type_content)
    elif type_content in _type_sgs + valueType.legal_types:
        type_content = _process_type_content(type_content)
        ty = valueType(type_content)
    elif re.search(r'\|.*\|', type_content):
        type_content = type_content.strip('|').lower()
        assert type_content in valueType.numeric_v_types
        ty = valueType(type_content)
    else:
        raise ValueError('No match: -{}-'.format(ori_type_content))
    return ty


def type_and_name_determined(ty, name):
    if ty is None:
        return False
    if name is None:
        return False
    return True


def match_value_from_math(content):
    p = r'^:math:`(.*?)\.\\+V?CONST~(.*)`$'
    r = re.compile(p).findall(content)
    ty = None
    name = None
    if r:
        r = r[0]
        ty_part = r[0]
        name = r[1]
        ty = _process_type(ty_part)
    else:
        p = r':math:`(.*?)\.\\[A-Z]\{const\}~(.*)`$'
        r = re.compile(p).findall(content)
        if r:
            r=r[0]
            ty = _process_type(r[0])
            name = r[1]

    return (ty, name)


def match_value_from_notv_op_math(content):
    ty = None
    name = None
    p = r'^:math:`\\[^v][a-z]+?op_(.*?)\(.*?\)`$'
    r = re.compile(p).findall(content)
    if r:
        ty = _process_type(r[0])
        name = unwrap_math(content, True)
    else:
        p = r':math:`\\[A-Z]\{[^v][a-z]+op\}_(.*?)\(.*?\)`$'
        # p = r':math:`\\[A-Z]\{[^v].+?\}_(.*?)\(.*?\)`$'
        r = re.compile(p).findall(content)
        if r:
            ty = _process_type(r[0])
            name = unwrap_math(content, True)
    return (ty, name)


def match_value_from_v_op_math(content):
    ty = None
    name = None
    p = r'^:math:`\\v[a-z]+?op_(.*?)\(.*?\)`$'
    r = re.compile(p).findall(content)
    if r:
        matched_type = _process_type_content(r[0])
        ty = valueType(_type='v128', detail_info=matched_type)
        name = unwrap_math(content, True)
    else:
        p = r'^:math:`\\[A-Z]\{v[a-z]+op\}_(.*?)\(.*?\)`$'
        r = re.compile(p).findall(content)
        if r:
            matched_type = _process_type_content(r[0])
            ty = valueType(_type='v128', detail_info=matched_type)
            name = unwrap_math(content, True)
    return (ty, name)


def match_cvtop_math(content):
    ty = None
    name = None
    p = r'^:math:`\\v?cvtop.*?_[\{\(].*?, *(.*)[\)\}]\(.*\)`$'
    r = re.compile(p).findall(content)
    if r:
        name = unwrap_math(content, True)
        ty = valueType('any', type_sig=r[0].strip('|'))
    else:
        p = r'^:math:`\\[A-Z]\{v?cvtop\}.*?_[\{].*?, *(.*)[\}]\(.*\)`$'
        r = re.compile(p).findall(content)
        if r:
            name = unwrap_math(content, True)
            ty = valueType('any', type_sig=r[0].strip('|'))
    return (ty, name)


def match_value_from_ref_op_math(content):
    ty = None
    name = None
    p = r'^:math:`\\REFNULL~(.+)`$'
    r = re.compile(p).findall(content)
    if r:
        ty = valueType(_type='ref', detail_info='ref_null')
        name = r[0]
    else:
        p = r'^:math:`\\REFFUNCADDR~(.+)`$'
        r = re.compile(p).findall(content)
        if r:
            ty = valueType(_type='ref', detail_info='ref_func')
            name = r[0]
    return (ty, name)


def math_value_from_val_math(content):
    ty = None
    name = None
    num = 1
    content = re.sub(r'^the values? ', '', content)
    content = re.sub(r'^the results? ', '', content)
    p = r'^:math:`(\\val[0-9a-z_]*)`$'
    r = re.compile(p).findall(content)
    if r:
        ty = valueType.generate_any_ty()
        name = r[0]
    else:
        p = r'^:math:`(\\val[0-9a-z_]*)\^(.+)`$'
        r = re.compile(p).findall(content)
        if r:
            ty = valueType.generate_any_ty()
            name = r[0][0]
            num = r[0][1]
    return (ty, name, num)


def match_value_from_integer_math(content):
    ty = None
    name = None
    p = r'^the integer :math:`(.*)`$'
    r = re.compile(p).findall(content)
    if r:
        ty = valueType(_type='i32')
        name = r[0]
    return (ty, name)


def match_value_from_lanes_math(content):
    ty = None
    name = None
    p = r'^(?:the sequence )?:math:`(\\lanes.*)`$'
    r = re.compile(p).findall(content)
    if r:
        ty = valueType(_type='other', detail_info='byte_seq')
        name = r[0]
    return (ty, name)


def match_value_from_arity_pattern(content):
    ty = None
    name = None
    if content.startswith('the arity'):
        ty = valueType('i32', detail_info='arity')
        name = content
    return (ty, name)


def match_value_from_length_pattern(content):
    ty = None
    name = None
    p = r'^[tT]he length of.*?:math:`.*`'
    if re.search(p, content):
        ty = valueType('i32', 'length')
        name = content
    return (ty, name)


def match_value_from_ref_math(content):
    ty = None
    name = None
    p = r'^(?:[tT]he )? *(:ref:`.*? *<syntax\-.*?>`) (.*:math:`.*`)$'
    r = re.compile(p).findall(content)
    if r:
        r = r[0]
        name = r[1]
        if re.compile(r'^:math:`[^`]+`$').findall(name):
            name = unwrap_math(name, False)
        else:
            print(f'==== match_value_from_ref_math content: {content}')
        ty = infer_type_from_ref(r[0])
    return (ty, name)


def match_value_from_for_which_pattern(content):
    ty = None
    name = None
    p = r'^the ([^,]*?) for which :math:`(.*?)`$'
    r = re.compile(p).findall(content)
    if r:
        r = r[0]
        if 'integer' in r[0]:
            ty = valueType('i32', detail_info='for which')
        else:
            ty = valueType('any', detail_info='for which')
        name = r[1]
    return (ty, name)


def match_value_from_bool_math(content):
    ty = None
    name = None
    p = r'^:math:`(\\bool.*)`$'
    r = re.compile(p).findall(content)
    if r:
        name = r[0]
        ty = valueType('i32', detail_info='bool')
    return (ty, name)


def match_the_label(content):
    ty = None
    name = None
    p = r'^the label (whose .*)$'
    if content == 'the label':
        name = 'any'
        ty = valueType('other', 'label')
    elif re.search(p, content):
        name = re.compile(p).findall(content)[0]
        ty = valueType('other', 'label')
    else:
        p = r'^the label :math:`(.*)`'
        r = re.compile(p).findall(content)
        if r:
            ty = valueType('other', 'label')
            name = r[0]
    return(ty, name)


def match_single_nonmath(content):
    ty = None
    name = None
    if content == 'the value':
        name = 'any'
        ty = valueType.generate_any_ty()
    elif content == 'the top element':
        name = 'the top content'
        ty = valueType.generate_any_ty()
    elif content == 'the frame':
        name = 'any'
        ty = valueType('other', 'frame')
    return (ty, name)


def match_common_math(content):
    ty = None
    name = None
    # 'the |i32| value :math:`2^{32}-1`, for which :math:`\\signed_{32}(\\X{err})` is :math:`-1`'
    p = re.compile(r'^(?:the ?(.*?) value )?:math:`(.+?)`,?.*$')
    r = p.findall(content)
    if r:
        r = r[0]
        if len(r[0]):
            ty = _process_type(r[0])
        else:
            ty = valueType.generate_any_ty()
        name = r[1]
    return (ty, name)


def match_ine_math(content):
    ty = None
    name = None
    p = r'^:math:`(\\ine_.*)`$'
    r = re.compile(p).findall(content)
    if r:
        ty = valueType('v128')
        name = r[0]
    return (ty, name)


def match_element_math(content):
    ty = None
    name = None
    p = r'^the (element) :math:`(.*)`$'
    r = re.compile(p).findall(content)
    if r:
        r = r[0]
        ty = valueType('other', detail_info=r[0])
        name = r[1]
    return (ty, name)


def match_bytes_math(content):
    ty = None
    name = None
    p = r'^the (bytes? ?(?:sequence)?) :math:`(.*)`$'
    r = re.compile(p).findall(content)
    if r:
        r = r[0]
        ty = valueType('other', detail_info=r[0])
        name = r[1]
    return (ty, name)


def match_type_unpacked_math(content):
    ty = None
    name = None
    p = r'^the type :math:`(\\unpacked.*)`$'
    r = re.compile(p).findall(content)
    if r:
        name = 'any'
        ty = valueType('other', 'type', type_sig=r[0])
    return (ty, name)


def match_function_describe_math(content):
    ty = None
    name = None
    p = r'^the function instance at address :math:`(.*)`$'
    r = re.compile(p).findall(content)
    if r:
        name = r[0]
        ty = valueType('other', 'function instance')
    return (ty, name)


def match_concatenation_describe_math(content):
    ty = None
    name = None
    p = r'^the concatenation of the two sequences :math:`.*`$'
    r = re.compile(p).findall(content)
    if r:
        name = content
        ty = valueType(_type='other', detail_info='byte_seq')
    return (ty, name)


def match_cur_frame_describe_math(content):
    ty = None
    name = None
    num = 1
    p1 = r'^the :ref:`current <exec-notation-textual>` :ref:`frame <syntax-frame>`$'
    p2 = r'^(.*?) ?frame ?(?::math:(`.*`))?$'
    if re.search(p1, content):
        ty = valueType('other', 'frame')
        name = 'current frame'
    elif re.search(p2, content):
        r = re.compile(p2).findall(content)
        r = r[0]
        if len(r[1]):
            name = r[1]
        else:
            name = 'any'
        possible_number = detect_number(r[0])
        if possible_number is not None:
            num = possible_number
        ty = valueType('other', 'frame')
    return (ty, name, num)


def match_sequence_extend_math(content):
    ty = None
    name = None
    p = r'^the sequence :math:`(\\extend.*)`$'
    r = re.compile(p).findall(content)
    if r:
        ty = valueType(_type='other', detail_info='byte_seq')
        name = r[0]
    return (ty, name)


def match_non_math_sg(content):
    ty = None
    name = None
    p = r'^`(.*)`$'
    r = re.compile(p).findall(content)
    if r:
        ty = valueType.generate_any_ty()
        name = r[0]
    return (ty, name)


def match_value_with_ref_pattern(content):
    ty = None
    name = None
    num = None
    p = r'^(.*?)(?: more)? values? ?(?:(?:(?:with)|(?:of)) :ref:`[^`]+` *(.*))?$'
    r = re.compile(p).findall(content)
    if r:
        name = 'any'
        num_part, type_part = r[0]
        num = detect_number(num_part)
        if num is None:
            num = num_part
        type_part = unwrap_math(type_part)
        type_part = _process_type_content(type_part)
        if type_part == '':
            ty = valueType.generate_any_ty()
        else:
            ty = _process_type(type_content=type_part)
    return (ty, name, num)


def match_num_ref_pattern(content):
    ty = None
    name = None
    num = None
    p = r'^(.*) (:ref:`.*?`)$'
    r = re.compile(p).findall(content)
    if r:
        r = r[0]
        possible_number = detect_number(r[0])
        if possible_number is not None:
            name = 'any'
            ty = infer_type_from_ref(r[1])
            num = possible_number
    return (ty, name, num)


def match_num_type_pattern(content):
    ty = None
    name = None
    num = None
    p = r'^(.*) ((?:labels?)|(:ref:`.*`))$'
    r = re.compile(p).findall(content)
    if r:
        name = 'any'
        r = r[0]
        num = r[0]
        possible_number = detect_number(num)
        if possible_number is not None:
            num = possible_number

        if re.search(r'^labels?$', r[1]):
            ty = valueType('other', 'label')
        else:
            ty = infer_type_from_ref(r[1])
    return (ty, name, num)

def match_label_idx_pattern(content):
    ty = None
    name = None
    num = None
    idx = None
    # a reg expr to match s
    p = r'^the :math:`(l)`-th label appearing on the stack, .*$'
    r = re.compile(p).findall(content)
    if r:
        ty = valueType('other', 'label')
        name = 'any'
        num = 1
        idx = r[0]
    return (ty, name, num, idx)

def math_type_pattern(content):
    ty = None
    name = None
    p = r'^\|(.*)\|$'
    r = re.compile(p).findall(content)
    if r:
        r = r[0].lower()
        if r in valueType.legal_types:
            ty = valueType(r)
            name = 'any'
    return (ty, name)


def match_mutability_pattern(content):
    ty = None
    name = None
    p = r'^The mutability :math:`(.*)`$'
    r = re.compile(p).findall(content)
    if r:
        ty = valueType('other', 'mutability')
        name = r[0]
    return (ty, name)


def match_special_macro(content):
    ty = None
    name = None
    special_macros = ['|MVAR|']
    if content in special_macros:
        ty = valueType('other', 'constant')
        name = content
    return (ty, name)

def match_context_pattern(content):
    ty = None
    name = None
    p = r'^the .*? :ref:`context <context>` .* :math:`(.*)`$'
    r = re.compile(p).findall(content)
    if r:
        ty = valueType('other', 'context')
        name = r[0]
    return (ty, name)


def match_value_from_type_of_pattern(content):
    ty = None
    name = None
    p = r'^[tT]he :ref:`result type <syntax-resulttype>` of :math:`.*`'
    if re.search(p, content):
        ty = valueType('i32', 'type_ref')
        name = content
    return (ty, name)

