from functools import partial
import pytest
from process_text import unwrap_math
from .line_extractor_util import _read_target_lines
from .line_extractor_util import _count_not_empty_result
from .line_extractor_util import extract_data_by_p
from .line_extractor_util import get_gt_data_for_p_name
from .line_extractor_util import get_processed_unique_lines
from Step_util.line_extractor import detect_line_type
from Step_util.valid_line_extractor import get_valid_line_hier
from Step_util.valid_line_extractor import practical_valud_ps
from Step_util.line_extractor import _ps


lines = _read_target_lines('Push') + _read_target_lines('Pop')
@pytest.mark.parametrize('line', lines)
def test_unwrap_math(line):
    assert 'math' not in unwrap_math(line)


def line_is_with_type(line_type, line):
    return line_type == detect_line_type(line)


line_names = ['Trap', 'While', 'Return', 'Replace', 'Repeat', 'Push', 'Pop', 'Let', 'Jump', 'Invoke', 'If', 'Execute', 'Do_nothing', 'Else','Assert', 'Enter']
@pytest.mark.parametrize('line_name', line_names)
def test_detect_num(line_name):
    lines = _read_target_lines(line_name)
    match_mun = _count_not_empty_result(partial(line_is_with_type, line_type=line_name.lower()), lines)
    assert match_mun == len(lines)


# ps_names = set([p.line_type for p in _ps.values()])
ps_names = list(_ps.keys())
@pytest.mark.parametrize('p_name', ps_names)
def test_extracted_content(p_name):
    gt_data_set = get_gt_data_for_p_name(p_name)
    extracted_data_set = extract_data_by_p(p_name)
    assert gt_data_set == extracted_data_set


line_cases_for_detect_line_type = [
    r'   b. Else, push the value :math:`\I32.\CONST~(-1)` to the stack.',
    r'   b. Else, push the value :math:`\I32.\CONST~\X{err}` to the stack.',
    r'   a. If it succeeds, push the value :math:`\I32.\CONST~\X{sz}` to the stack.'
]
line_type_for_detect_line_type = [
    'else', 'else', 'if'
]
@pytest.mark.parametrize('line, line_type', zip(line_cases_for_detect_line_type, line_type_for_detect_line_type))
def test_detect_line_type(line, line_type):
    assert line_type == detect_line_type(line)


test_get_valid_line_hier_paras = [
    ['* The instruction is valid with type :math:`[t] \to [t]`.', 0],
    [r'  * The length of :math:`t^\ast` must be :math:`1`.', 1],
    [r'* The table :math:`C.\CTABLES[y]` must be defined in the context.', 0]
]

@pytest.mark.parametrize('line, hier_gt', test_get_valid_line_hier_paras)
def test_get_valid_line_hier(line, hier_gt):
    assert hier_gt == get_valid_line_hier(line)


def test_detect_valid_line_type():
    unique_lines = get_processed_unique_lines()
    unknown_lines = []
    d = {}
    for line in unique_lines:
        try:
            ty = detect_line_type(line, practical_valud_ps)
            d.setdefault(ty, []).append(line)
        except Exception:
            unknown_lines.append(line)
    assert len(unknown_lines) == 0, print(f'unknown_lines: {unknown_lines}')

