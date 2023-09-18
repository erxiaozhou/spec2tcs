import re
from Value_util import Value
from process_text import unwrap_math


class BlockValue(Value):
    def __init__(self, ty, name, label, raw_value, *args, num=1):
        self.type = ty
        self.name = name
        self.label = label
        self.raw_content = raw_value
        self.num = num

    @classmethod
    def from_enter_line(cls, raw_value):
        p = re.compile(r'.*?the block (.*?) with label (.*?)\.?$')
        r = p.findall(raw_value)[0]

        assert len(r) == 2
        name = unwrap_math(r[0])
        label = unwrap_math(r[1])
        return cls(ty='block', name=name, label=label, raw_value=raw_value)


class Location_descibor:
    def __init__(self, line):
        self.raw_content = line

    def __repr__(self):
        return self.raw_content


class Try_content():
    def __init__(self, line):
        self.raw_content = line

    def __repr__(self):
        return self.raw_content

class Label(Value):
    def __init__(self, name, ty, raw_value, *args, num=1, idx=None):
        self.name = name
        self.type = ty
        self.raw_content = raw_value
        self.num = num
        self.idx = idx

    def generate_svalue(cls, *args, **kwads):
        assert 0

    def __repr__(self):
        idx = f'idx={self.idx}' if self.idx is not None else ''
        s = f'{self.__class__.__name__}({self.type}, {self.name}, {self.num}, {idx})'
        return s


class Arity(Value):
    def __init__(self, name, ty, raw_value, *args, num=1):
        self.name = name
        self.type = ty
        self.raw_content = raw_value
        self.num = num
        self.label_ref = self._get_label_ref_name()

    def _get_label_ref_name(self):
        p = re.compile(r'^the arity of :math:`(.*?)`$')
        r = p.findall(self.raw_content)
        assert r, print(self.raw_content)
        label_ref = r[0]
        return label_ref

    def generate_svalue(cls, *args, **kwads):
        assert 0

    def get_arity(self, store):
        return store.outest_output.num
