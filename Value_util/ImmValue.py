import claripy
from .Value import Value
from symbol_util import get_traditional_type
from .SValue import SValue
from Value_util import valueType

class blocktype_ph_tmp:
    def __init__(self):
        self.t1 = valueType('i32')
        self.t2 = valueType('i32')
        self.in_num = 1
        self.out_num = 1

class ImmValue(Value):
    def __init__(self, name, ty, imm_type, *args, num=1):
        super().__init__(name, ty, *args, num=num)
        self.imm_type = imm_type

    def generate_svalue(self):
        traditional_tys = ['i32', 'i64', 'f32', 'f64', 'i128', 'v128', 'ref']
        svalue = SValue()

        assert not self.type.need_infer
        type_str = self.type._type
        assert type_str != 'i128'
        if type_str in traditional_tys:
            v_value, self_constraints, ty_value = get_traditional_type(self.type, self.name)
            svalue.v_value = v_value
            svalue.self_constraints = self_constraints
            svalue.ty_value = ty_value
        elif type_str == 'u32':
            svalue.v_value = claripy.BVS(self.name, 64)
            svalue.self_constraints = [svalue.v_value < 2 **32]
        elif type_str == 'u8' :
            svalue.v_value = claripy.BVS(self.name, 8)
        elif type_str == 'blocktype':
            svalue.v_value = blocktype_ph_tmp()
        elif type_str == 'instr':
            pass
        else:
            raise Exception('unknown type_str: <{}>'.format(type_str))
        self.svalue = svalue


    @property
    def has_symbol_ty(self):
        return False