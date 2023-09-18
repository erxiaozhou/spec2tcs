from .line_extractor import extract_exec_line_elements
from .StepFactory import AssertStep, ElseStep, IfStep, RepeatStep, ReturnStep, TrapStep
from .StepFactory import emit_lines_from_paras
from .Step import Step
from .valid_line_extractor import extract_valid_line_elements
import re


class Steps(list):
    @classmethod
    def from_exec_paragraph(cls, paragraph):
        step_paras = []
        lines = paragraph.split('\n')
        for line in lines:
            step_para = extract_exec_line_elements(line)
            step_paras.append(step_para)
        steps = emit_lines_from_paras(step_paras)
        return cls(steps)

    @classmethod
    def from_valid_inst_text(cls, inst_text):
        step_lines = _extract_step_lines_from_inst_text(inst_text)
        paras = [extract_valid_line_elements(line) for line in step_lines]
        steps = emit_lines_from_paras(paras)
        return cls(steps)

    def __repr__(self):
        return '\n'.join(repr(x) for x in self)

    def as_data(self):
        return [repr(x) for x in self]

    def get_blocks(self):
        block_groups = []
        last_h = 0
        current_block_group = []

        for i, s in enumerate(self):
            assert isinstance(s, Step)
            if last_h != s.hier:
                block_groups.append(current_block_group)
                current_block_group = []
                last_h = s.hier
            current_block_group.append(i)
        block_groups.append(current_block_group)
        return block_groups

    def organize_steps(self):
        # get blocks
        block_groups = self.get_blocks()

        hier_log = []
        for i, group in enumerate(block_groups):
            assert len(group)
            step_index = group[0]
            block_leading_step = self[step_index]
            hier_log.append(block_leading_step.hier)

        k_followed_by_v = {}
        for i, h in enumerate(hier_log):
            if h >= 1:
                if h > hier_log[i-1]:
                    last_step_in_last_block = block_groups[i-1][-1]
                    k = last_step_in_last_block
                    k_followed_by_v[k] = block_groups[i]
        self.k_followed_by_v = k_followed_by_v
        return k_followed_by_v

    def get_graph(self):
        blocks = self.get_blocks()
        hiers = [self[b[0]].hier for b in blocks]
        tail_jump_relation = {}
        block_num = len(blocks)
        for block_idx in range(block_num):
            block = blocks[block_idx]
            current_hier = hiers[block_idx]
            tail_line_idx = block[-1]
            tail_line = self[tail_line_idx]
            if isinstance(tail_line, IfStep):
                assert self[tail_line_idx+1].hier == current_hier + 1
                jump_relation = {}
                # condition is True
                jump_relation[1] = tail_line_idx + 1
                contain_else = False
                for search_idx in range(block_idx+2, block_num):
                    block_first_line_idx = blocks[search_idx][0]
                    if hiers[search_idx] <= current_hier:
                        if isinstance(self[block_first_line_idx], ElseStep):
                            contain_else = True
                            jump_relation[0] = block_first_line_idx
                        else:
                            if contain_else:
                                jump_relation['after_if_structure'] = block_first_line_idx
                            else:
                                jump_relation[0] = block_first_line_idx
                            break
                if contain_else and 'after_if_structure' not in jump_relation:
                    jump_relation['after_if_structure'] = None
                if 0 not in jump_relation:
                    jump_relation[0] = None
                # ----- ----
                if jump_relation.get(0) is None:
                    jump_relation[0] = -1
                tail_jump_relation[tail_line_idx] = jump_relation
            elif isinstance(tail_line, ElseStep):
                tail_jump_relation[tail_line_idx] = tail_line_idx + 1
            elif isinstance(tail_line, TrapStep):
                tail_jump_relation[tail_line_idx] = None
            elif isinstance(tail_line, ReturnStep):
                tail_jump_relation[tail_line_idx] = None
            else:
                block_first_line_idx = blocks[block_idx][0]
                jump_relation = {}
                if tail_line_idx + 1 == len(self):
                    tail_jump_relation[tail_line_idx] = None
                else:
                    last_block = blocks[block_idx-1]
                    last_line_idx = last_block[-1]
                    if isinstance(self[last_line_idx], IfStep):
                        if_jump_relation = tail_jump_relation[last_line_idx]
                        if 'after_if_structure' not in if_jump_relation:
                            tail_jump_relation[tail_line_idx] = tail_line_idx + 1
                        else:
                            tail_jump_relation[tail_line_idx] = if_jump_relation['after_if_structure']
                    else:
                        tail_jump_relation[tail_line_idx] = tail_line_idx + 1
        assert block_num == len(tail_jump_relation)
        return tail_jump_relation

    def get_all_execution_paths_c_assert(self):
        jump_relation = self.get_graph() 
        paths = _explore_dict_path_with_assert(jump_relation, self)
        return paths

    def get_all_execution_paths_01_failed_assert(self):
        jump_relation = self.get_graph()
        paths = _explore_dict_path_with_1or0_failed_assert(jump_relation, self)
        return paths


