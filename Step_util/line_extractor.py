import re
from Condition_util import ConditionFactory
from Value_util import generate_Value_from_common_line
from Value_util import FormulaValue, ValRefValue
from Value_util import BlockValue, Location_descibor, Try_content


class linePattern:
    def __init__(self, line_type, reg_exp, may_contain_other=False):
        self.line_type = line_type
        self.reg_exp = re.compile(reg_exp)
        self.may_contain_other = may_contain_other

    def findall(self, line):
        return self.reg_exp.findall(line)


_ps = {
    # let
    'let_1_p': linePattern('let', r'Let (.*) be .* result of.* (:math:`.*?`)'),
    'let_2_p': linePattern('let', r'Let (.*) be (.*?)\.?$'),
    # push
    'push_p': linePattern('push', r'[Pp]ush (.*?) (?:(?:onto)|(?:on)|(?:back to)|(?:to)) the stack'),
    # pop
    'pop_p': linePattern('pop', r'[pP]op (.*) from the stack'),
    # if
    'if_p': linePattern('if', r' ?If (.*?)(?:, then)?:?$', True),
    'if_2_p': linePattern('if', r'If ([^`]*?), (.*?)\.?$', True),
    # jump
    'jump_1_p': linePattern('jump', r'Jump to (.*?)\.?$'),
    # assert
    'assert_p': linePattern('assert', r'Assert: (.*?)\.?$'),
    # trap
    'trap_p': linePattern('trap', r'Trap'),
    # while
    'while_p': linePattern('while', r'While (.*), do'),
    # return
    'return_p': linePattern('return', r'Return'),
    # replace
    'replace_p': linePattern('replace', r'Replace (.*) with (.*?)\.?$'),
    # repeat
    'repeat_p': linePattern('repeat', r'Repeat (.*) times'),
    # invoke
    'invoke_p': linePattern('invoke', r':ref:`Invoke <exec-invoke>` (.*?)\.?$'),
    # execute
    'execute_1_p': linePattern('execute', r':ref:`Execute <exec-br>` the instruction (.*?)\.?$'),
    'execute_2_p': linePattern('execute', r':ref:`Execute <exec-local.set>` the instruction (.*?)\.?$'),
    'execute_3_p': linePattern('execute', r'Execute the instruction (.*?)\.?$'),
    # do nothing
    'do_nothing_p': linePattern('do_nothing', r'Do nothing'),
    # else
    'else_1_p': linePattern('else', r'Else:$'),
    'else_2_p': linePattern('else', r'Else, (.*)$', True),
    # enter
    'enter': linePattern('enter', r':ref:`Enter <exec-instr-seq-enter>` (.*?)\.?$'),
    # either

    'either_p': linePattern('either', r' Either, try (.*?):$')
}


def get_exec_line_hier(line):
    if re.search(r'^\d{1,2}\.', line):
        hier = 0
    elif re.search(r'^ {3,4}[a-z]+\.', line):
        hier = 1
    elif re.search(r'^ {6}i\.', line):
        hier = 2
    else:
        print(line)
        raise ValueError('get hier info failed')
    return hier


non_para_types = ['trap', 'return', 'do_nothing']
# class line_extractor():


#     @staticmethod
def extract_exec_line_elements(line, hier_info=None):
    line_type = detect_line_type(line)
    if hier_info is None:
        hier_info = get_exec_line_hier(line)
    result_dict = {
        'line_type': line_type,
        'hier': hier_info,
        'elems': [],
        "raw_line": line,
        'embedded_line': []
    }
    # 
    type2func = {
        'push': get_push_paras,
        'pop': get_pop_paras,
        'execute': get_execute_paras,
        'invoke': get_invoke_paras,
        'while': get_while_paras,
        'jump': get_jump_paras,
        'enter': get_enter_paras,
        'assert': get_assert_paras,
        'replace': get_replace_paras,
        'repeat': get_repeat_paras,
        'let': get_let_paras,
        'either': get_either_paras
    }

    # 
    if line_type in non_para_types:
        pass
    elif line_type == 'if':
        conds, embedded_line = get_if_paras(line)
        result_dict['elems'].append(conds)
        if embedded_line:
            result_dict['embedded_line'].append(
                extract_exec_line_elements(embedded_line, hier_info+1))
    elif line_type == 'else':
        sub_sentence = get_else_paras(line)
        if sub_sentence is not None:
            result_dict['embedded_line'].append(
                extract_exec_line_elements(sub_sentence, hier_info+1))
    elif line_type in type2func:
        result_dict['elems'].append(type2func[line_type](line))
    else:
        raise Exception(f"unknown line_type: {line_type}")
    return result_dict


