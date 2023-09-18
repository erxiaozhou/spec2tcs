from pathlib import Path
from combinedInst_util import combinedInst
from combinedInst_util import combinedInsts
from env_store import env_store
from file_util import read_json
from se_inst_env_util import get_tc_mode
from solve_util import get_all_self_constraints
from spec_coverage_calculator import generate_random_vals
from spec_coverage_calculator import coverage_Env
import claripy
from file_util import save_json, check_dir
from value_encoder import value_holder
import sys


def is_satisfiable(constraints):
    s = claripy.Solver()
    for c in constraints:
        s.add(c)
    return s.satisfiable()

def _process_concrete(concrete):
    if isinstance(concrete, value_holder):
        concrete = concrete.constant
    if isinstance(concrete, list):
        assert len(concrete) == 16
        concrete = _list2num(concrete)
    return concrete




def cal_coverage(reachable_paths, stack_concrete_vals, imm_concrete_vals):
    path_num = len(reachable_paths)
    visited_num = 0
    for reachable_path in reachable_paths:

        reached = False
        constrains = reachable_path[0]
        store = reachable_path[1]
        assert isinstance(store, env_store)
        stack_in_store = store.stack
        imm_in_store = store.imm_values
        stack_val_symbols = [v.svalue.v_value for v in stack_in_store]
        imm_val_symbols = [v.svalue.v_value for v in imm_in_store]
        self_constraints = get_all_self_constraints(stack_in_store, imm_in_store)
        constrains += self_constraints
        assert len(stack_concrete_vals) >= len(stack_val_symbols), print(len(stack_concrete_vals), len(stack_val_symbols), stack_in_store, imm_in_store)
        assert len(imm_concrete_vals) == len(imm_val_symbols)

        if len(stack_concrete_vals) + len(imm_val_symbols)== 0:
            assert path_num == 1
            visited_num = 1 
            break
        if not is_satisfiable(constrains):
            path_num -= 1
            continue
        if len(stack_concrete_vals) == 0:
            sample_num = len(imm_concrete_vals[0])
        else:
            sample_num = len(stack_concrete_vals[0])
        for i in range(sample_num):
            cur_sample_stack = [val[i] for val in stack_concrete_vals]
            cur_sample_imm = [val[i] for val in imm_concrete_vals]
            _constrains = [c for c in constrains]
            for j in range(len(stack_val_symbols)):
                symbol = stack_val_symbols[j]
                if isinstance(symbol, str) and (symbol == 'any'):
                    continue
                concrete = cur_sample_stack[j]
                concrete = _process_concrete(concrete)
                c = symbol == concrete
                assert isinstance(c, claripy.ast.bool.Bool), print(symbol, concrete, c)
                _constrains.append(c)
            for j in range(len(cur_sample_imm)):
                symbol = imm_val_symbols[j]
                concrete = cur_sample_imm[j]
                concrete = _process_concrete(concrete)
                c = symbol == concrete
                assert isinstance(c, claripy.ast.bool.Bool)
                _constrains.append(c)
            if is_satisfiable(_constrains):
                visited_num += 1
                break
    return path_num, visited_num


def _list2num(L):
    assert len(L) == 16
    ba = bytearray(L[::-1])
    return int.from_bytes(ba, byteorder='little')


def generate_and_cal_cov(cinst: combinedInst, env: coverage_Env, val_num=10000):
    print('In generate_and_cal_cov: val_num', val_num)
    assert isinstance(env, coverage_Env)
    reachable_paths = env.execute(cinst)
    if cinst.name == 'ref.is_null':
        return 2, 2

    store = reachable_paths[0][1]
    stack_vals = store.stack
    imm_vals = store.imm_values
    all_num = len(reachable_paths)
    if all_num == 1:
        return 1, 1
    stack_concrete_vals, imm_concrete_vals = generate_random_vals(stack_vals, imm_vals, val_num)
    actual_all_num, visited_num = cal_coverage(reachable_paths, stack_concrete_vals, imm_concrete_vals)
    return visited_num, actual_all_num


def test_all_insts(num_log, each_inst_info_report, failed_insts_json, onlylist=None):
    if onlylist is not None:
        onlylist = read_json(onlylist)
    # process num_log
    if isinstance(num_log, str):
        assert Path(num_log).exists()
        num_log = read_json(num_log)
    assert isinstance(num_log, dict)
    combined_insts = combinedInsts.get_combined_insts()
    path_log = {
        'visited_num_sum': 0,
        'all_path_sum': 0,
        'visited_num_sum_without_1p': 0,
        'all_path_sum_without_1p': 0,
    }
    d = {}

    failed_insts = []
    for inst_name in num_log.keys():
        try:
            cinst = combined_insts.get_inst_by_inst_name(inst_name)
            tc_mode = get_tc_mode(cinst, 8)
            env = coverage_Env(tc_mode)
            print(tc_mode, inst_name)
            # continue
            num = num_log[inst_name]
            assert isinstance(num, list) and len(num) == 1
            num = num[0]
            visited_num, all_num = generate_and_cal_cov(cinst, env, val_num=num)
            path_log['visited_num_sum'] += visited_num
            path_log['all_path_sum'] += all_num

            if all_num > 1:
                d[inst_name] = [visited_num, all_num]
                path_log['visited_num_sum_without_1p'] += visited_num
                path_log['all_path_sum_without_1p'] += all_num
        except Exception as e:
            raise e
            failed_insts.append(inst_name)
    for k, v in path_log.items():
        print(k, v)
    save_json(each_inst_info_report, d)
    save_json(failed_insts_json, failed_insts)
    return path_log



if __name__ == '__main__':
    save_base_dir = sys.argv[1]
    results = []
    save_base_dir = check_dir(save_base_dir)
    num_log = './generated_tcs/v19/log/num_log.json'
    each_inst_info_report = str(Path(save_base_dir) / 'each_inst_info_report.json')
    failed_insts_json = str(Path(save_base_dir) / 'failed_insts.json')

    r = test_all_insts(num_log, each_inst_info_report,  failed_insts_json)
    results.append(r)