def _explore_dict_path_with_assert(dict_, steps):
    assert isinstance(steps, Steps)
    results = []
    un_explored_list = []
    start_id = 0
    un_explored_list.append([start_id])
    while un_explored_list:
        current_path = un_explored_list.pop()
        last_step_idx = [idx for idx in current_path if (isinstance(idx, int) and (not isinstance(idx, bool)))][-1]
        if isinstance(steps[last_step_idx], AssertStep):
            current_path_1 = current_path.copy()
            current_path_1.append(False)
            results.append(current_path_1)
            current_path_2 = current_path.copy()
            current_path_2.append(True)
            if last_step_idx + 1 < len(steps) and (dict_.get(last_step_idx, 'other') is not None):
                current_path_2.append(last_step_idx+1)
                un_explored_list.append(current_path_2)
            else:
                results.append(current_path_2)
        elif last_step_idx not in dict_:
            current_path.append(last_step_idx+1)
            un_explored_list.append(current_path)
        else:
            possible_paths = dict_[current_path[-1]]
            if possible_paths is None:
                results.append(current_path)
            elif isinstance(possible_paths, int):
                current_path.append(possible_paths)
                un_explored_list.append(current_path)
            elif isinstance(possible_paths, dict):
                for k, v in possible_paths.items():
                    current_path_ = current_path.copy()
                    if k == 0:
                        current_path_.append(False)
                    elif k == 1:
                        current_path_.append(True)
                    else:
                        continue
                    current_path_.append(v)
                    un_explored_list.append(current_path_)
    return results


def _explore_dict_path_with_1or0_failed_assert(dict_, steps):
    assert isinstance(steps, Steps)
    results = []
    un_explored_list = []
    start_id = 0
    un_explored_list.append([start_id])
    while un_explored_list:
        current_path = un_explored_list.pop()
        last_step_idx = [idx for idx in current_path if (isinstance(idx, int) and (not isinstance(idx, bool)))][-1]
        if isinstance(steps[last_step_idx], AssertStep):
            current_path_1 = current_path.copy()
            current_path_1.append(False)
            # un_explored_list.append(current_path_1)
            current_path_2 = current_path.copy()
            current_path_2.append(True)
            if last_step_idx + 1 < len(steps) and (dict_.get(last_step_idx, 'other') is not None):
                current_path_2.append(last_step_idx+1)
                un_explored_list.append(current_path_2)
                current_path_1.append(last_step_idx+1)
                un_explored_list.append(current_path_1)
            else:
                results.append(current_path_2)
                results.append(current_path_1)
        elif last_step_idx not in dict_:
            current_path.append(last_step_idx+1)
            un_explored_list.append(current_path)
        else:
            possible_paths = dict_[current_path[-1]]
            if possible_paths is None:
                results.append(current_path)
            elif isinstance(possible_paths, int):
                current_path.append(possible_paths)
                un_explored_list.append(current_path)
            elif isinstance(possible_paths, dict):
                for k, v in possible_paths.items():
                    current_path_ = current_path.copy()
                    if k == 0:
                        current_path_.append(False)
                    elif k == 1:
                        current_path_.append(True)
                    else:
                        continue
                    current_path_.append(v)
                    un_explored_list.append(current_path_)
    # 
    to_save_path_idx = []
    for path_idx, path in enumerate(results):
        # count the False follow AssertStep
        false_follow_assert_step = 0
        for idx, elem in enumerate(path):
            if isinstance(elem, bool):
                if not elem:
                    if isinstance(steps[path[idx-1]], AssertStep):
                        false_follow_assert_step += 1
        if false_follow_assert_step <= 1:
            to_save_path_idx.append(path_idx)
    results = [results[idx] for idx in to_save_path_idx]
    return results

def get_steps_skip_repeat(steps):
    assert isinstance(steps, Steps)
    indexs_to_skip = []
    in_repeat = False
    for idx, step in enumerate(steps):
        if isinstance(step, RepeatStep):
            in_repeat = True
            repeat_hier = step.hier
            indexs_to_skip.append(idx)
            continue
        if in_repeat:
            if step.hier > repeat_hier:
                indexs_to_skip.append(idx)
            else:
                in_repeat = False
    print(indexs_to_skip)
    steps = Steps([step for idx, step in enumerate(steps) if idx not in indexs_to_skip])
    return steps

def _extract_step_lines_from_inst_text(inst_text):
    assert inst_text.count('\n.. math::\n') == 1, print(inst_text)
    p = r'^(.*?)(?=\.\. math::\n).*$'
    steps_text = re.compile(p, re.S).findall(inst_text)[0]
    step_lines = [line for line in steps_text.split('\n') if line]
    p = re.compile(r' *\*')
    new_lines = []
    append_next_line = False
    for line in step_lines:
        if line.endswith(','):
            append_next_line = True
            new_lines.append(line)
        else:
            if append_next_line:
                new_lines[-1] += (' ' + line.strip(' '))
            else:
                new_lines.append(line)
            append_next_line = False
    for line in new_lines:
        assert p.findall(line), print(line)
    return new_lines
