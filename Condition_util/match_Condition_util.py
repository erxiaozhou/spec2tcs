import re
from Value_util import constantValue
from Value_util import StackValue
from Value_util import generate_Value_from_common_line
from Value_util import FormulaValue


def extract_bool(content):
    words = content.split(' ')
    result = True
    if 'not' in words:
        result = False
    return result


def match_is_condition(line):
    elems = []
    p = re.compile(r'^(:math:`.*?`) (is(?: not)?) (:math:`.*?`)$')
    r = p.findall(line)
    if r:
        r = r[0]
        assert len(r) == 3
        elems.append('is_condition')
        elems.append(generate_Value_from_common_line(r[0]))
        elems.append(extract_bool(r[1]))
        elems.append(generate_Value_from_common_line(r[2]))
    return elems


def match_is_ref_condition(line):
    elems = []
    p = re.compile(r'^(:math:`.*?`) (is(?: not)?) (a? :ref:`.*?`)$')
    r = p.findall(line)
    if r:
        r = r[0]
        assert len(r) == 3, print(r)
        elems.append('is_condition')
        elems.append(generate_Value_from_common_line(r[0]))
        elems.append(extract_bool(r[1]))
        v = generate_Value_from_common_line(r[2])
        elems.append(v)
    return elems


def match_is_defined_condition(line):
    elems = []
    p = re.compile(r'^(:math:`.*?`) is defined$')
    r = p.findall(line)
    if r:
        assert len(r) == 1
        elems.append('is_defined_condition')
        elems.append(generate_Value_from_common_line(r[0]))
    return elems

def match_is_present_condition(line):
    elems = []
    p = re.compile(r'^(:math:`.*?`) is present$')
    r = p.findall(line)
    if r:
        assert len(r) == 1
        elems.append('present_condition')
        elems.append(generate_Value_from_common_line(r[0]))
    return elems


def match_formula_condition(line):
    elems = []
    p = re.compile(r'^(:math:`[^`]+`)$')
    r = p.findall(line)
    if r:
        elems.append('formula_condition')
        elems.append(FormulaValue.from_common_line(r[0]))
    return elems


def match_non_zero_condition(line):
    elems = []
    p = re.compile(r'^(:math:`.*?`) is non-zero$')
    r = p.findall(line)
    if r:
        elems.append('non_zero_condition')
        elems.append(generate_Value_from_common_line(r[0]))
    return elems


def match_is_part_condition(line):
    elems = []
    p = re.compile(r'^(:math:`[^`]*?`) (is(?: not)?) part of the instruction$')
    r = p.findall(line)
    if r:
        r = r[0]
        assert len(r) == 2
        elems.append('instruction_part_condition')
        vs = [generate_Value_from_common_line(v_str) for v_str in r[:1]]
        elems.append(vs)
        elems.append(extract_bool(r[1]))
    p = re.compile(r'^(:math:`[^`]*?`) and (:math:`[^`]*?`) ((?:(?:is)|(?:are))(?: not)?) part of the instruction$')
    r = p.findall(line)
    if r:
        r = r[0]
        assert len(r) == 3
        elems.append('instruction_part_condition')
        vs = [generate_Value_from_common_line(v_str) for v_str in r[:1]]
        elems.append(vs)
        elems.append(extract_bool(r[2]))
    return elems


def match_differ_condition(line):
    elems = []
    p = re.compile(r'^(:math:`.*?`) and (:math:`.*?`) differ$')
    r = p.findall(line)
    if r:
        r = r[0]
        assert len(r) == 2
        elems.append('differ_condition')
        elems.append(generate_Value_from_common_line(r[0]))
        elems.append(generate_Value_from_common_line(r[1]))
    return elems


def match_compare_condition(line):
    elems = []
    p = re.compile(r'^(:math:`.*?`) (is(?: not)?) (.*?) than (.*)$')
    r = p.findall(line)
    if r:
        r = r[0]
        assert len(r) == 4
        elems.append('compare_condition')
        elems.append(generate_Value_from_common_line(r[0]))
        elems.append(extract_bool(r[1]))
        elems.append(r[2])
        elems.append(generate_Value_from_common_line(r[3]))
    return elems


def match_the_top_of_stack_be_condition(line):
    elems = []
    p = re.compile(r'the top of the stack.*?((?:(?:is)|(?:are))(?: not)?) (.*?)$')
    r = p.findall(line)
    if r:
        r = r[0]
        elems.append('stack_top_be')
        elems.append(extract_bool(r[0]))
        elems.append(generate_Value_from_common_line(r[1]))
    return elems


def match_on_the_stack_top_condition(line):
    elems = []
    p = re.compile(
        r'^(.*? values? ?(?:(?:(?:with)|(?:of)) :ref:`[^`]+`.*)?) (?:(?:is)|(?:are)) on the top of the stack$')
    r = p.findall(line)
    if r:
        elems.append('stack_top')
        elems.append(True)
        elems.append(StackValue.from_common_line(r[0]))
    return elems


def match_thereb_on_the_stack_top_condition(line):
    elems = []
    p = re.compile(r'^there are (.*? values?) on the top of the stack$')
    r = p.findall(line)
    if r:
        elems.append('thereb_stack_top')
        elems.append(True)
        elems.append(generate_Value_from_common_line(r[0]))
    return elems


def match_stack_contain_condition(line):
    elems = []
    p = re.compile(r'^the stack contains (.*)$')
    r = p.findall(line)
    if r:
        v = generate_Value_from_common_line(r[0])
        elems.append('stack_contain')
        elems.append(v)
    return elems


def match_ref_on_the_stack_top_condition(line):
    elems = []
    p = re.compile(
        r'^(.* :ref:`.*?`) (?:(?:is)|(?:are)) on the top of the stack$')
    r = p.findall(line)
    if r:
        elems.append('ref_stack_top')
        elems.append(True)
        elems.append(StackValue.from_common_line(r[0]))
    return elems


def match_exists_condition(line):
    elems = []
    p = re.compile(r'^(:math:`.*`) exists$')
    r = p.findall(line)
    if r:
        assert len(r) == 1
        elems.append('exist')
        elems.append(generate_Value_from_common_line(r[0]))
    return elems


def match_two_same_type_stack_top_condition(line):
    elems = []
    p = re.compile(r'^(.*? values) \(of the same :ref:`value type <syntax\-valtype>`\) are on the top of the stack')
    r = p.findall(line)
    if r:
        v = StackValue.from_common_line(r[0])
        elems.append('two_same_type_on_stack')
        elems.append(True)
        elems.append(v)
    return elems


def match_simd_val_condition(line):
    elems = []
    p = re.compile(r'^for all :math:`x_i` in (:math:`.*`) it holds that :math:`x_i ([=<>]) (\d+)`$')
    r = p.findall(line)
    if r:
        r = r[0]
        v1 = generate_Value_from_common_line(r[0])
        v2 = constantValue.from_constant_str(r[2])
        v3 = r[1]
        elems.append('simd_val')
        elems.append(v1)
        elems.append(v2)
        elems.append(v3)
    return elems


def match_machine_determined_condition(line):
    elems = []
    if re.compile(r'^it succeeds$').findall(line):
        elems.append('machine_determined')
    return elems
