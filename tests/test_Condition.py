from Step_util.line_extractor import get_if_paras
from file_util import read_json
import pytest
from Condition_util import ConditionFactory, Condition
from Step_util.line_extractor import _get_assert_para_text
from .line_extractor_util import _read_target_lines


all_extracted_lines = read_json('./tests/testing_data/testingdata_for_line_extractor.json')
while_cond_lines = all_extracted_lines['while_p']
assert_cond_lines = all_extracted_lines['assert_p']
if_raw_lines = _read_target_lines('If')


def get_all_if_conds():
    conds = []
    for line in if_raw_lines:
        conds.extend(get_if_paras(line)[0])
    return conds


def get_all_while_conds():
    conds = []
    for line in while_cond_lines:
        cond_text = line
        conds.append(ConditionFactory.from_while_line(cond_text))
    return conds


def get_all_assert_conds():
    conds = []
    for line in assert_cond_lines:
        cond_text = _get_assert_para_text(line)
        conds.append(ConditionFactory.from_assert_line(cond_text))
    return conds


while_conds = get_all_while_conds()
@pytest.mark.parametrize('cond', while_conds)
def test_all_while_conds_can_match(cond):
    assert isinstance(cond, Condition)

if_conds = get_all_if_conds()
@pytest.mark.parametrize('cond', if_conds)
def test_all_if_conds_can_match(cond):
    assert isinstance(cond, Condition)

assert_conds = get_all_assert_conds()
@pytest.mark.parametrize('cond', assert_conds)
def test_all_assert_conds_can_match(cond):
    assert isinstance(cond, Condition)
