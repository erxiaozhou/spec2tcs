from copy import deepcopy
import claripy
from Value_util import valueType
from combinedInst_util import combinedInst
from env_store import env_store, env_store_config
from .get_template import get_template
from solve_util import check_satisfiable, check_stack_imm, get_type_solutions, solve_symbols, get_all_self_constraints
from value_encoder import candidate_values
from generation_process_util import execConfig
from symbol_util import val2type_str
from .se_inst_exec_util import get_path_tuple, is_false_constraint
from .se_inst_exec_util import whether_trap
from .se_inst_exec_util import whether_exec_ty_trap
from .se_inst_encoding_util import generate_encoding_for_one_ty, generate_random_encoding_for_imm
from Condition_util import append_operands
from file_util import get_logger


std_logger = get_logger('std_log', 'tt/std_log.log')
logger = get_logger('test_se_inst.py', 'tt/se_inst.log')
spec_cov_logger = get_logger('spec_cov', 'tt/spec_cov.log')
all_val_d_path_num = 0
nulti_path_inst_num = 0


def _check_path_satisfiable(store, constraints):
    stack_values = store.stack
    imm_values = store.imm_values
    all_self_constraints = get_all_self_constraints(imm_values, stack_values)
    all_constraints = all_self_constraints + constraints
    std_logger.debug('all_self_constraints\n' + str(all_self_constraints))
    std_logger.debug('all_constraints\n' + str(all_constraints))
    std_logger.debug('store.stack\n' + str(store.stack))
    return check_satisfiable(all_constraints)

