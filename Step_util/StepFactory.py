import logging
import claripy
from Condition_util import Condition
from .Step import Step
from Value_util import Value
from Value_util import DataAddrInstance, DataInstance, ElemAddrInstance, ElemInstance, FormulaValue, FrameInstance, FuncAddrInstance, GlobalAddrInstance, GlobalInstance, LengthRefValue, MemAddrInstance, MemInstance, OtherValue, StackValue, TableAddrInstance, TableInstance, ValRefValue, constType, constantValue, LocalAddrInstance, Label, ModuleInstance, Arity, globalItem
import re
from env_store import env_store
from env_store_util import get_value_name_in_store_dict
from env_store_util import get_val_from_dict_by_name
std_logger = logging.getLogger('std_log')

class PushStep(Step):
    def __init__(self, hier, elems, type_, raw_line=None):
        super().__init__(hier, elems, type_, raw_line)
        assert len(elems) == 1
        self.val = elems[0]
        assert isinstance(self.val, Value)

    def execute(self, store: env_store, *args, **kwads):
        pass


class PopStep(Step):
    def __init__(self, hier, elems, type_, raw_line=None):
        super().__init__(hier, elems, type_, raw_line)
        assert len(elems) == 1
        self.val = elems[0]
        assert isinstance(self.val, Value)

    def execute(self, store: env_store, *args, **kwads):
        val = self.val
        assert isinstance(val, ValRefValue), print(repr(val), type(val))
        top_stack_val = store.stack[store.stack_top]
        assert isinstance(top_stack_val, StackValue)
        store.stack_top += 1
        if top_stack_val.name == 'any':
            top_stack_val.name = val.name
        if top_stack_val.type.is_unconstrained_ty():
            pass

        if not top_stack_val.has_svalue:
            assert 0, print(store.stack, [o.svalue for o in store.stack])
            top_stack_val.generate_svalue()

        val_name = val.name
        store_name = get_value_name_in_store_dict(val_name, store.value_relation)
        store.value_relation[store_name] = top_stack_val


class ExecuteStep(Step):
    def __init__(self, hier, elems, type_, raw_line=None):
        super().__init__(hier, elems, type_, raw_line) 


class ElseStep(Step):
    def __init__(self, hier, elems, type_, raw_line=None):
        super().__init__(hier, elems, type_, raw_line)


class InvokeStep(Step):
    def __init__(self, hier, elems, type_, raw_line=None):
        super().__init__(hier, elems, type_, raw_line)


class WhileStep(Step):
    def __init__(self, hier, elems, type_, raw_line=None):
        super().__init__(hier, elems, type_, raw_line)

    def execute(self, store: env_store, **kwads):
        assert 0


class JumpStep(Step):
    def __init__(self, hier, elems, type_, raw_line=None):
        super().__init__(hier, elems, type_, raw_line)


class EnterStep(Step):
    def __init__(self, hier, elems, type_, raw_line=None):
        super().__init__(hier, elems, type_, raw_line)


class AssertStep(Step):
    def __init__(self, hier, elems, type_, raw_line=None):
        super().__init__(hier, elems, type_, raw_line)
        assert len(self.elems) == 1
        self.condition = self.elems[0]
        assert isinstance(self.condition, Condition)

    def execute(self, store: env_store, whether_meet, *args, **kwads):
        assert len(self.elems) == 1
        if isinstance(self.condition, Condition):
            constraint = self.condition.execute(store, whether_meet, **kwads)
        elif isinstance(self.condition, list):
            constraints = []
            for cond in self.condition:
                constraints.append(cond.execute(store, whether_meet, **kwads))
            constraint = claripy.And(*constraints)
        else:
            raise Exception('Unknown condition type: {}'.format(type(self.condition)))
        if isinstance(constraint, list):
            constraint = claripy.And(*constraint)
        return constraint


class IfStep(Step):
    def __init__(self, hier, elems, type_, raw_line=None):
        super().__init__(hier, elems, type_, raw_line)
        assert len(self.elems) == 1
        self.condition = self.elems[0]
        assert isinstance(self.condition, (Condition, list))

    def execute(self, store: env_store, whether_meet, *args, **kwads):
        if isinstance(self.condition, Condition):
            constraint = self.condition.execute(store, whether_meet, **kwads)
        elif isinstance(self.condition, list):
            constraints = []
            for cond in self.condition:
                constraints.append(cond.execute(store, whether_meet, **kwads))
            constraint = claripy.And(*constraints)
        if isinstance(constraint, list):
            constraint = claripy.And(*constraint)
        return constraint


class ReplaceStep(Step):
    def __init__(self, hier, elems, type_, raw_line=None):
        super().__init__(hier, elems, type_, raw_line)


class RepeatStep(Step):
    def __init__(self, hier, elems, type_, raw_line=None):
        super().__init__(hier, elems, type_, raw_line)


