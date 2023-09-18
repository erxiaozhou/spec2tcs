from .Condition import Condition
from .Conditions import StackCondition
from .Conditions import StackContainCondition
from .Conditions import IsCondition
from .Conditions import IsDefinedCondition
from .Conditions import FormulaCondition
from .Conditions import ExistCondition
from .Conditions import NonZeroCondition
from .Conditions import InstructionPartCondition
from .Conditions import DifferCondition
from .Conditions import StackTopSameTypeCondition
from .Conditions import CompareCondition
from .Conditions import SIMDValCondition
from .Conditions import MachineDeterminedCondition
from .Conditions import immPresentCondition
from .match_Condition_util import match_is_condition
from .match_Condition_util import match_two_same_type_stack_top_condition
from .match_Condition_util import match_is_ref_condition
from .match_Condition_util import match_is_defined_condition
from .match_Condition_util import match_formula_condition
from .match_Condition_util import match_non_zero_condition
from .match_Condition_util import match_is_part_condition
from .match_Condition_util import match_differ_condition
from .match_Condition_util import match_compare_condition
from .match_Condition_util import match_the_top_of_stack_be_condition
from .match_Condition_util import match_on_the_stack_top_condition
from .match_Condition_util import match_thereb_on_the_stack_top_condition
from .match_Condition_util import match_stack_contain_condition
from .match_Condition_util import match_ref_on_the_stack_top_condition
from .match_Condition_util import match_exists_condition
from .match_Condition_util import match_simd_val_condition
from .match_Condition_util import match_machine_determined_condition
from .match_Condition_util import match_is_present_condition


class ConditionFactory:
    kwd2cond = {
        'stack_top': StackCondition,
        'ref_stack_top': StackCondition,
        'thereb_stack_top': StackCondition,
        'stack_top_be': StackCondition,
        'stack_contain': StackContainCondition,
        'is_condition': IsCondition,
        'is_defined_condition': IsDefinedCondition,
        'formula_condition': FormulaCondition,
        'exist': ExistCondition,
        'non_zero_condition': NonZeroCondition,
        'instruction_part_condition': InstructionPartCondition,
        'present_condition': immPresentCondition,
        'differ_condition': DifferCondition,
        'two_same_type_on_stack': StackTopSameTypeCondition,
        'compare_condition': CompareCondition,
        'simd_val': SIMDValCondition,
        'machine_determined': MachineDeterminedCondition
    }

    @staticmethod
    def from_assert_line(line):
        funcs = [
            match_on_the_stack_top_condition,
            match_exists_condition,
            match_formula_condition,
            match_is_defined_condition,
            match_is_ref_condition,
            match_ref_on_the_stack_top_condition,
            match_thereb_on_the_stack_top_condition,
            match_stack_contain_condition,
            match_the_top_of_stack_be_condition,
            match_two_same_type_stack_top_condition,
            match_simd_val_condition
        ]
        cond = extract_cond_from_line(line, funcs)
        return cond

    @staticmethod
    def from_if_line(line):
        funcs = [
            match_is_condition,
            match_is_defined_condition,
            match_formula_condition,
            match_non_zero_condition,
            match_is_part_condition,
            match_differ_condition,
            match_compare_condition,
            match_machine_determined_condition,
            match_is_present_condition
        ]
        cond = extract_cond_from_line(line, funcs)
        return cond

    @staticmethod
    def from_while_line(line):
        funcs = [
            match_the_top_of_stack_be_condition
        ]
        cond = extract_cond_from_line(line, funcs)
        return cond


def extract_cond_from_line(line, extraction_funcs):
    elems = extract_elems_from_cond_line(line, extraction_funcs)
    cond = generate_Condition_from_elems(line, elems)
    return cond


def extract_elems_from_cond_line(line, extraction_funcs):
    line = line.rstrip('.:')
    elems = None
    for func in extraction_funcs:
        elems = func(line)
        if elems:
            return elems
    raise Exception(f'Have not match Condition: <{line}>')


def generate_Condition_from_elems(line, elems):
    kwd = elems[0]
    assert kwd in ConditionFactory.kwd2cond
    condition_class = ConditionFactory.kwd2cond[kwd]
    cond = condition_class(line, elems)
    return cond

