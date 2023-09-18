from combinedInst_util.combine_inst_info import get_exec_insts_possible_names
from combinedInst_util.combine_inst_info import get_valid_insts_possible_names
from file_util import read_json
import pytest


def test_new_exec_insts_possible_names_eq_the_ori():
    d1 = get_exec_insts_possible_names()
    d2 = read_json('tests/testing_data/exec_ori_matched_data.json')
    d1_names = []
    for inst, names in d1:
        d1_name = inst.raw_title
        d1_names.append(d1_name)
        assert set(names) == set(d2[d1_name]), print(d1_name, set(names)-set(d2[d1_name]), set(d2[d1_name])-set(names))
    assert set(d1_names) == set(d2.keys())

test_data = [
    get_exec_insts_possible_names(),
    get_valid_insts_possible_names()
]
@pytest.mark.parametrize('d', test_data)
def test_no_conflict(d):
    d = get_valid_insts_possible_names()
    values = set()
    for v in d:
        for vv in v[1]:
            assert vv not in values
