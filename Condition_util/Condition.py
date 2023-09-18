from .match_Condition_util import match_is_condition
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


class Condition():
    def __init__(self, line, elems=None):
        self.raw_content = line
        if elems is None:
            self.elems = []
        else:
            self.elems = elems

    def __repr__(self):
        return f'{self.__class__.__name__}({self.elems})'

    @classmethod
    def from_assert_line(cls, line):
        line = line.rstrip('.:')
        elems = match_on_the_stack_top_condition(line)
        if not elems:
            elems = match_exists_condition(line)
        if not elems:
            elems = match_formula_condition(line)
        if not elems:
            elems = match_is_defined_condition(line)
        if not elems:
            elems = match_is_ref_condition(line)
        if not elems:
            elems = match_ref_on_the_stack_top_condition(line)
        if not elems:
            elems = match_thereb_on_the_stack_top_condition(line)
        if not elems:
            elems = match_stack_contain_condition(line)
        if not elems:
            elems = match_the_top_of_stack_be_condition(line)

        return cls(line, elems)

    @classmethod
    def from_if_line(cls, line):
        line = line.rstrip('.:')
        elems = match_is_condition(line)
        if not elems:
            elems = match_is_defined_condition(line)
        if not elems:
            elems = match_formula_condition(line)
        if not elems:
            elems = match_non_zero_condition(line)
        if not elems:
            elems = match_is_part_condition(line)
        if not elems:
            elems = match_differ_condition(line)
        if not elems:
            elems = match_compare_condition(line)
        return cls(line, elems)

    @classmethod
    def from_while_line(cls, line):
        line = line.rstrip('.:')
        elems = match_the_top_of_stack_be_condition(line)
        return cls(line, elems)
