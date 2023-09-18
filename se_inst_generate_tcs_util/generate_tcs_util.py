from itertools import product
from combinedInst_util import combinedInst
from file_util import check_dir
from value_encoder import candidate_values
from .determine_push_ty_util import determine_push_ty
from .generate_one_tc import generate_one_tc, instEncodingParas


def generate_tcs_from_result_pairs(result_pairs, cinst, base_dir, template_config=None, start_idx=0, save_meta_data=True, skip_generation=False):
    assert isinstance(cinst, combinedInst)
    check_stack_vals_type(result_pairs)
    all_para_combinations = set()
    for stack_vals, imm_vals, opcodes in result_pairs:
        opcodes = [opcodes]
        for stack_val_candi in stack_vals:
            para_combinations = _get_para_combinations(stack_val_candi, imm_vals, opcodes)
            all_para_combinations.update(para_combinations)
    base_dir = check_dir(base_dir)

    inferred_push_ty = cinst.push_type_with_exec_title_info
    inst_name = cinst.name
    if skip_generation:
        return len(all_para_combinations)
    for idx, para_combination in enumerate(all_para_combinations, start=start_idx):
        stack_len = para_combination[-1]
        cur_stack_vs = para_combination[:stack_len]
        cur_imm_vs = para_combination[stack_len:-2]
        cur_opcode = para_combination[-2]
        # rewrite the above line
        target_path = str(base_dir / f'{cinst.name}_{idx}.wasm')
        push_ty = determine_push_ty(template_config, inst_name, inferred_push_ty, cur_stack_vs, cur_imm_vs)
        inst_en_paras = instEncodingParas(cur_opcode, cur_imm_vs, cinst.bin_inst.imm_new_index, cinst.binary_info)
        generate_one_tc(template_config, cur_stack_vs, target_path, push_ty, inst_en_paras, save_meta_data)
    return len(all_para_combinations)

def check_stack_vals_type(result_pairs):
    for stack_vals, imm_vals, opcodes in result_pairs:
        type_logs = set()
        for stack_val_candi in stack_vals:
            for x in stack_val_candi:
                assert isinstance(x, candidate_values)
            type_log = tuple([x.ty for x in stack_val_candi])
            assert type_log not in type_logs, print(type_log, type_logs)
            type_logs.add(type_log)


def _get_para_combinations(stack_vals, imm_vals, opcodes):
    all_vals = stack_vals + imm_vals + opcodes
    para_combination = list(product(*all_vals))
    para_combination = [comb+(len(stack_vals),) for comb in para_combination]
    return para_combination
