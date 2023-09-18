from .renew_util import renew_raw_content_without_math
from .valueType import valueType
from .match_Value_util import get_name_type_from_p
from .SValue import SValue


class Value:
    def __init__(self, name, ty, raw_value=None, *args, num=1, **kwads):
        # has considered push
        assert isinstance(ty, valueType), print(name, ty, raw_value)
        self.name = name
        self.type = ty
        if raw_value is None:
            raw_value = name
        self.raw_content = raw_value
        self.num = num
        self.svalue = None
        self.svalue_constraints = []

        self.generate_trap = False
        self.simd_lane_num = None

    def update_type_by_title_paras(self, title_info):
        self.type.renew_type_with_type_sig_info(title_info)

    def update_name(self, dict_):
        self.name = renew_raw_content_without_math(self.name, dict_)

    def generate_svalue(self):
        self.svalue = SValue(v_value='any')

    @property
    def has_svalue(self):
        return (self.svalue is not None)

    @property
    def has_symbol_ty(self):
        return (not isinstance(self.svalue.ty_value, int))

    def __eq__(self, __o: object):
        if self.name == __o.name:
            if self.type == __o.type:
                return True
        return False

    def __hash__(self):
        return hash((self.name, self.type))

    def __repr__(self):
        s = f'{self.__class__.__name__}({self.type}, {self.name}, {self.num})'
        return s

    @classmethod
    def generate_value_with_type(cls, ty: valueType):
        return cls('any', ty, 'any', 1)

    @classmethod
    def generate_value_with_any_type(cls):
        ty = valueType.generate_any_ty()
        return cls('any', ty, 'any', 1)

    @classmethod
    def from_common_line(cls, raw_value):
        name, ty, num, idx = get_name_type_from_p(raw_value)
        return cls(name, ty, raw_value, num=num)


