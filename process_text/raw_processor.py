import re
from file_util import path_read
from file_util import save_json
from spec_src_file_path_util import macro_def_path


def unwrap_math(line, must_math_check=False):
    p1 = r'(:math:`.*?`)'
    r = re.search(p1, line)
    if r is None:
        new_line = line
        if must_math_check:
            raise ValueError("the parameter `line` must match (:math:`.*?`)")
    else:
        span_ = r.span()
        new_line = ''.join(
            (line[:span_[0]], line[span_[0]+7:span_[1]-1], line[span_[1]:]))
    return new_line


def process_char_bracket_fmt(content):
    to_replace_pairs = {}
    to_match = []
    for i in range(len(content)):
        c = content[i]
        if c == '{':
            to_replace_pairs[i] = -1
            to_match.append(i)
        if c == '}':
            match_i = to_match.pop(-1)
            to_replace_pairs[match_i] = i
    assert len(to_match) == 0
    index_to_remove = []
    chars = []
    for left in to_replace_pairs.keys():
        if left < 2:
            continue
        if content[left-2] == '\\':
            if content[left-1] in 'KBTFX':
                index_to_remove.append(to_replace_pairs[left])
                index_to_remove.extend([left, left-1, left-2])
    chars = [content[i]
             for i in range(len(content)) if i not in index_to_remove]
    content = ''.join(chars)

    return content


def _process_bk(s):
    return s.replace('{', '').replace('}', '')


def process_str(s, remove_bk=False):
    s = unwrap_math(s)
    s = raw_processor._process_macro(s)
    s = process_char_bracket_fmt(s)
    s = s.replace('\\_', '_')
    if remove_bk:
        s = _process_bk(s)
    return s


class raw_processor():
    _inst_marco_dict = None

    @staticmethod
    def _init_inst_marco_dict():
        if raw_processor._inst_marco_dict is None:
            raw_processor._inst_marco_dict = _process_macro_file()

    @staticmethod
    def _process_characters(content):
        content = content.replace('\\_', '_').replace(
            '~', ' ').replace('\\ast', '*')
        return content

    @staticmethod
    def _process_macro(content: str, macro_dict=None):
        if macro_dict is None:
            raw_processor._init_inst_marco_dict()
            macro_dict = raw_processor._inst_marco_dict
        macro_list = [(''.join(('\\', k)), v) for k, v in macro_dict.items()]
        macro_list = sorted(macro_list, key=lambda x: len(x[0]), reverse=True)
        for k, v in macro_list:
            content = content.replace(k, v)
        return content

    @staticmethod
    def has_macro(content: str, macro_dict=None):
        if macro_dict is None:
            raw_processor._init_inst_marco_dict()
            macro_dict = raw_processor._inst_marco_dict
        keys = list(macro_dict.keys())
        keys = sorted(keys, key=lambda x: len(x), reverse=True)
        for k in keys:
            if k in content:
                return True
        return False

    @staticmethod
    def _remove_empty_lines(content):
        content = re.sub(r'\n{2,}', '\n', content)
        content = content.strip('\n')
        return content

    @staticmethod
    def _remove_sub_sec(content):
        lines = content.split('\n')
        subsec_index = -1
        for i, line in enumerate(lines):
            if re.search(r'^~+$', line):
                subsec_index = i
                break
        if subsec_index > 0:
            lines = lines[:subsec_index-1]
        content = '\n'.join(lines)
        return content

    @staticmethod
    def process_raw_title(raw_title):
        name = process_str(raw_title, remove_bk=True)
        name = name.split('~')[0]

        name = raw_processor._process_characters(name)
        name = re.sub(r'\^\?', '', name)
        return name

    @staticmethod
    def process_raw_content(raw_content):
        raw_processor._init_inst_marco_dict()
        content = raw_processor._remove_sub_sec(raw_content)
        content = raw_processor._remove_empty_lines(content)

        special_lines_index = {
            'note': [],
            'comment': [],
            'index': [],
            'num': [],
            'math': []
        }
        lines = content.split('\n')
        line_type = None
        for index, line in enumerate(lines):
            if line.startswith('.. math::'):
                line_type = 'math'
            elif line.startswith('.. _'):
                line_type = 'comment'
            elif line.startswith('.. index::'):
                line_type = 'index'
            elif line.startswith('.. note::'):
                line_type = 'note'
            elif re.search(r'^\d+\. ', line):
                line_type = 'num'
            else:
                pass
            special_lines_index[line_type].append(index)
        # check all potential lines are in one para
        _is_one_or_zero_para(special_lines_index['math'])
        _is_one_or_zero_para(special_lines_index['index'])
        _is_one_or_zero_para(special_lines_index['note'])
        _is_one_or_zero_para(special_lines_index['num'])

        math_para = '\n'.join(lines[i] for i in special_lines_index['math'])
        num_para = '\n'.join(lines[i] for i in special_lines_index['num'])

        p_content = {}
        p_content['math'] = math_para
        p_content['steps'] = num_para
        return p_content


def _process_macro_file(mode='only_inst'):
    assert mode in ['only_inst', 'all']
    content = path_read(macro_def_path)
    if mode == 'all':
        pass
    else:
        content = content
    p = r'\.\. \|(.*)\| mathdef:: .*\}\{(.*)\}'
    p = re.compile(p)
    words = p.findall(content)
    macro_dict = {w[0]: w[1] for w in words}
    save_json('./inst_info_log/last_macro_dict.json', macro_dict)
    return macro_dict


def _is_one_or_zero_para(lines: list):
    assert len(lines) == 0 or len(lines) == max(lines) - min(lines) + 1
