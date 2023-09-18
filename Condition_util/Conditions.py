import re
import logging
from Value_util.ValueFactory import FormulaValue
from Value_util import DataAddrInstance, DataInstance, ElemAddrInstance, ElemInstance, FuncAddrInstance, GlobalAddrInstance, GlobalInstance, LengthRefValue, MemAddrInstance, MemInstance, StackValue, TableAddrInstance, TableInstance, constantValue, ValRefValue, LocalAddrInstance
from process_text import process_condition_text
from Condition_util import Condition
from Value_util import Value
import claripy
from env_store_util import check_val_exist, get_val_from_dict_by_name, replace_val
from env_store import env_store
from  data_model import memoryInstanceModel, tableInstanceModel, globalValModel, localValModel, funcModel, dataInstanceModel, elementInstanceModel
from process_text import process_char_bracket_fmt, process_str, raw_processor
from symbol_util import type_str2val
from symbol_util import get_ty_combination_constraint
import logging
from .text_util import relation_str2sg
std_logger = logging.getLogger('std_log')


class IsCondition(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        assert isinstance(elems[1], Value)
        assert isinstance(elems[3], Value)
        assert isinstance(elems[2], bool)
        self.v1 = elems[1]
        self.v2 = elems[3]
        self.z = elems[2]

    def execute(self, store, whether_meet, *args, **kwads):
        assert isinstance(self.v1, Value)
        assert isinstance(self.v2, Value)
        assert isinstance(store, env_store)
        v1_name = self.v1.name
        processed_v1_name = process_char_bracket_fmt(
            raw_processor._process_macro(v1_name))
        if processed_v1_name in store.title_info:
            whether_contain = store.title_info[processed_v1_name] == process_str(self.v2.name)
            if self.z == whether_meet:
                cond_require_contain = whether_contain
            else:
                cond_require_contain = not whether_contain
            if whether_contain == cond_require_contain:
                return claripy.true
            else:
                return claripy.false
        constraints = []
        self.v1.update_name(store.propagate_info)
        v1_name = self.v1.name
        assert check_val_exist(v1_name, store.value_relation), print(v1_name, '<--->', store.value_relation)
        val_1 = get_val_from_dict_by_name(v1_name, store.value_relation)
        assert val_1.has_svalue
        assert isinstance(self.v2, constantValue)
        val_2 = self.v2
        val_2.generate_svalue(store.value_relation)
        if val_2.svalue.ty_value is not None:
            constraints.append(val_1.svalue.ty_value == val_2.svalue.ty_value)
        else:
            constraints.append(val_1.svalue.v_value == val_2.svalue.v_value)

        cond = claripy.And(*constraints)
        if whether_meet:
            return cond
        else:
            return claripy.Not(cond)


class IsDefinedCondition(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        assert isinstance(elems[1], Value)
        self.v = elems[1]

    def execute(self, store, whether_meet, *args, **kwads):
        # we solve it in a simplier way, because it will not be contrained with other symbols
        assert isinstance(store, env_store)
        if 'blocktype' not in raw_processor._process_macro(self.v.name):
            need_generate_tcs = store.get_opcode_candidates(whether_meet)
            # if illegal opcodes have been generated for the current illegal type, return false
            # else, return 
            if need_generate_tcs:
                return claripy.true
            else:
                return claripy.false
        else:
            if whether_meet:
                store.is_defined_block_type = True
                return claripy.true
            else:
                store.is_defined_block_type = False
                return claripy.false


class FormulaCondition(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        self.v = elems[1]

    def execute(self, store, whether_meet, *args, **kwads):
        self.v.update_name(store.propagate_info)
        formula_text = process_condition_text(self.v.name)
        cond = replace_val(store.value_relation, formula_text, False)
        if isinstance(cond, bool):
            cond = bool2claripybool(cond)
        if not whether_meet:
            cond = claripy.Not(cond)
        return cond


class NonZeroCondition(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        assert isinstance(elems[1], Value)
        self.v = elems[1]

    def execute(self, store, whether_meet, *args, **kwads):
        val = get_val_from_dict_by_name(self.v.name, store.value_relation)
        assert val.has_svalue
        if whether_meet:
            return val.svalue.v_value != 0
        else:
            return val.svalue.v_value == 0


class InstructionPartCondition(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        assert isinstance(elems[1], list)
        assert isinstance(elems[2], bool)
        self.v = elems[1]
        self.z = elems[2]

    def execute(self, store, whether_meet, *args, **kwads):
        whether_contain = True
        for v in self.v:
            assert isinstance(v, Value)
            if v.name not in store.title_info:
                whether_contain = False
        cond_require_contain = (self.z == whether_meet)
        return bool2claripybool(whether_contain == cond_require_contain)

class immPresentCondition(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        assert isinstance(elems[1], Value)
        self.v = elems[1]

    def execute(self, store, whether_meet, *args, **kwads):
        raise NotImplementedError

class DifferCondition(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        assert isinstance(elems[1], Value)
        assert isinstance(elems[2], Value)
        self.v1 = elems[1]
        self.v2 = elems[2]

    def execute(self, *args, **kwads):
        assert 0


class CompareCondition(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        assert isinstance(elems[1], Value)
        assert isinstance(elems[4], Value)
        assert isinstance(elems[2], bool)
        assert isinstance(elems[3], str)
        self.v1 = elems[1]
        self.v2 = elems[4]
        self.z = elems[2]
        self.relation = elems[3]

    def execute(self, store, whether_meet, *args, **kwads):
        assert isinstance(store, env_store)
        # right part
        assert isinstance(self.v2, LengthRefValue)
        self.v2.generate_svalue(store.value_relation)
        right_val = self.v2.svalue.v_value
        sg = relation_str2sg(self.relation)
        # left part
        assert isinstance(self.v1, (ValRefValue, FormulaValue)), 'self.v1 : {}'.format(self.v1)
        self.v1.update_name(store.propagate_info)
        self.v1.generate_svalue(store.value_relation)
        left_symbol = self.v1.svalue.v_value
        std_logger.debug('self.v1 : {}'.format(self.v1))
        std_logger.debug('left_symbol : {}'.format(left_symbol))
        std_logger.debug('processed right_val str : {}'.format(right_val))
        cond = eval(f'left_symbol {sg} right_val')
        std_logger.debug('cond : {}'.format(cond))
        std_logger.debug(f'self.z whether_meet: {self.z} {whether_meet}')
        if self.z != whether_meet:
            return claripy.Not(cond)
        else:
            return cond

# def _get_


class StackCondition(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        assert isinstance(elems[1], bool), print(elems)
        assert isinstance(elems[2], Value)
        self.z = elems[1]
        self.v = elems[2]
        num = self.v.num
        self.val_num = num
        self.has_constraint_between_vals=False

    def execute(self, store, whether_meet, *args, **kwads):
        assert self.z  # We observe that self.z always holds true
        val = self.v
        if val.type.need_infer:
            val.update_type_by_title_paras(store.propagate_info)
        stack = store.stack
        if isinstance(self.val_num, int) :
            num = self.val_num
        assert isinstance(num, int), print(num, store.value_relation)
        ori_stack_length = len(stack)
        assert store.stack_top <= ori_stack_length
        unexplored_stack_len = ori_stack_length - store.stack_top
        to_compare_num = min(num, unexplored_stack_len)
        # compare
        constraints = []
        all_self_constrains = [claripy.true]
        val.generate_svalue()
        std_logger.debug(f'unexplored_stack_len: {unexplored_stack_len}, ori_stack_length: {ori_stack_length}, store.stack_top: {store.stack_top}')
        std_logger.debug(f'to_compare_num: {to_compare_num}')
        store.explored_top += to_compare_num
        for stack_offset in range(to_compare_num):
            std_logger.debug(f'In StackCondition.execute first for val.svalue.ty_value: {val.svalue.ty_value}')
            cur_stack_v = stack[stack_offset+store.stack_top]
            assert cur_stack_v.has_svalue
            assert cur_stack_v.name == 'any', print(cur_stack_v)
            v_type_unconstrained = val.type.is_unconstrained_ty()
            cur_stack_v_type_unconstrained = cur_stack_v.type.is_unconstrained_ty()

            if isinstance(cur_stack_v.svalue.ty_value, (claripy.ast.bv.BV, int)) and isinstance(val.svalue.ty_value, int):
                assert val.type._type in ['i32', 'i64', 'f32', 'f64', 'v128']
                if whether_meet and cur_stack_v_type_unconstrained:
                    # * to facilitate debugging
                    cur_stack_v.type = val.type
                    cur_stack_v.generate_svalue()    
                c = cur_stack_v.svalue.ty_value == val.svalue.ty_value
                if isinstance(c, bool):
                    c = bool2claripybool(c)
                constraints.append(c)
            elif v_type_unconstrained:
                constraints.append(claripy.true)
            elif self.v.type.detail_info == 'reference value':
                c, _ = get_ty_combination_constraint('reference type', cur_stack_v.svalue.ty_value)
                std_logger.debug(f"reference value branch c: {c}")
                constraints.append(c)
            else:
                raise Exception("Unexpected situation")
            all_self_constrains.extend(val.svalue.self_constraints)
        if (self.z != whether_meet) and val.type.is_unconstrained_ty():
            if store.stack_max == len(stack):
                stack.pop()
        std_logger.debug('StackCondition.execute constraints: {}'.format(constraints))
        constraints = claripy.And(*constraints)
        if whether_meet != self.z: 
            constraints = claripy.Not(constraints)
        all_self_constrains = claripy.And(*all_self_constrains)
        constraints = claripy.And(constraints, all_self_constrains)
        std_logger.debug('StackCondition.execute stack: {}'.format(stack))
        return constraints


def bool2claripybool(b):
    if b:
        return claripy.true
    else:
        return claripy.false


class ExistCondition(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        assert isinstance(elems[1], Value)
        self.v = elems[1]

    def execute(self, store, whether_meet, *args, **kwads):
        val = self.v
        std_logger.debug('ExistCondition.execute val: {}'.format(val))
        std_logger.debug('ExistCondition.execute self.v.index: {}'.format(self.v.index))
        idx_constraint = None
        if isinstance(val, (GlobalInstance, MemInstance, TableInstance, ElemInstance, DataInstance)):
            cond = claripy.true
        else:
            idx_val = self.v.index
            idx_val.generate_svalue(store.value_relation)
            idx_symbol = idx_val.svalue.v_value
            if isinstance(val, GlobalAddrInstance):
                cond =  store.template_config['global_len'] > idx_symbol
                store.global_obj[val.index_name] =globalValModel()
            # Local Instance
            elif isinstance(val, LocalAddrInstance):
                cond = store.template_config['local_len'] > idx_symbol
                store.global_obj[val.index_name] =localValModel()
            # func
            elif isinstance(val, FuncAddrInstance):
                cond = store.template_config['func_num'] > idx_symbol
                store.global_obj[val.index_name] =funcModel()
            # Memory
            elif isinstance(val, MemAddrInstance):
                cond = store.template_config['mem_num'] > idx_symbol
                instance = memoryInstanceModel()
                store.memory_obj[val.index_name] = instance
                idx_constraint = get_constraints_pair(idx_symbol, instance.len, store.template_config['mem_lens'])
            # table
            elif isinstance(val, TableAddrInstance):
                cond = store.template_config['table_num'] > idx_symbol
                instance = tableInstanceModel()
                store.table_obj[val.index_name] = instance
                idx_constraint = get_constraints_pair(idx_symbol, instance.len, store.template_config['table_lens'])
            # elem
            elif isinstance(val, ElemAddrInstance):
                cond = store.template_config['elem_num'] > idx_symbol
                instance = elementInstanceModel()
                store.elem_obj[val.index_name] = instance
                idx_constraint = get_constraints_pair(idx_symbol, instance.len, store.template_config['elem_lens'])
            # data
            elif isinstance(val, DataAddrInstance):
                cond = store.template_config['data_num'] > idx_symbol
                instance = dataInstanceModel()
                store.data_obj[val.index_name] = instance
                idx_constraint = get_constraints_pair(idx_symbol, instance.len, store.template_config['data_lens'])
            std_logger.debug('ExistCondition.execute cond: {}'.format(cond))
        # cond = claripy.And(*[cond])
        assert not isinstance(cond, list)

        if whether_meet and idx_constraint is not None:
            cond = claripy.And(cond, idx_constraint)
        if not whether_meet:
            cond = claripy.Not(cond)
        return cond


def get_constraints_pair(val1, val2, len_list):
    conds = [claripy.false]
    for len1, len2 in enumerate(len_list):
        cond = claripy.And(val1 == len1, val2 == len2)
        conds.append(cond)
    return claripy.Or(*conds)


class StackContainCondition(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        assert isinstance(elems[1], Value)
        self.v = elems[1]

    def execute(self, store, whether_meet, *args, **kwads):
        assert 0, print(self.v, self.v.num)
        num_str = self.v.num
        at_least_p = re.compile(r'at least :math:`(.*)`$')
        r = at_least_p.findall(num_str)
        assert r
        num_str = r[0]
        left_str = replace_val(store.value_relation, num_str, True)
        cond = claripy.ULE(left_str, store.control_stack_len)
        if whether_meet:
            return cond
        else:
            return claripy.Not(cond)

class StackTopSameTypeCondition(StackCondition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        self.has_constraint_between_vals=True

    def execute(self, store, whether_meet, *args, **kwads):
        constraints =  super().execute(store, True, *args, **kwads)
        assert not isinstance(constraints, list)
        new_constraints = [constraints]
        std_logger.debug("In StackTopSameTypeCondition.execute, whether_meet: {} =====".format(whether_meet))
        std_logger.debug(f"type(new_constraints): {type(new_constraints)}")
        std_logger.debug(f"new_constraints: {new_constraints}")
        for i in range(1, self.val_num):
            assert isinstance(store.stack[-i], StackValue)
            assert isinstance(store.stack[-i-1], StackValue)
            val1_ty = store.stack[-i].svalue.ty_value
            val2_ty = store.stack[-i-1].svalue.ty_value
            new_constraints.append(val1_ty==val2_ty)
        cond = claripy.And(*new_constraints)
        if not whether_meet:
            cond = claripy.Not(cond)
        return cond


def _get_line_constraints(val, lane_num, lim_val, sg):
    bw = 128 // lane_num
    mask = 2 ** bw -1
    constraints = []
    s = f'((val>>(bw*i)) & mask) {sg} lim_val'
    for i in range(lane_num):
        constraints.append(eval(s))
    return claripy.And(*constraints)


class SIMDValCondition(Condition):
    def __init__(self, line, elems=None) -> None:
        super().__init__(line, elems)
        self.v = elems[1]
        self.limit = elems[2]
        self.sg = elems[3]

    def execute(self, store, whether_meet, *args, **kwads):
        assert isinstance(store, env_store)
        assert isinstance(self.v, ValRefValue), print(self.v)
        assert isinstance(self.limit, constantValue), print(self.limit)
        val = get_val_from_dict_by_name(self.v.name, store.value_relation)
        if not self.limit.has_svalue:
            self.limit.generate_svalue()
        if not val.has_svalue:
            val.generate_svalue()
        assert val.simd_lane_num is not None
        para = {
            'val': val.svalue.v_value,
            'lane_num': val.simd_lane_num,
            'lim_val': self.limit.svalue.v_value,
            'sg': self.sg
        }
        constraints = _get_line_constraints(**para)
        if whether_meet:
            return constraints
        else:
            return claripy.Not(constraints)


class MachineDeterminedCondition(Condition):
    def __init__(self, line, elems=None) -> None:
        super().__init__(line, elems)
        self.line = line

    def execute(self, store, whether_meet, *args, **kwads):
        return claripy.true
