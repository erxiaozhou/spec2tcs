import claripy
from Condition_util import StackCondition, StackTopSameTypeCondition
from Step_util import AssertStep, TrapStep
from Condition_util.validCondition import typeConds

def is_false_constraint(constraint):
    assert isinstance(constraint, claripy.ast.bool.Bool), print(constraint, type(constraint))
    if isinstance(constraint, list):
        for c in constraint:
            if c is claripy.false:
                return True
    elif constraint is claripy.false:
        return True
    else:
        return False


def path_tuple(path):
    new_path = []
    for path_element in path:
        if isinstance(path_element, bool):
            new_path[-1] = (new_path[-1], path_element)
        elif isinstance(path_element, int) and not isinstance(path_element, bool):
            new_path.append(path_element)
        else:
            assert 0
    return new_path


def whether_trap(path, steps):
    if len(path) == 0:
        return False
    for e in path:
        assert isinstance(e, (int, bool))
    idxs = [p for p in path if not isinstance(p, bool)]
    last_idx = idxs[-1]
    for idx, path_step_idx in enumerate(path):
        if (not isinstance(path_step_idx, bool)) and isinstance(steps[path_step_idx], AssertStep):
            assert isinstance(path[idx+1], bool), print(path[idx+1], path, idx)
            if path[idx+1] is False:
                return True
    return (path[-1] is False) or isinstance(steps[last_idx], TrapStep)


def whether_exec_ty_trap(path, steps):
    if len(path) == 0:
        return False
    for e in path:
        assert isinstance(e, (int, bool))
    idxs = [p for p in path if isinstance(p, int) and not isinstance(p, bool)]
    last_idx = idxs[-1]
    if path[-1] is False:
        assert isinstance(steps[last_idx], AssertStep), print('===\n', steps, path)
        if isinstance(steps[last_idx].condition, (StackCondition, StackTopSameTypeCondition)):
            return True
        else:
            return False
    else:
        return False

def whether_valid_ty_trap(path, steps):
    if len(path) == 0:
        return False
    idxs = [p for p in path if isinstance(p, int) and not isinstance(p, bool)]
    last_idx = idxs[-1]
    if path[-1] is False:
        assert isinstance(steps[last_idx], AssertStep)
        return isinstance(steps[last_idx].condition, (StackCondition, StackTopSameTypeCondition) + typeConds)
    else:
        return False


def has_undetermined_constraints(constraints):
    assert isinstance(constraints, list)
    constraints = [con for con in constraints if con is not claripy.true]
    if len(constraints):
        return True
    else:
        return False


def get_path_tuple(steps, saved_types, path):
    path = cut_exec_path(path, steps, saved_types)
    path = cut_step_after_ctr(path, steps, save_execute=False)
    path_with_conditions = path_tuple(path)
    return path_with_conditions


def cut_exec_path(path, steps, saved_types):
    # ['LET', 'IF', 'ASSERT', 'POP', 'TRAP', 'ELSE', 'EXECUTE']
    saved_elems = []
    for e in path:
        if isinstance(e, bool):
            saved_elems.append(e)
        elif steps[e].type in saved_types:
            saved_elems.append(e)
    return saved_elems


def cut_step_after_ctr(path, steps, save_execute=False):
    trap_idxs = [i for i in range(len(path)) if (not isinstance(path[i], bool)) and steps[path[i]].type=='TRAP']
    assert len(trap_idxs) <= 1
    if len(trap_idxs) == 1:
        trap_idx = trap_idxs[0]
        assert trap_idx==0 or (isinstance(path[trap_idx-1], bool) and steps[path[trap_idx-2]].type=='IF') or steps[trap_idx-1].type=='ELSE', print(trap_idx, [steps[i].type  if (not isinstance(i, bool)) else i for i in path],  steps[path[trap_idx-2]].type)
    # check part ========================================

    last_idx = None
    save_types = ['IF', 'ELSE', 'TRAP']
    if save_execute:
        save_types.append('EXECUTE')
    for i, step_idx in enumerate(path):
        if isinstance(step_idx, bool):
            last_idx = i
        else:
            step_type = steps[step_idx].type
            if step_type in save_types:
                last_idx = i
    if last_idx is None:
        return path
    else:
        return path[:last_idx+1]