def detect_line_type(line, ps=None):
    if ps is None:
        ps = _ps
    possible_types = []
    for pattern in ps.values():
        if pattern.findall(line):
            if pattern.may_contain_other:
                possible_types = [pattern.line_type]
                break
            possible_types.append(pattern.line_type)
    if not possible_types:
        raise Exception(f'Unknown line type: <{line}>')
    possible_types = list(set(possible_types))
    assert len(possible_types) == 1
    return possible_types[0]


def get_push_paras(line):
    content = _ps['push_p'].findall(line)[0]
    content = re.sub('the values? ', '', content)
    value = generate_Value_from_common_line(content)
    return value


def get_pop_paras(line):
    content = _ps['pop_p'].findall(line)[0]
    content = re.sub('the values? ', '', content)
    value = generate_Value_from_common_line(content)
    return value


def get_if_paras(line):
    if_2_p_result = _ps['if_2_p'].findall(line)
    if if_2_p_result and if_2_p_result[0][1] != 'then:':
        text, embedded_line = if_2_p_result[0]
        conds = [ConditionFactory.from_if_line(text)]
        return conds, embedded_line
    else:
        if_p_result = _ps['if_p'].findall(line)
        assert if_p_result, print(line)
        line = if_p_result[0]
        texts = _get_if_para_text(line)
        conds = [ConditionFactory.from_if_line(text) for text in texts]
        return conds, None


def _get_if_para_text(line):
    texts = []
    or_pattern = re.compile(r'^(.+?) or (.*)$')
    or_p_match_result = or_pattern.findall(line)
    if len(or_p_match_result) > 0:
        assert len(or_p_match_result) == 1
        or_p_match_result = or_p_match_result[0]
        for sub_condition in or_p_match_result:
            texts.append(sub_condition)
    else:
        texts.append(line)
    return texts


def get_else_paras(line):
    if _ps['else_1_p'].findall(line):
        return None
    elif _ps['else_2_p'].findall(line):
        content = _ps['else_2_p'].findall(line)[0]
        return content


def get_enter_paras(line):
    content = _ps['enter'].findall(line)[0]
    value = BlockValue.from_enter_line(content)
    return value


def get_while_paras(line):
    content = _ps['while_p'].findall(line)[0]
    condition = ConditionFactory.from_while_line(content)
    return condition


def get_repeat_paras(line):
    content = _ps['repeat_p'].findall(line)[0]
    value = generate_Value_from_common_line(content)
    return value


def get_invoke_paras(line):
    content = _ps['invoke_p'].findall(line)[0]
    value = generate_Value_from_common_line(content)
    return value


def get_jump_paras(line):
    content = _ps['jump_1_p'].findall(line)[0]
    location = Location_descibor(content)
    return location


def get_either_paras(line):
    content = _ps['either_p'].findall(line)[0]
    value = Try_content(content)
    return value


def get_assert_paras(line):
    line = _ps['assert_p'].findall(line)[0]
    condition_content = _get_assert_para_text(line)
    condition = ConditionFactory.from_assert_line(condition_content)
    return condition


def _get_assert_para_text(line):
    cond_text = re.compile(r', (.*)$').findall(line)
    if cond_text:
        cond_text = cond_text[0]
    else:
        cond_text = line
    return cond_text


def get_replace_paras(line):
    content = _ps['replace_p'].findall(line)
    v1_txt, v2_txt = content[0]
    v1 = generate_Value_from_common_line(v1_txt)
    v2 = generate_Value_from_common_line(v2_txt)
    extracted_values = (v1, v2)
    return extracted_values


def get_let_paras(line):
    content = _ps['let_1_p'].findall(line)
    if content:
        v1_txt, v2_txt = content[0]
        v1 = ValRefValue.from_common_line(v1_txt)
        v2 = FormulaValue.from_common_line(v2_txt)
        extracted_values = (v1, v2)
    else:
        content = _ps['let_2_p'].findall(line)
        v1_txt, v2_txt = content[0]
        v1 = ValRefValue.from_common_line(v1_txt)
        v2 = generate_Value_from_common_line(v2_txt)
        extracted_values = (v1, v2)
    return extracted_values


def get_execute_paras(line):
    content = _ps['execute_1_p'].findall(line)
    if not content:
        content = _ps['execute_2_p'].findall(line)
    if not content:
        content = _ps['execute_3_p'].findall(line)
    content = content[0]
    value = generate_Value_from_common_line(content)
    return value
