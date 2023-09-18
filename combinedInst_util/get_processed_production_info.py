from .extract_syntax_names import get_inst_names_from_syntax
from file_util import save_json
from process_text import _process_bk, process_char_bracket_fmt, process_str, raw_processor


def get_processed_productions():
    inst_syntax = get_inst_names_from_syntax()
    productions = inst_syntax.productions_without_cgty
    cleaned_productions = {}
    for k, v in productions.items():
        k = _process_k_name(k)
        v = [_process_v_name(v_) for v_ in v]
        cleaned_productions[k] = v
    save_json('./inst_info_log/last_processed_productions.json', cleaned_productions)
    save_json('./inst_info_log/last_ori_productions.json', productions)
    return cleaned_productions


def get_sorted_production_list():
    processed_productions = get_processed_productions()
    sorted_production_list = _sort_processed_productions(processed_productions)
    return sorted_production_list


def _process_k_name(s):
    s = raw_processor._process_macro(s)
    s = process_char_bracket_fmt(s)
    s = _process_bk(s)
    s = s.replace('\\_', '_')
    return s

def _process_v_name(s):
    s = raw_processor._process_macro(s)
    s = process_char_bracket_fmt(s)
    s = _process_bk(s)
    s = s.replace('\\_', '_')
    return s


def _sort_processed_productions(processed_productions_dict):
    rp_list = []
    for k, v in processed_productions_dict.items():
        rp_list.append([k, v])
    rp_list = sorted(rp_list, key=lambda x: len(x[0]), reverse=True)
    return rp_list
