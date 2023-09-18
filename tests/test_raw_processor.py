import pytest
from process_text import raw_processor

# @pytest.mark.parametrize('line_name', line_names)

raw_title_and_expected_name = [
    [":math:`t\\K{.}\\CONST~c`", "t.const"],
    [":math:`t_2\\K{.}\\cvtop\\K{\\_}t_1\\K{\\_}\\sx^?`", "t_2.cvtop_t_1_sx"],
    [":math:`t_1\\K{x}N\\K{.}\\EXTRACTLANE\\K{\\_}\\sx^?~x`", "t_1xN.extract_lane_sx"],
    [":math:`t_2\\K{x}N\\K{.}\\EXTADDPAIRWISE\\_t_1\\K{x}M\\_\\sx`", "t_2xN.extadd_pairwise_t_1xM_sx"],
    [":math:`\\BRTABLE~l^\\ast~l_N`", "br_table"],
    [":math:`\\IF~\\blocktype~\\instr_1^\\ast~\\ELSE~\\instr_2^\\ast~\\END`", "if"],
    [":math:`t\\K{.}\\STORE{N}~\\memarg`", "t.storeN"]
]

@pytest.mark.parametrize('raw_title, expected_name', raw_title_and_expected_name)
def test_process_raw_title(raw_title, expected_name):
    processed_name = raw_processor.process_raw_title(raw_title)
    assert processed_name == expected_name
