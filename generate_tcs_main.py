import sys
import traceback
from combinedInst_util import combinedInst
from combinedInst_util import combinedInsts
from file_util import check_dir, read_json, rm_dir
from se_inst_generate_tcs_util import generate_tcs_from_result_pairs
from generation_process_util import generationResult, generationConfig
from se_inst_env_util import get_env
from se_inst_env_util import Environment


def generate_main(config):
    assert isinstance(config, generationConfig)
    base_dir = config.base_dir
    if config.remove_existing:
        rm_dir(base_dir)
    tcs_dir = check_dir(config.tcs_dir)
    generaetion_r = generationResult(config, config.log_dir)
    generaetion_r.init_start_testing_time()
    combined_insts = combinedInsts.get_combined_insts()
    visited_illegalop_ty = []
    if config.only_exec_todo_list:
        totest_list = read_json(config.todolist_path)

    for inst in combined_insts:
        if config.only_exec_todo_list and (inst.name not in totest_list):
            continue
        print(inst.name)
        assert isinstance(inst, combinedInst)
        try:
            if inst.name in ['call_indirect', 'br', 'br_if', 'br_table', 'if', 'if_04~bt~in_1~05~in_2~0B', 'block', 'loop', 'return']:
                assert 0
            start_idx=0
            tc_nums = []
            envs = get_env(inst, config.template_strategy, solution_num=config.solution_num)
            assert isinstance(envs, list)
            for env in envs:
                assert isinstance(env, Environment)
                result_pairs, invoked_non_defined_ops = env.execute(inst, visited_illegalop_ty, config.exec_config, config.detect_spec_cov_exec)
                tc_num = generate_tcs_from_result_pairs(result_pairs, inst, base_dir=tcs_dir, template_config=env.template_config, start_idx=start_idx, save_meta_data=config.save_meta_data, skip_generation=config.skip_generation)
                print('tc_num', tc_num)
                start_idx += tc_num
                tc_nums.append(tc_num)
            if invoked_non_defined_ops:
                visited_illegalop_ty.append(inst.infer_std_type_for_opcodes)
            generaetion_r.num_log[inst.name] = tc_nums
        except Exception as e:
            traceback.print_exc()
            print('=' * 20)
            generaetion_r.failed_inst_names.append(inst.name)
            continue
        generaetion_r.ok_inst_names.append(inst.name)
    generaetion_r.init_end_testing_time()
    generaetion_r.save()
    print('base_dir:', base_dir)


def _get_config(argv):
    assert len(argv) == 2
    config_path = argv[1]
    config = generationConfig.from_json(config_path)
    return config


if __name__ == '__main__':
    argv = sys.argv
    config = _get_config(argv)
    generate_main(config)
