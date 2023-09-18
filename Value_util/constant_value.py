import re
from .Value import Value
from Value_util import valueType
from process_text import process_char_bracket_fmt
from symbol_util import ref_null_constant
from .SValue import SValue


class Constant_(Value):
    def __init__(self, name, ty, raw_value=None, *args, num=1, **kwads):
        super().__init__(name, ty, raw_value, *args, num=num, **kwads)
        self.constant_value = None

    @property
    def need_solve(self):
        return self.constant_value is None

    def __repr__(self):
        s = f'{self.__class__.__name__}({self.name}:{self.type}:{self.constant_value}:{self.need_solve}:{self.raw_content})'
        return s


class constantValue(Constant_):
    def __init__(self, name, ty, raw_value=None, *args, num=1, **kwads):
        super().__init__(name, ty, raw_value, *args, num=num, **kwads)
        self.infer_value()

    def generate_svalue(self, *args):
        svalue = SValue()
        assert not self.need_solve, print(self, self.constant_value)
        if self.type.is_ref_null:
            svalue.ty_value = 6
            svalue.v_value = ref_null_constant
        else:
            svalue.v_value = self.constant_value
        self.svalue = svalue

    def update_name(self, dict_):
        super().update_name(dict_)
        self.infer_value()
        print('in constantValue update_name:', self.name)

    def infer_value(self):
        # null
        if self.type.is_ref_null:
            self.constant_value = 'ref_null'
        # p1
        if self.name.isdigit():
            assert self.type._type in ('u32', 'i32', 'any'), print(self, self.name, self.raw_content)
            self.constant_value = int(self.name)
        # p2
        if self.need_solve:
            if self.type.detail_info == 'bit width':
                calculated_ty = re.compile(r'\|(.*?)\|').findall(self.name)
                if not calculated_ty:
                    calculated_ty = re.compile(r'^(.*?)$').findall(self.name)
                assert calculated_ty, print(f'<{self.name}>')
                calculated_ty = calculated_ty[0]
                if calculated_ty in ['i32', 'f32', 'i64', 'f64', 'v128', 'i8', 'i16']:
                    self.constant_value = determine_bw(calculated_ty)
                else:
                    pass
        if self.need_solve:
            p = r'^dim\(.+x(.+)\)$'
            _processed_name = process_char_bracket_fmt(self.name)
            r = re.compile(p).findall(_processed_name)
            if r:
                self.constant_value = eval(r[0])

    @classmethod
    def from_constant_str(cls, s):
        obj = cls(s, valueType('u32'), s)
        return obj

def determine_bw(ty_str):
    if ty_str == 'i8' or ty_str == 'i16':
        ty_str = 'i32'
    bw = [32, 64, 128]
    for i in bw:
        if str(i) in ty_str:
            return i
    raise Exception('unknown bit width: {}'.format(ty_str))


class constType(Constant_):
    def __init__(self, name, ty, raw_value=None, *args, num=1, **kwads):
        super().__init__(name, ty, raw_value, *args, num=num, **kwads)
        self.infer_value()
    def infer_value(self):
        if self.type.detail_info == 'type':
            name = self.name
            if name == 'any':
                name = self.type.type_sig
                self.name = name
            p = r'^unpacked\((.+)x.+\)$'
            _processed_name = process_char_bracket_fmt(name)
            r = re.compile(p).findall(_processed_name)
            if r:
                ty_str = r[0]
                if ty_str == 'i8' or ty_str == 'i16':
                    ty_str = 'i32'
                infered_type = ty_str
                self.constant_value = infered_type