class LetStep(Step):
    def __init__(self, hier, elems, type_, raw_line=None):
        super().__init__(hier, elems, type_, raw_line)
        assert len(elems[0]) == 2, print(elems)
        self.val_1 = elems[0][0]
        self.val_2 = elems[0][1]

    def execute(self, store: env_store, **kwads):
        val_1 = self.val_1
        val_1.update_type_by_title_paras(store.propagate_info)
        assert isinstance(val_1, ValRefValue)
        name_for_val1 = get_value_name_in_store_dict(
            val_1.name, store.value_relation)

        if isinstance(self.val_2, constantValue):
            self.val_2.update_name(store.propagate_info)
            assert not self.val_2.need_solve, print(self.val_2, store.propagate_info)
            assert not self.val_2.has_svalue
            self.val_2.generate_svalue()
            store.value_relation[name_for_val1] = self.val_2
            store.propagate_info[val_1.name] = self.val_2.constant_value
        elif isinstance(self.val_2, constType):
            self.val_2.update_name(store.propagate_info)
            if self.val_2.need_solve:
                self.val_2.infer_value()
            assert not self.val_2.need_solve, print(self.val_2, self.val_2.name, store.propagate_info)
            store.propagate_info[val_1.name] = self.val_2.constant_value
        elif isinstance(self.val_2, ValRefValue):
            assert 0
            val = get_val_from_dict_by_name(
                self.val_2.name, store.value_relation)
            store.value_relation[name_for_val1] = val
        elif isinstance(self.val_2, (OtherValue, globalItem)):
            assert 0
            ref_name = self.val_2.index_name
            val = get_val_from_dict_by_name(ref_name, store.value_relation)
            store.value_relation[name_for_val1] = val
        elif isinstance(self.val_2, (GlobalInstance, TableInstance, MemInstance, DataInstance, ElemInstance)):
            new_val = get_val_from_dict_by_name(self.val_2.index_name, store.value_relation)
            store.value_relation[name_for_val1] = new_val
        elif isinstance(self.val_2, (TableAddrInstance, GlobalAddrInstance, MemAddrInstance, FuncAddrInstance, LocalAddrInstance, DataAddrInstance, ElemAddrInstance)):
            val = self.val_2.get_instance_by_idx(store)
            store.value_relation[name_for_val1] = val
        elif isinstance(self.val_2, FrameInstance):
            pass
        elif isinstance(self.val_2, Label):
            store.value_relation[name_for_val1] = self.val_2
            print(f'LetStep.Label <{self.val_2}>')
        elif isinstance(self.val_2, Arity):
            store.value_relation[name_for_val1] = self.val_2.get_arity(store)
        elif self.val_2.type.detail_info == 'function type':
            val_1_raw_name = val_1.name
            parse_block_p = re.compile(r'^\[.*\^(.*?)\] .*? \[.*\^(.*?)\]$')
            r = parse_block_p.findall(val_1_raw_name)
            assert r, print(f'r:<{r}>, val_1_raw_name:<{val_1_raw_name}>')
            in_num_name, out_num_name = r[0]
            in_num_name_to_store = get_value_name_in_store_dict(in_num_name, store.value_relation)
            out_num_name_to_store = get_value_name_in_store_dict(out_num_name, store.value_relation)
            print(f'self.val_2.name: {self.val_2.name}', self.val_2)
            parsed_val_2_name = re.compile(r'.*expand_F\((.*?)\)').findall(self.val_2.name)[0]
            print(f'parsed_val_2_name: {parsed_val_2_name}')
            val_2_value = get_val_from_dict_by_name(parsed_val_2_name, store.value_relation)
            store.value_relation[in_num_name_to_store] = val_2_value.svalue.v_value.in_num
            store.value_relation[out_num_name_to_store] = val_2_value.svalue.v_value.out_num

        elif isinstance(self.val_2, FormulaValue):
            self.val_2.update_name(store.propagate_info)
            assert not self.val_2.has_svalue
            self.val_2.generate_svalue(store.value_relation)
            store.value_relation[name_for_val1] = self.val_2
        else:
            std_logger.debug(f'self.val_2: <{self.val_2}> ==at end**** un matched')


class EitherStep(Step): pass
class TrapStep(Step): pass
class ReturnStep(Step): pass
class DoNothingStep(Step): pass


class forEachStep(Step): pass 

class suchThatStep(Step): pass

class StepFactory:
    keyword2step = {
        'PUSH': PushStep,
        'POP': PopStep,
        'EXECUTE': ExecuteStep,
        'ELSE': ElseStep,
        'INVOKE': InvokeStep,
        'WHILE': WhileStep,
        'JUMP': JumpStep,
        'ENTER': EnterStep,
        'ASSERT': AssertStep,
        'REPLACE': ReplaceStep,
        'REPEAT': RepeatStep,
        'IF': IfStep,
        'LET': LetStep,
        'EITHER': EitherStep,
        'TRAP': TrapStep,
        'RETURN': ReturnStep,
        'DO_NOTHING': DoNothingStep,
        # valid only
        'MUST_TY': AssertStep,
        'MUST_BE': AssertStep,
        'MUST_EXIST': AssertStep,
        'SUCH_THAT': suchThatStep,
        'FOR_EACH': forEachStep
    }

    def __init__(self) -> None:
        pass

    @staticmethod
    def from_step_parameters(para_dict):
        assert 'hier' in para_dict
        assert 'line_type' in para_dict, print(para_dict)
        assert 'elems' in para_dict
        assert 'raw_line' in para_dict
        hier = para_dict['hier']
        type_ = para_dict['line_type'].upper()
        elems = para_dict['elems']
        raw_line = para_dict['raw_line']
        step = StepFactory.keyword2step[type_](hier, elems, type_, raw_line)
        return step


def emit_lines_from_paras(paras):
    result = []
    for para in paras:
        step = StepFactory.from_step_parameters(para)
        result.append(step)
        result.extend(emit_lines_from_paras(para['embedded_line']))
    return result
