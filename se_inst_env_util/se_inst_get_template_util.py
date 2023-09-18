from .se_inst import Environment
from combinedInst_util import combinedInst


def get_env(inst, template_strategy, solution_num):
    tc_mode = get_tc_mode(inst, template_strategy)
    if isinstance(tc_mode, list):
        envs = []
        for tc_mode_ in tc_mode:
            env = Environment(tc_mode_, solution_num)
            envs.append(env)
    else:
        assert isinstance(tc_mode, str)
        envs = [Environment(tc_mode, solution_num)]
    return envs


def get_tc_mode(inst, template_strategy):
    assert template_strategy == 8
    tc_mode = _get_single_tc_mode(inst, template_strategy)
    assert isinstance(tc_mode, (str, list))
    return tc_mode


def _get_single_tc_mode(inst, template_strategy):
    assert isinstance(inst, combinedInst)
    if template_strategy == 8:
        if inst.name in ['memory.init', 'data.drop']:
            tc_mode = 'template_nonv128_add_data_count'
        elif inst.require_state_variables or inst.name == 'local.tee':
            tc_mode = 'non_v128'
        else:
            tc_mode = 'nonv128_empty'
    else:
        assert 0, 'template_strategy not supported'
    return tc_mode