class Environment:
    def __init__(self, tc_mode, solution_num):
        self.solution_num = solution_num
        self.template_config = get_template(tc_mode)

    def _solve(self, store, constraints, is_ty_trap, exec_config=None):
        assert exec_config is not None
        if is_ty_trap and exec_config.limit_val_cnaditaions_on_failed_ty_trap:
            value_candidate_num = 1
            add_special = False
        else:
            value_candidate_num = self.solution_num
            add_special = True
        stack_values = store.stack
        imm_values = store.imm_values
        constraints = [cond for cond in constraints if cond is not claripy.true]
        check_stack_imm(imm_values, stack_values)
        # if trap, only oneset of type solution is enough
        limit_ty_num = is_ty_trap and exec_config.limit_ty_candidates_on_failed_ty_trap
        ty_solutions = get_type_solutions(stack_values, constraints, limit_ty_num)
        # solve symbols
        stack_solved, imm_solved, stack_symbol_need_solve_bool, imm_symbol_need_solve_bool = solve_symbols(constraints, stack_values, imm_values, value_candidate_num)
        stack_results = get_stack_results(store, value_candidate_num, add_special, stack_values, ty_solutions, stack_solved, stack_symbol_need_solve_bool)
        imm_val_list = get_imm_vals(store, value_candidate_num, imm_values, imm_solved, imm_symbol_need_solve_bool)
        return stack_results, imm_val_list

    def execute(self, cinst, visited_illegalop_ty, exec_config, detect_spec_cov_exec=False):
        assert isinstance(visited_illegalop_ty, list)
        assert isinstance(exec_config, execConfig)
        assert isinstance(cinst, combinedInst)
        assert not exec_config.debug_add_valid
        exec_paths = cinst.skip_repeat_exec_steps.get_all_execution_paths_c_assert()
        result_pairs = []
        has_undefined_ops = False
        to_explore_paths = [[[], exec_path] for exec_path in exec_paths]
        if detect_spec_cov_exec:
            result_dict = {
                'inst_name': cinst.name,
                "all_path_num": 0,
                "reachable_valued_path_num": 0,   # * some paths are unreachable in nature, we skip them
            }
        while to_explore_paths:
            exec_steps, exec_path, valid_steps, valid_path = get_path_and_steps(cinst, to_explore_paths)
            constraints = []
            is_trap = whether_trap(exec_path, exec_steps)
            is_ty_trap = whether_exec_ty_trap(exec_path, exec_steps)
            if is_ty_trap and detect_spec_cov_exec:
                continue
            if detect_spec_cov_exec:
                result_dict['all_path_num'] += 1

            std_logger.debug(f'Test path trap: whether_trap(exec_path, exec_steps): {whether_trap(exec_path, exec_steps)}')
            std_logger.debug(f'is_trap: {is_trap}')
            if exec_config.only_non_trap and is_trap:
                continue
            cur_store = env_store(env_store_config(
                cinst.valid_title_paras, 
                self.template_config,
                cinst,
                visited_illegalop_ty,
                exec_config.consider_illegal_op
            ))
            print(f'cur_store.title_info: {cur_store.title_info}')
            print(f'cur_store.propagate_info: {cur_store.propagate_info}')
            print(f'cur_store.value_relation: {cur_store.value_relation}')
            cur_store.init_title_info(cinst.exec_title_paras)
            r = self.get_exec_result(cinst, cur_store, exec_config, exec_steps, exec_path, constraints, is_ty_trap)
            if len(cur_store.stack):
                std_logger.debug(f'cur_store.stack[0].svalue: {cur_store.stack[0].svalue}')
            std_logger.debug(f'constraints: {constraints}')
            if r is None:
                pass
            else:
                if detect_spec_cov_exec:
                    result_dict['reachable_valued_path_num'] += 1

                _has_undefined_ops, result_pair =r
                result_pairs.append(result_pair)
                if _has_undefined_ops:
                    has_undefined_ops = True
                std_logger.debug(f'======================result_pairs======================')
                std_logger.debug(result_pair)
        if detect_spec_cov_exec:
            spec_cov_logger.debug(f'result_dict: {result_dict}')
            if result_dict['reachable_valued_path_num'] > 1:
                global all_val_d_path_num 
                all_val_d_path_num += result_dict['reachable_valued_path_num']
                global nulti_path_inst_num
                nulti_path_inst_num += 1
            spec_cov_logger.debug(f'all_val_d_path_num: {all_val_d_path_num}')
            spec_cov_logger.debug(f'nulti_path_inst_num: {nulti_path_inst_num}')
        return result_pairs, has_undefined_ops

    def get_exec_result(self, cinst, store, exec_config, exec_steps, exec_path, constraints, _whether_ty_trap):
        pop_ty_seq = get_pop_ty_for_exec_path(cinst, store)
        assert not exec_config.debug_add_valid
        if store.stack_max is None or len(store.stack) <= store.stack_max:
            append_operands(store.stack, pop_ty_seq.num-store.explored_top)
            assert isinstance(pop_ty_seq.num, int)
        if store.stack_max is None:
            store.stack_max = pop_ty_seq.num
        if pop_ty_seq.num-store.explored_top:
            std_logger.debug(f'pop_ty_seq.num-store.stack_top: {pop_ty_seq.num-store.stack_top}')
            std_logger.debug(f'pop_ty_seq.num-store.explored_top: {pop_ty_seq.num-store.explored_top}')
        unreachable, exec_constraints = get_exec_constrains(exec_steps, exec_path, store)
        constraints.extend(exec_constraints)
        std_logger.debug(f'constraints: {constraints}')
        if unreachable or \
                (not _check_path_satisfiable(store, constraints)):
            std_logger.debug(f'UNREACHABLE: {constraints}')
            return None
        else:
            _symbolize_rest_stack(pop_ty_seq.as_expanded_seq, explored_top=store.explored_top, cur_stack=store.stack)
            std_logger.debug(f'current_store.stack: {store.stack}')
            stack_results, imm_val_list = self._solve(store, constraints, is_ty_trap=_whether_ty_trap, exec_config=exec_config)
            opcodes = [tuple(x) for x in store.opcode_candidates]
            result_pair = (stack_results, imm_val_list, opcodes)
            return (len(opcodes) > 1), result_pair


def get_exec_constrains(steps, exec_path, store):
    saved_types = ['LET', 'IF', 'ASSERT', 'POP', 'TRAP', 'ELSE']
    path_with_conditions = get_path_tuple(steps, saved_types, exec_path)
    unreachable = False
    constraints = []
    for step_idx in path_with_conditions:
        if isinstance(step_idx, int):
            step = deepcopy(steps[step_idx])
            step.execute(store=store)
        elif isinstance(step_idx, tuple):
            assert isinstance(step_idx[0], int)
            assert isinstance(step_idx[1], bool)
            step = deepcopy(steps[step_idx[0]])
            cond = step_idx[1]
            constraint = step.execute(store=store, whether_meet=cond)
            std_logger.debug(f'Condition Step: {step}; constraint: {constraint}')
            if is_false_constraint(constraint):
                unreachable = True
                std_logger.debug('break because Unsafisfitable condition')
                break
            else:
                assert constraint is not None, print(step)
                assert not isinstance(constraint, list), print(constraint)
                constraints.append(constraint)
    return unreachable,constraints

