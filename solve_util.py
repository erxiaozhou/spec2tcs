import logging
import claripy
from Value_util.ImmValue import blocktype_ph_tmp
from symbol_util import type_str2val
std_logger = logging.getLogger('std_log')

def check_stack_imm(imm_values, stack_values):
    for v in imm_values:
        assert v.has_svalue, print(v)
        assert not v.has_symbol_ty
    for v in stack_values:
        assert v.has_svalue
        if v.type.is_unconstrained_ty():
            assert v.has_symbol_ty


def get_all_self_constraints(imm_values, stack_values):
    all_self_constraints = []
    for v in imm_values + stack_values:
        all_self_constraints.extend(v.svalue.self_constraints)
    return all_self_constraints


def check_satisfiable(constraints):
    s = claripy.Solver()
    for cons in constraints:
        s.add(cons)
    return s.satisfiable()


def get_type_solutions(stack_values, constraints, limit_ty_num):
    type_solver = claripy.Solver()
    all_self_constraints = []
    for v in stack_values:
        self_constraints = v.svalue.self_constraints
        if self_constraints is not None:
            for cons in self_constraints:
                type_solver.add(cons)
                all_self_constraints.append(cons)
    print('all_self_constraints\n', all_self_constraints)
    print('all_constraints\n', all_self_constraints+constraints)

    for cons in constraints:
        type_solver.add(cons)
    stack_ty_values = [v.svalue.ty_value for v in stack_values]
    stack_ty_is_syb = [v.has_symbol_ty for v in stack_values]
    to_solve_ty_syb = [v.svalue.ty_value for v in stack_values if v.has_symbol_ty]
    type_num_constraints = [s< len(type_str2val) for s in to_solve_ty_syb]
    assert type_solver.satisfiable(), print(constraints + all_self_constraints+type_num_constraints)
    for cons in type_num_constraints:
        type_solver.add(cons)
    if limit_ty_num:
        ty_solution_num = 1
    else:
        ty_solution_num = 10 ** len(to_solve_ty_syb)
    solved_result = type_solver.batch_eval(to_solve_ty_syb, ty_solution_num)

    ty_solutions = []
    for solved_solution in solved_result:
        _idx=0
        concrete_ty_soluiton = [x for x in stack_ty_values]
        for i in range(len(stack_ty_is_syb)):
            if stack_ty_is_syb[i]:
                concrete_ty_soluiton[i] = solved_solution[_idx]
                _idx += 1
            else:
                assert isinstance(stack_ty_is_syb[i], int)
        assert _idx == len(solved_solution)
        ty_solutions.append(concrete_ty_soluiton)
    return ty_solutions


def solve_symbols(constraints, stack_values, imm_values, solve_num):
    s = claripy.Solver()
    for cond in constraints:
        s.add(cond)
    assert s.satisfiable()
    symbol_relation = s.independent_constraints()
    to_solve_symbols = [v.svalue.v_value for v in stack_values] + [v.svalue.v_value for v in imm_values]
    if len(constraints) == 0 and len(to_solve_symbols) != 0:
        std_logger.warning("No constraints for symbols, please check!")
    stack_symbol_need_solve_bool = [(not _is_independent(v.svalue.v_value, symbol_relation)) for v in stack_values]
    imm_symbol_need_solve_bool = [(not _is_independent(v.svalue.v_value, symbol_relation)) for v in imm_values]
    to_solve_symbols = [symbol for symbol in to_solve_symbols if not _is_independent(symbol, symbol_relation)]
    stack_need_solve_num = len([1 for b in stack_symbol_need_solve_bool if b])
    imm_need_solve_num = len([1 for b in imm_symbol_need_solve_bool if b])
    # add self constraints
    for v in stack_values+imm_values:
        assert v.has_svalue
        self_constraints = v.svalue.self_constraints
        if self_constraints is not None:
            for cons in self_constraints:
                s.add(cons)

    stack_solved, imm_solved = _solve_core(to_solve_symbols, s, solve_num, stack_need_solve_num, imm_need_solve_num)
    return stack_solved, imm_solved, stack_symbol_need_solve_bool, imm_symbol_need_solve_bool


def _is_independent(symbol, symbol_relation):
    if isinstance(symbol, str):
        assert symbol == 'any'
        return True
    if isinstance(symbol, blocktype_ph_tmp):
        return True
    if symbol is None:
        return True
    names = []
    symbol_name = symbol._encoded_name.decode()
    for relation in symbol_relation:
        cur_names = list(relation[0])
        names.extend(cur_names)
    if symbol_name in names:
        return False
    else:
        return True


def _solve_core(to_solve_symbols, solver, solve_num, stack_num, imm_num):
    if len(to_solve_symbols):
        solved_result = solver.batch_eval(to_solve_symbols, solve_num)
        std_logger.debug('solved_result: {}'.format(solved_result))
        stack_result = []
        imm_result = []
        for i in range(stack_num):
            stack_result.append([])
        for i in range(imm_num):
            imm_result.append([])
        for solved_ in solved_result:
            for i, elem in enumerate(solved_[:stack_num]):
                stack_result[i].append(elem)
            for i, elem in enumerate(solved_[stack_num:]):
                imm_result[i].append(elem)
        return stack_result, imm_result
    else:
        return [], []
