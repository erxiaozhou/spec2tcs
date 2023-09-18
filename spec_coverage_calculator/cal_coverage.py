from copy import deepcopy
from Condition_util import IsDefinedCondition, StackCondition
from Condition_util.append_operand import append_operands
from Step_util import AssertStep, IfStep
from combinedInst_util import combinedInst
from env_store import env_store, env_store_config
from se_inst_env_util import get_template
from se_inst_env_util.se_inst import get_exec_constrains, get_pop_ty_for_exec_path
from se_inst_env_util.se_inst_exec_util import get_path_tuple


class coverage_Env:
    def __init__(self, tc_mode):
        self.template_config = get_template(tc_mode)

    def execute(self, cinst, visited_illegalop_ty=None):
        assert isinstance(cinst, combinedInst)
        steps = cinst.skip_repeat_exec_steps
        paths = cinst.skip_repeat_exec_steps.get_all_execution_paths_c_assert()
        saved_types = ['LET', 'IF', 'ASSERT', 'POP', 'TRAP', 'ELSE']
        reachable_paths = []
        path_num_info = {
            'skipped_paths': 0,
            'unreachable_paths': 0,
            'reached_paths': 0,
            'ori_paths':len(paths),
            'filtered_path_num':{
            'opcode': 0,
            'type':0
            }
        }
        while paths:
            path = paths.pop()
            # cut useless steps
            path_with_conditions =get_path_tuple(steps, saved_types, path)
            skip_this_path = False
            for p in path_with_conditions:
                if isinstance(p, int):
                    cur_step = steps[p]
                elif isinstance(p, tuple):
                    cur_step = steps[p[0]]
                    is_satisfied = p[1]
                    assert isinstance(is_satisfied, bool)
                if isinstance(cur_step, AssertStep):
                    cond = cur_step.condition
                    if isinstance(cond, StackCondition) and (not is_satisfied):
                        skip_this_path = True
                        path_num_info['filtered_path_num']['type'] += 1
                if isinstance(cur_step, IfStep):
                    cond = cur_step.condition
                    if isinstance(cond, list) and len(cond) == 1:
                        if isinstance(cond[0], IsDefinedCondition) and (not is_satisfied):
                            skip_this_path = True
                            path_num_info['filtered_path_num']['opcode'] += 1
            if skip_this_path:
                path_num_info['skipped_paths'] += 1
                continue
            # ===================================================================
            store_config = env_store_config(deepcopy(cinst.exec_title_paras), self.template_config, cinst, [], False)
            current_store = env_store(store_config)
            # 
            pop_ty_seq = get_pop_ty_for_exec_path(cinst, current_store)
            if current_store.stack_max is None or len(current_store.stack) <= current_store.stack_max:
                append_operands(current_store.stack, pop_ty_seq.num-current_store.explored_top)
                assert isinstance(pop_ty_seq.num, int)
            if current_store.stack_max is None:
                current_store.stack_max = pop_ty_seq.num
            unreachable, constraints = get_exec_constrains(deepcopy(cinst.skip_repeat_exec_steps), path, current_store)
            if unreachable:
                path_num_info['unreachable_paths'] += 1
            else:
                path_num_info['reached_paths'] += 1
                reachable_paths.append([constraints, current_store])
        assert sum(path_num_info['filtered_path_num'].values()) == path_num_info['skipped_paths']
        assert path_num_info['ori_paths'] == path_num_info['skipped_paths'] + path_num_info['unreachable_paths'] + path_num_info['reached_paths'], print(path_num_info)
        return reachable_paths
