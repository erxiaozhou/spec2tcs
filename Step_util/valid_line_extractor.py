import re
from Condition_util.validCondition import get_must_ty_cond, get_seq_ty_cond, get_infered_must_ty_cond
from Condition_util.validCondition import get_must_define_cond, get_CompareCondition_from_must_be, get_valid_must_be_cond, get_valid_exist_cond, get_blocktype_type_cond
from Value_util import ValRefValue
from Value_util import generate_Value_from_common_line
from .line_extractor import _ps, linePattern
from .line_extractor import detect_line_type, get_let_paras, get_if_paras, get_else_paras


valid_unique_ps = {
    'let_3_p': linePattern('let', r'Let (:math:`.*?`) be (.*),'),
    'with_type1': linePattern('must_ty', r'[tT]he instruction is valid with type (:math:`[^`]*?`)\.$'),
    'with_type12': linePattern('must_ty', r'[tT]he instruction is valid with type (:math:`[^`]*?`, for any .*)\.$'),
    'with_type2': linePattern('must_ty', r'[tT]he compound instruction is valid with type (:math:`[^`]*?`)\.$'),
    'with_type3': linePattern('must_ty', r'[tT]he instruction sequence (:math:`[^`]*?`) must be .*with type (:math:`[^`]*?`)'),
    'must_exist': linePattern('must_exist', r'^(.*) must (?:(?:not be absent)|(?:be defined)) in the context\.'),
    'must_be1': linePattern('must_be', r'(.*) must be ((?::math:`.*`)|(?:\|.*\|))\.'),
    'must_be2': linePattern('must_be', r'(.*) must (not )?be ((?:larger than)|(?:the same as)|(?:smaller than)) (.*)\.'),
    'must_be_contain': linePattern('must_be', r'(.*?) must be contained in (.*)\.'),
    'must_be_blocktype': linePattern('must_be', r'.*:ref:`(.*) <syntax-blocktype>` must be .*valid.* :math:`\[(.*)\] \\to \[(.*)\]`\.'),
    'for_each': linePattern('for_each', r'For (?:(?:each)|(?:all)).*', True),
    'such_that': linePattern('such_that', r'^(.*), such that:', True),

}

practical_valud_ps = valid_unique_ps.copy()
practical_valud_ps.update(_ps)

def get_valid_line_hier(line):
    assert re.compile(r' *\* ').findall(line)
    blank_part = re.compile(r'^( *)\* ').findall(line)[0]
    return int(len(blank_part) / 2)

def extract_valid_line_elements(line, hier_info=None):
    line_type = detect_line_type(line, practical_valud_ps)
    if hier_info is None:
        hier_info = get_valid_line_hier(line)
    cleaned_line = re.sub(r' *\* ', '', line)
    result_dict = {
        'line_type': line_type,
        'hier': hier_info,
        'elems': [],
        'raw_line': line,
        'embedded_line': []
    }
    type2func = {
        'let': get_valid_let_paras,
        'must_ty': get_must_ty_paras,
        'must_be': get_must_be_paras,
        'must_exist': get_must_define_paras,
        'for_each': get_for_each_paras,
        'such_that': get_such_that_paras

    }
    if line_type == 'if':
        conds, embedded_line = get_if_paras(cleaned_line)
        result_dict['elems'].append(conds)
        assert embedded_line is None
    elif line_type == 'else':
        sub_sentence = get_else_paras(cleaned_line)
        assert sub_sentence is None
    elif line_type in type2func:
        result_dict['elems'].append(type2func[line_type](cleaned_line))
    else:
        raise Exception(f"unknown line_type: {line_type}")
    return result_dict


def get_must_ty_paras(line):
    if valid_unique_ps['with_type1'].findall(line):
        cond_text = valid_unique_ps['with_type1'].findall(line)[0]
        cond = get_must_ty_cond(cond_text)
        return cond
    elif valid_unique_ps['with_type2'].findall(line):
        cond_text = valid_unique_ps['with_type2'].findall(line)[0]
        cond = get_must_ty_cond(cond_text)
        return cond
    elif valid_unique_ps['with_type3'].findall(line):
        cond_text = valid_unique_ps['with_type3'].findall(line)[0]
        return get_seq_ty_cond(line, *cond_text)
    elif valid_unique_ps['with_type12'].findall(line):
        cond_text = valid_unique_ps['with_type12'].findall(line)[0]
        return get_infered_must_ty_cond(cond_text)

def get_must_define_paras(line):
    return get_must_define_cond(valid_unique_ps['must_exist'].findall(line)[0])

def get_must_be_paras(line):
    if valid_unique_ps['must_be1'].findall(line):
        elem_strs = valid_unique_ps['must_be1'].findall(line)[0]
        return get_valid_must_be_cond(line, elem_strs)
    elif valid_unique_ps['must_be2'].findall(line):
        r = valid_unique_ps['must_be2'].findall(line)[0]
        v1, hold_or_not, relation, v2 = r
        return get_CompareCondition_from_must_be(line, v1, hold_or_not, relation, v2)
    elif valid_unique_ps['must_be_contain'].findall(line):
        r = valid_unique_ps['must_be_contain'].findall(line)[0]
        return get_valid_exist_cond(line, r)
    elif valid_unique_ps['must_be_blocktype'].findall(line):
        r = valid_unique_ps['must_be_blocktype'].findall(line)[0]
        r = list(r)
        r[0] = r[0].replace(' ', '')
        return get_blocktype_type_cond(line, r)

def get_valid_let_paras(line):
    r = valid_unique_ps['let_3_p'].findall(line)
    if r:
        r = r[0]
        r1 = ValRefValue.from_common_line(r[0])
        r2 = generate_Value_from_common_line(r[1])
        return r1, r2
    else:
        return get_let_paras(line)

def get_for_each_paras(line):
    return 'for each step is not implemented yet'

def get_such_that_paras(line):
    return 'such that is not implemented yet'
