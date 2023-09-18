import re
from process_text import raw_processor
from functools import partial


def renew_raw_content_without_math(raw_content, dict_):
    expand_macro_and_paras = partial(_extract_macro_in_math, dict_)
    p1 = r'.*'
    s2 = re.sub(p1, expand_macro_and_paras, raw_content)
    return s2


def _extract_macro_in_math(dict_, matched):
    matched_whole_str = matched.group(0)
    expand_macro_str = raw_processor._process_macro(matched_whole_str)
    keys = list(dict_.keys())
    expand_paras = partial(_expand_dict, dict_)
    s = expand_macro_str
    for k in keys:
        final_p = f'(?:(?:^)|(?:[^a-zA-Z]))({k})(?:(?:$)|(?:[^a-zA-Z_]))'
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
        start_str = whole_s[:related_span[0]]
        end_str = whole_s[related_span[1]:]
        new_str = '{}{}{}'.format(start_str, new_name, end_str)
    return new_str
