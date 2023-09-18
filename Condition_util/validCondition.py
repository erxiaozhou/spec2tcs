from Condition_util.text_util import relation_str2sg
from Value_util import StackValue
from Value_util.ValueFactory import FormulaValue, ModuleInstance
from env_store_util import replace_val
from process_text import unwrap_math
from process_text.process_str_parts_in_steps import process_condition_text
from .Condition import Condition
from .Conditions import ExistCondition
from .match_validCondition_util import match_must_ty_direct_cond, match_must_ty_from_store_cond, match_must_ty_infered_cond
from Value_util import generate_Value_from_common_line
import re
from Value_util import ValRefValue, valueType
import logging
logger = logging.getLogger('std_log')
import claripy
from .append_operand import append_operands
from symbol_util import type_str2val
from symbol_util import get_ty_combination_constraint
logger = logging.getLogger('std_log')

class directValidTypeCond(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        self.input_vals = elems[1]
        self.output_vals = elems[2]

    def execute(self, store, whether_meet, *args, **kwargs):
        logger.debug('In directValidTypeCond.execute')
        input_vals = self.input_vals[::-1][:]
        for val in input_vals:
            assert isinstance(val, StackValue)
            if val.type.need_infer:
                val.update_type_by_title_paras(store.propagate_info)
        # all input vals are of unconstrained type
        need_mismatch_op_num = (len(input_vals) == len([v for v in input_vals if v.type.is_unconstrained_ty()]) > 1) and (not whether_meet)

        constraints = []
        for val in input_vals:
            if whether_meet:
                new_val = StackValue.generate_value_with_type(val.type)
            else:
                new_val = StackValue.generate_value_with_any_type()
            new_val.generate_svalue()
            c = get_constraint(new_val, val)
            store.stack.append(new_val)
            constraints.append(c)

        if need_mismatch_op_num:
            store.stack.pop()
        store.explored_top = len(store.stack)
        store.stack_max = len(store.stack)

        if len(constraints) == 0:
            constraints = claripy.true
        else:
            constraints = claripy.And(*constraints)
        if not whether_meet:
            constraints = claripy.Not(constraints)

        logger.debug(f'In directValidTypeCond.execute, store.stack_max: {store.stack_max}')
        logger.debug(f'In directValidTypeCond.execute, constraints: {constraints}')
        logger.debug(f'In directValidTypeCond.execute, whether_meet: {whether_meet}')
        if len(self.input_vals):
            assert constraints is not claripy.false
        return constraints

def get_constraint(new_val, val):
    if val.type._type in type_str2val:
        c = new_val.svalue.ty_value == type_str2val[val.type._type]
    elif val.type.detail_info=='reference value':
        assert val.type._type == 'other'
        c, is_unconstrained = get_ty_combination_constraint('reference value', new_val.svalue.ty_value)
    elif val.type.is_unconstrained_ty():
        return claripy.true
    else:
        raise ValueError(f'In directValidTypeCond.execute, val.type._type: {val.type._type}')
    return c

class fromStoreValidTypeCond(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        self.refer_ty_val = elems[1]

    def execute(self, store, whether_meet, *args, **kwargs):
        cond = claripy.true
        if not whether_meet:
            cond = claripy.Not(cond)
        return cond

class inferedValidTypeCond(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        self.input_vals = elems[1]
        assert len(self.input_vals)
        self.output_vals = elems[2]
        self.is_seq = elems[3]
        self.types = elems[4]
        self.referred_ty_strs = elems[5]

    def execute(self, store, whether_meet, *args, **kwargs):
        # raise NotImplementedError
        logger.debug('In inferedValidTypeCond.execute')
        input_vals = self.input_vals[::-1][:]
        assert not self.is_seq
        all_unconstrained = (len(input_vals) > 0)
        constraints = []
        for val in input_vals:

            if val.type.need_infer:
                val.update_type_by_title_paras(store.propagate_info)
            if whether_meet:
                new_val = StackValue.generate_value_with_type(val.type)
            else:
                new_val = StackValue.generate_value_with_any_type()
            assert isinstance(new_val, StackValue)
            new_val.generate_svalue()
            if val.type.need_infer:
                if val.type.type_sig in self.referred_ty_strs:
                    logger.debug('In inferedValidTypeCond.execute, it is referred be itself')
                    logger.debug(f'{self.types}, {new_val.svalue.ty_value}')
                    constraint, is_unconstrained = get_ty_combination_constraint(self.types, new_val.svalue.ty_value)
                    if not is_unconstrained:
                        all_unconstrained = False
                    constraints.append(constraint)
                else:
                    raise Exception('Unexpected situation')
            else:
                c = get_constraint(new_val, val)
                if c == claripy.true:
                    all_unconstrained = False
                constraints.append(c)
            store.stack.append(new_val)
        if all_unconstrained and (not whether_meet):
            store.stack.pop()
        store.stack_max = len(store.stack)
        store.explored_top = len(store.stack)

        logger.debug(f'In inferedValidTypeCond.execute, constraints: {constraints}')
        if len(constraints) == 0:
            constraints = claripy.true
        else:
            constraints = claripy.And(*constraints)
        if not whether_meet:
            constraints = claripy.Not(constraints)
        assert constraints is not claripy.false
        return constraints


class seqValidTypeCond(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        self.insts_ref = elems[1]
        self.seq_input_ty = elems[2]
        self.seq_output_ty = elems[3]

    def execute(self, store, whether_meet, *args, **kwargs):
        raise NotImplementedError

typeConds = (directValidTypeCond, fromStoreValidTypeCond, inferedValidTypeCond, seqValidTypeCond)

def get_seq_ty_cond(line, part1, part2):
    seq_ty_p = re.compile(r'^:math:`\[(.*?)\] \\to \[(.*?)\]`$')
    r = seq_ty_p.findall(part2)[0]
    seq_in_ty_str = r[0]
    seq_out_ty_str = r[1]
    inst_ref_str = unwrap_math(part1)
    elems = ['seq_valid_type', inst_ref_str, seq_in_ty_str, seq_out_ty_str]
    return seqValidTypeCond(line, elems)

def get_must_ty_cond(line):
    elems = match_must_ty_direct_cond(line)
    if elems:
        return directValidTypeCond(line, elems)
    elems = match_must_ty_from_store_cond(line)
    if elems:
        return fromStoreValidTypeCond(line, elems)

def get_infered_must_ty_cond(line):
    elems = match_must_ty_infered_cond(line)
    return inferedValidTypeCond(line, elems)


# ===================
# must exist


def get_must_define_cond(line):
    line = re.compile(r'(:math:`[^`]*?`)').findall(line)[0]
    return ExistCondition(line, ['valid_define_condition', generate_Value_from_common_line(line)])


# ===================
# must be
class validCompareCond(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        self.v1 = elems[1]
        self.v2 = elems[2]
        self.hold_or_not = elems[3]
        assert isinstance(self.hold_or_not, bool)
        self.relation = elems[4]

    def execute(self, store, whether_meet, *args, **kwargs):
        whether_meet = (whether_meet == self.hold_or_not)
        self.v1.update_name(store.propagate_info)
        self.v2.update_name(store.propagate_info)
        right_val = self.v2
        if isinstance(right_val, FormulaValue):
            right_str = process_condition_text(right_val.name)
        else:
            raise NotImplementedError
        logger.debug(f'In validCompareCond.execute, right_str: {right_str}')
        left_str = process_condition_text(self.v1.name)
        sg = relation_str2sg(self.relation)
        logger.debug(f'In validCompareCond.execute, self.v1.name: {self.v1.name}')
        logger.debug(f'In validCompareCond.execute, left_str: {left_str}')
        cond_str = f'{left_str} {sg} {right_str}'
        logger.debug(f'In validCompareCond.execute, cond_str: {cond_str}')
        cond = replace_val(store.value_relation, cond_str, False)
        if not whether_meet:
            cond = claripy.Not(cond)
        return cond

def get_CompareCondition_from_must_be(line, v1, hold_or_not, relation, v2):
    hold_or_not = ('not' not in hold_or_not)
    assert isinstance(v1, str)
    assert isinstance(v2, str)
    p = r'^.*(:math:`[^`]+`)$'
    v1 = re.compile(p).findall(v1)[0]
    v1 = generate_Value_from_common_line(v1)
    v2 = generate_Value_from_common_line(v2)
    elems = ['compare_condition', v1, v2, hold_or_not, relation]
    return validCompareCond(line, elems)

class validIsCondition(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        self.val1 = elems[1]
        self.val2 = elems[2]

    def execute(self, store, whether_meet, *args, **kwargs):
        raise NotImplementedError

def get_valid_must_be_cond(line, elem_strs):
    elems = [
        'valid_must_be_condition',
        generate_Value_from_common_line(elem_strs[0]),
        generate_Value_from_common_line(elem_strs[1])
    ]
    return validIsCondition(line, elems)


class validExistCond(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        self.ref_val = elems[1]
        self.instance = elems[2]

    def execute(self, store, whether_meet, *args, **kwargs):
        if whether_meet:
            return claripy.true
        else:
            return claripy.false


def get_valid_exist_cond(line, elem_strs):
    elems = [
        'valid_exist_condition',
        generate_Value_from_common_line(elem_strs[0]),
        generate_Value_from_common_line(elem_strs[1])
    ]
    return validExistCond(line, elems)

class blocktypeTypeCond(Condition):
    def __init__(self, line, elems=None):
        super().__init__(line, elems)
        self.block_type = elems[1]
        self.input_ty_ref = elems[2]
        self.output_ty_ref = elems[3]

    def execute(self, store, whether_meet, *args, **kwargs):
        raise NotImplementedError

def get_blocktype_type_cond(line, elem_strs):
    elems = [
        'blocktype_type_condition',
        ValRefValue(elem_strs[0], valueType.generate_any_ty()),
        ValRefValue(elem_strs[1], valueType.generate_any_ty()),
        ValRefValue(elem_strs[2], valueType.generate_any_ty())
    ]
    return blocktypeTypeCond(line, elems)