def get_pop_ty_for_exec_path(cinst, cur_store):
    if cinst.name in ['br', 'loop', 'if', 'if_04~bt~in_1~05~in_2~0B', 'return']:
        pop_ty_seq = cur_store.outest_output
    else:
        pop_ty_seq = cinst.infer_std_pop_ty_seq
    return pop_ty_seq

def get_path_and_steps(cinst, to_explore_paths):
    valid_steps = []
    exec_steps = deepcopy(cinst.skip_repeat_exec_steps)
    valid_path, exec_path = to_explore_paths.pop()
    return exec_steps,exec_path, valid_steps, valid_path


def _symbolize_rest_stack(infer_std_pop_ty_seq, explored_top, cur_stack):
    need_rewrite = False
    if len(infer_std_pop_ty_seq) > explored_top:
        to_rewrite_tys = infer_std_pop_ty_seq[explored_top:]
        to_rewrite_tys = [valueType(ty_str) if isinstance(ty_str, str) else ty_str  for ty_str in to_rewrite_tys]
        # detect whether need rewrite type
        for ty in to_rewrite_tys:
            if not ty.is_unconstrained_ty():
                need_rewrite = True
                break
    std_logger.debug(f'need_rewrite: {need_rewrite}')
    if need_rewrite:
        assert len(to_rewrite_tys) + explored_top == len(cur_stack), print(f'len(to_append_ty): {len(to_rewrite_tys)},\n explored_top: {explored_top},\n len(cur_stack): {len(cur_stack), cur_stack},\n infer_std_pop_ty_seq: {infer_std_pop_ty_seq}')
        for to_append_idx, ty in enumerate(to_rewrite_tys):
            stack_idx = explored_top + to_append_idx
            cur_stack[stack_idx].type = ty
            cur_stack[stack_idx].generate_svalue()


def get_stack_results(store, value_candidate_num, add_special, stack_values, ty_solutions, stack_solved, stack_symbol_need_solve_bool):
    stack_results = []
    for ty_solution in ty_solutions:
        ty_solution = [val2type_str[i] for i in ty_solution]
        assert len(ty_solution) == len(stack_values)
        stack_result = [None] * len(stack_values)
        stack_solved_idx = 0
        for j in range(len(stack_values)):
            if stack_symbol_need_solve_bool[j]:
                ty_str = ty_solution[j]
                stack_result[j] = candidate_values.from_raw_data_list(ty_str, stack_solved[stack_solved_idx], add_special=True, template_config_for_special_val=store.template_config)
                stack_solved_idx += 1
            else:
                std_logger.debug(f'In get_stack_results,ty_solution[j]: {ty_solution[j]}, value_candidate_num: {value_candidate_num}, add_special: {add_special}')
                stack_result[j] = generate_encoding_for_one_ty(ty_solution[j], value_candidate_num, add_special=add_special)
                std_logger.debug(f'In get_stack_results  stack_result[j]: {stack_result[j]}')
        assert stack_solved_idx == len(stack_solved)
        stack_results.append(stack_result)
    _check_stack_results(store, stack_results)
    return stack_results

def _check_stack_results(store, stack_results):
    for v in stack_results:
        for _ in v:
            assert isinstance(_, candidate_values), print(_, store.stack, type(_))


def get_imm_vals(store, value_candidate_num, imm_values, imm_solved, imm_symbol_need_solve_bool):
    imm_val_list = []
    imm_solved_idx = 0
    for i in range(len(imm_values)):
        cur_imm_ty = imm_values[i].imm_type
        if imm_symbol_need_solve_bool[i]:
            val = candidate_values.from_raw_data_list(cur_imm_ty, imm_solved[imm_solved_idx], add_special=True, template_config_for_special_val=store.template_config)
            imm_solved_idx += 1
        else:
            val = generate_random_encoding_for_imm(imm_values[i], value_candidate_num,template_config_for_special_val=store.template_config)
        assert isinstance(val, candidate_values)
        imm_val_list.append(val)
    for val in imm_val_list:
        assert val.added_special
    assert imm_solved_idx == len(imm_solved)
    return imm_val_list
