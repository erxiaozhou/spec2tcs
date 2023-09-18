import re
from functools import partial

val_p = r'(?:(?:^)|(?:[^a-zA-Z\d]))([a-zA-Z][a-zA-Z\d_]*)(?:(?:$)|(?:[^a-zA-Z_\d]))'


def is_val(s):
    if re.search(val_p, s):
        return True
    else:
        return False


def check_is_val(s):
    p = r'^[a-zA-Z][a-zA-Z\d_]*$'
    if re.search(p, s):
        return True
    else:
        return False


def propagate_paras(dict_, whole_str):
    keys = list(dict_.keys())
    expand_paras = partial(_expand_dict, dict_)
    s = whole_str
    for k in keys:
        for c in 'KBTFX':
            pass
        k = k.replace('\\', '\\\\')

        kp = f'({k})'
        p_fmt = '(?:(?:^)|(?:[^a-zA-Z\d])){}(?:(?:$)|(?:[^a-zA-Z_\d]))'
        final_p = p_fmt.format(kp)

        s = re.sub(final_p, expand_paras, s)
    return s


def _expand_dict(dict_, matched):
    whole_span = matched.span(0)
    matched_span = matched.span(1)
    whole_s = matched.group(0)
    matched_name = matched.group(1)
    new_name = dict_[matched_name]
    related_span = (matched_span[0] - whole_span[0],
                    matched_span[1] - whole_span[1])
    if whole_s.startswith(matched_name) and whole_s.endswith(matched_name):
        assert len(whole_s) == len(matched_name)
        new_str = new_name
    elif whole_s.startswith(matched_name):
        assert len(whole_s) == len(matched_name) + 1
        new_str = new_name + whole_s[-1]
    elif whole_s.endswith(matched_name):
        assert len(whole_s) == len(matched_name) + 1
        new_str = whole_s[0] + new_name
    else:
        assert len(whole_s) == len(matched_name) + 2
        start_str = whole_s[:related_span[0]]
        end_str = whole_s[related_span[1]:]
        new_str = ''.join((start_str, new_name, end_str))
    return new_str
