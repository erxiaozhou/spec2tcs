from process_text import find_all_vals, process_condition_text, raw_processor
from process_text import propagate_paras
import re

from process_text.process_str_parts_in_steps import process_power_eqieq
possible_cmp_sgs = ['<', '<=', '>', '>=', '==']

def get_value_name_in_store_dict(value_name, dict_):
    value_name = raw_processor._process_macro(value_name)
    name_fmt = '{}_{}'
    start_idx = 0
    generated_name = name_fmt.format(value_name, start_idx)
    while generated_name in dict_:
        start_idx += 1
        generated_name = name_fmt.format(value_name, start_idx)
    return generated_name


def check_val_exist(value_name, dict_):
    matched_values = _get_matched_val_indexs(value_name, dict_)
    if len(matched_values) == 0:
        return False
    else:
        return True


def _get_matched_val_indexs(value_name, dict_):
    keys = list(dict_.keys())
    matched_values = []
    add_line_name = ''.join((value_name, '_'))
    add_line_name_len = len(add_line_name)
    for name in keys:
        if not name.startswith(add_line_name):
            continue
        num_str = name[add_line_name_len:]
        if num_str.isdigit():
            matched_values.append(int(num_str))
    return matched_values


def can_replace_val(dict_, s, process_condiiton_text_=True):
    assert isinstance(dict_, dict), print(dict_)
    if process_condiiton_text_:
        s = process_condition_text(s)
    val_names = find_all_vals(s)
    for name in val_names:
        if not check_val_exist(name, dict_):
            return False
    return True


def replace_val(dict_, s, process_condiiton_text_=True):
    assert isinstance(dict_, dict), print(dict_)
    if process_condiiton_text_:
        s = process_condition_text(s)
    val_names = find_all_vals(s)
    name_relation = {}
    for name in val_names:
        # name = re.sub(r'\\+', '\\'*2, name)
        assert check_val_exist(name, dict_), print(f'***{name}*\n{dict_.keys()}\n{val_names}')
        new_val = get_val_from_dict_by_name(name, dict_)
        new_val_v = new_val.svalue.v_value
        name_relation[name] = new_val_v
    repr_d = {}
    for name in val_names:
        value_line = f"name_relation['{name}']"
        repr_d[name] = value_line
    print(repr_d, val_names)
    new_str = propagate_paras(repr_d, s)
    print(new_str)

    def func(m):
        s = m.group(0)
        fmt = 'int({})'.format(s)
        return fmt.format(s)
    new_str = re.sub(r'\d+ +[/] +\d+', func, new_str)
    new_str = process_constant_overflow(new_str)
    # process power eq / ineq
    new_str = process_power_eqieq(new_str)
    return eval(new_str)


def get_val_from_dict_by_name(value_name, dict_):
    target_name = _detect_value_name_in_store_dict(value_name, dict_)
    return dict_[target_name]


def _detect_value_name_in_store_dict(value_name, dict_):
    value_name = raw_processor._process_macro(value_name)
    assert check_val_exist(value_name, dict_), print(f'value_name: {value_name}\n', f'dict_: {dict_}')
    matched_values = _get_matched_val_indexs(value_name, dict_)
    max_index = max(matched_values)
    name_fmt = '{}_{}'
    target_name = name_fmt.format(value_name, max_index)
    return target_name


def process_constant_overflow(s):
    exist_sg = None
    for sg in possible_cmp_sgs:
        if ' {} '.format(sg) in s:
            exist_sg = sg
    if exist_sg is None:
        return s
    else:
        p = r'(.*) {} (.*)'.format(exist_sg)
        r = re.compile(p).findall(s)
        # to remove
        if r:
            left_part = r[0][0]
            right_part = r[0][1]
            if right_part == '2**32':
                left_part = left_part + ' - 1'
                right_part = right_part + ' -1'
                return '{} {} {}'.format(left_part, exist_sg, right_part)
    return s
