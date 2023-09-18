import re
from Condition_util import Condition
from Step_util import Step
from Step_util import Steps
from Value_util import Value
from file_util import save_json
from process_text import raw_processor
from process_text import unwrap_math
from Value_util import POP_TYPE, PUSH_TYPE
from Value_util import valueType


class execInst():
    def __init__(self, raw_title, math_part, steps_part, category=''):
        self.raw_title = raw_title
        # possible another title
        p = r'^(:math:`.*?`) and (:math:`.*?`)$'
        r = re.compile(p).findall(raw_title)
        if r:
            r = r[0]
            self.raw_name = r[0]
            self.raw_another_name = r[1]
        else: 
            self.raw_name = raw_title
            self.raw_another_name = ''
        self.name = raw_processor.process_raw_title(self.raw_name)
        self.exec_imms = _extract_imm_from_exec_name_from_title(self.raw_name)
        self.another_name = raw_processor.process_raw_title(self.raw_another_name)
        self.math_part = math_part
        self.steps_part = steps_part
        self.steps = self.get_steps_from_content()
        self.ctgy = category
        self.infer_type()
        self.unique_values = set(self.all_values)
        self.organization = self.organize_steps()

    @property
    def all_values(self):
        values = []
        for step in self.steps:
            assert isinstance(step, Step)
            step_elems = step.elems
            cur_values = _flat_values(step_elems)
            values.extend(cur_values)
        return values

    @classmethod
    def from_raw_rst(cls, category, raw_title, raw_content):
        content = raw_processor.process_raw_content(raw_content)
        return cls(raw_title, content['math'], content['steps'], category=category)

    def get_steps_from_content(self):
        steps_text = self.steps_part
        steps = Steps.from_exec_paragraph(steps_text)
        return steps

    def as_data(self):
        data = {}
        data['ctgy'] = self.ctgy
        data['raw_title'] = self.raw_title
        data['name'] = self.name
        data['steps_part'] = self.steps_part
        # data['math_part'] = self.math_part
        data['steps'] = self.steps.as_data()
        data['vstack_vt_num_seq'] = repr(self.vstack_vt_num_seq)
        return data

    def organize_steps(self):
        organization = self.steps.organize_steps()
        return organization

    def __repr__(self):
        raw_title = 'raw_title: {}'.format(self.raw_title)
        title = 'name: {}'.format(self.name)
        steps = 'steps:\n{}'.format(self.steps)
        return '\n'.join((raw_title, title, steps))

    def infer_type(self):
        organization = self.organize_steps()
        index_to_drop = []
        in_repeat_scope=False
        for i, s in enumerate(self.steps):
            assert isinstance(s, Step)
            if s.type == 'ELSE':
                index_to_drop.append(i)
                index_to_drop.extend(organization[i])
            if s.type == 'RETURN':
                index_to_drop.extend(range(i, len(self.steps)))
            if s.type in ['REPEAT', 'EITHER', 'WHILE']:
                in_repeat_scope = True
                repeat_hier = s.hier
                index_to_drop.append(i)
                continue
            if in_repeat_scope:
                if s.hier > repeat_hier:
                    index_to_drop.append(i)
                else:
                    in_repeat_scope = False
        check_key_to_drop = [x for x in index_to_drop]
        while check_key_to_drop:
            i = check_key_to_drop.pop()
            possible_new_drop = organization.get(i)
            if possible_new_drop:
                for ni in possible_new_drop:
                    check_key_to_drop.append(ni)
                    index_to_drop.append(ni)
        step_index_for_analyze = [i for i in range(len(self.steps)) if i not in index_to_drop]
        steps_to_analyze = [self.steps[i] for i in step_index_for_analyze]
        steps_to_analyze = [s for s in steps_to_analyze if s.type in ['PUSH', 'POP']]

        self.vstack_vt_num_seq = []
        for s in steps_to_analyze:
            assert isinstance(s, Step)
            assert s.type in ['PUSH', 'POP']
            val = s.elems[0]
            ty = val.type
            if ty in [valueType('other', 'label'), valueType('other', 'frame')]:
                continue
            if s.type == 'PUSH':
                self.vstack_vt_num_seq.append([(ty, val.num), PUSH_TYPE])
            else:
                self.vstack_vt_num_seq.append([(ty, val.num), POP_TYPE])


def _flat_values(x):
    result = []
    if isinstance(x, (list,tuple)):
        for x_idx in range(len(x)):
            result.extend(_flat_values(x[x_idx]))
    elif isinstance(x, Value):
        result.append(x)
    elif isinstance(x, Condition):
        for x_idx in range(len(x.elems)):
            result.extend(_flat_values(x.elems[x_idx]))

    return result


def _extract_imm_from_exec_name_from_title(s):
    if s.count('~') == 0:
        return []
    else:
        s = unwrap_math(s)
        parts = s.split('~')[1:]
        if '\\memarg' in parts:
            memarg_idx = parts.index('\\memarg')
            parts = parts[:memarg_idx] + [raw_processor._process_macro('\\memarg.\\ALIGN'), raw_processor._process_macro('\\memarg.\\OFFSET')] + parts[memarg_idx+1:]
        return parts
