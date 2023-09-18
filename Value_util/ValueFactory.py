import re

from data_model import memoryInstanceModel
from .Value import Value
from .match_Value_util import get_name_type_from_p
from Value_util import valueType
from env_store_util import can_replace_val, check_val_exist, get_val_from_dict_by_name, replace_val
from process_text import process_char_bracket_fmt, process_str, raw_processor
from symbol_util import get_traditional_type
from .SValue import SValue
from .unique_value_for_control_inst import Label, Arity
from .constant_value import constantValue, constType


class ValRefValue(Value):
    def generate_svalue(self, val_relation=None):
        val = get_val_from_dict_by_name(self.name, val_relation)
        assert isinstance(val, Value), print(val, type(val))
        assert val.has_svalue, print('self', self, 'val_relation=\n{}\n='.format(val_relation), '\n{}\n'.format(val), val.has_svalue)
        self.svalue = val.svalue

    def generate_svalue(self, val_relation=None):
        svalue = SValue()
        if val_relation is not None and can_replace_val(val_relation, self.name):
            svalue.v_value = replace_val(val_relation, self.name)
        self.svalue = svalue


class FormulaValue(Value):
    def generate_svalue(self, val_relation=None):
        svalue = SValue()
        if val_relation is not None and can_replace_val(val_relation, self.name):
            svalue.v_value = replace_val(val_relation, self.name)
        self.svalue = svalue


class ModuleInstance(Value):
    def __init__(self, name, ty, raw_value=None, *args, num=1, **kwads):
        super().__init__(name, ty, raw_value, *args, num=num, **kwads)
        self.index = None
        self.index_name = None

    def init_index(self, index):
        assert isinstance(index, str)
        if index.isdigit():
            val = constantValue.from_constant_str(index)
            self.index = val
            self.index_name = val.constant_value
        else:
            val = ValRefValue(index, valueType('u32'), index)
            self.index = val
            self.index_name = val.name


    def get_instance_by_idx(self, store):
        raise NotImplementedError

    def __repr__(self):
        s = f'{self.__class__.__name__}({self.name}:{self.type}:{self.index}:{self.raw_content})'
        return s


class FrameInstance(Value): pass


class LengthRefValue(Value):
    def __init__(self, name, ty, raw_value=None, *args, num=1, StoreName=None, StoreAttr=None, **kwads):
        super().__init__(name, ty, raw_value, *args, num=num, **kwads)
        self.StoreName = StoreName
        self.StoreAttr = StoreAttr

    def __repr__(self):
        s = f'{self.__class__.__name__}({self.name}:{self.type}:{self.StoreName}:{self.StoreAttr}:{self.raw_content})'
        return s

    def generate_svalue(self, val_relation=None):
        instance_name = self.StoreName
        assert check_val_exist(instance_name, val_relation)
        instance = get_val_from_dict_by_name(instance_name, val_relation)
        if isinstance(instance, memoryInstanceModel):
            v_value = instance.len * 64 * 1024
        else:
            v_value = instance.len
        self.svalue = SValue()
        self.svalue.v_value = v_value


class TypeRefValue(Value):
    def __init__(self, name, ty, raw_value=None, *args, num=1, type_base=None, **kwads):
        super().__init__(name, ty, raw_value, *args, num=num, **kwads)
        self.type_base = type_base

    def __repr__(self):
        s = f'{self.__class__.__name__}({self.name}:{self.type}:{self.type_base}:||{self.raw_content})'
        return s

class LabelAddrInstance(ModuleInstance):
    def get_instance_by_idx(self, store):
        raise NotImplementedError

class TypeInstance(ModuleInstance):
    def get_instance_by_idx(self, store):
        raise NotImplementedError

class GlobalAddrInstance(ModuleInstance):
    def get_instance_by_idx(self, store):
        return store.global_obj[self.index_name]


class GlobalInstance(ModuleInstance):
    pass

class LocalAddrInstance(ModuleInstance):
    def get_instance_by_idx(self, store):
        return store.local_obj[self.index_name]


class DataAddrInstance(ModuleInstance):
    def get_instance_by_idx(self, store):
        return store.data_obj[self.index_name]


class ElemAddrInstance(ModuleInstance):
    def get_instance_by_idx(self, store):
        return store.elem_obj[self.index_name]


class FuncAddrInstance(ModuleInstance):
    def get_instance_by_idx(self, store):
        return store.func_obj[self.index_name]


class MemAddrInstance(ModuleInstance):
    def get_instance_by_idx(self, store):
        return store.memory_obj[self.index_name]


class TableAddrInstance(ModuleInstance):
    def get_instance_by_idx(self, store):
        return store.table_obj[self.index_name]


class TableInstance(ModuleInstance): pass
class DataInstance(ModuleInstance): pass
class ElemInstance(ModuleInstance): pass
class MemInstance(ModuleInstance): pass


class OtherValue(Value):
    def init_attrs(self, **kwads):
        self.__dict__.update(kwads)

class globalItem(Value):
    def init_attrs(self, **kwads):
        self.__dict__.update(kwads)

class ReturnInstance(Value): pass

class RefsInstance(Value):
    pass

class StackValue(Value):
    def generate_svalue(self, val_relation=None):
        svalue = SValue()
        if not self.type.need_infer:
            ty = self.type
        else:
            ty = valueType.generate_any_ty()
        v_value, self_constraints, ty_value = get_traditional_type(
            ty, self.name)
        svalue.v_value = v_value
        svalue.self_constraints = self_constraints
        svalue.ty_value = ty_value
        self.svalue = svalue


def _is_val_ref_name(s):
    if s in ['\\V128', '\\I32', '\\I64', '\\F32', '\\F64',  '\\FUNCREF', '\\EXTERNREF']:
        return False
    p = r'^[a-zA-Z\\][a-zA-Z\d_\{\}\^\']*(?:\^\\ast)?$'
    if re.search(p, s):
        return True
    else:
        return False

def _is_constant_obj(ty, name):
    if ty.detail_info == 'bit width':
        return True
    elif ty.detail_info == 'constant':
        return True
    elif name.isdigit():
        return True
    elif ty.is_ref_null:
        return True
    else:
        p = r'^dim\(.+\)$'
        _processed_name = process_str(name)
        r = re.compile(p).findall(_processed_name)
        if r:
            return True
    return False


def generate_Value_from_common_line(raw_value):
    name, ty, num, idx = get_name_type_from_p(raw_value)
    p = r'^\(.*\)$'
    if re.search(p, name):
        name = name[1:-1]
    # ============================== constant ==================
    # p1
    if _is_constant_obj(ty, name):
        obj = constantValue(name, ty, raw_value, num=num)
        return obj
    # ============================== type ==================
    if ty.detail_info == 'type':
        obj = constType(name, ty, raw_value, num=num)
        return obj
    # ============================== label ==================
    if ty.detail_info == 'label':
        obj = Label(name, ty, raw_value, num=num, idx=idx)
        return obj
    # ============================== arity ==================
    if ty.detail_info == 'arity':
        obj = Arity(name, ty, raw_value, num=num)
        return obj
    # ============================== ref ================================

    # ============================== instance ==================
    if name == 'current frame':
        assert ty.detail_info == 'frame', print(ty.detail_info, name)
        return FrameInstance(name, ty, raw_value, num=num)
    p = r'^C\.\\CRETURN$'
    if re.search(p, name):
        return ReturnInstance(name, ty, raw_value, num=num)
    p = r'^C\.\\CREFS$'
    if re.search(p, name):
        return RefsInstance(name, ty, raw_value, num=num)
    p = re.compile(r'^[tT]he :ref:`result type <syntax-resulttype>` of :math:`(.*)`')
    r = p.findall(name)
    if r:
        r = r[0]
        return TypeRefValue(name, ty, raw_value, num=num, StoreName=r)
    p = re.compile(r'^the length of :math:`([^\.]+)\.([^`]*)`$')
    r = p.findall(name)
    if r:
        r = r[0]
        ty = valueType('u32')
        return LengthRefValue(name, ty, raw_value, num=num, StoreName=r[0], StoreAttr=r[1])
    #
    p = re.compile(r'^C\.\\CLABELS\[(.*)\]$')
    r = p.findall(name)
    if r:
        assert num == 1
        obj = LabelAddrInstance(name, ty, raw_value, num=num)
        obj.init_index(r[0])
        return obj
    # TypeInstance
    p = re.compile(r'^C\.\\CTYPES\[(.*)\]$')
    r = p.findall(name)
    if r:
        assert num == 1
        obj = TypeInstance(name, ty, raw_value, num=num)
        obj.init_index(r[0])
        return obj
    p = re.compile(r'^(?:(?:F\.\\AMODULE\.\\MIGLOBALS)|(?:C\.\\CGLOBALS))\[(.*)\]$')
    r = p.findall(name)
    if r:
        assert num == 1
        obj = GlobalAddrInstance(name, ty, raw_value, num=num)
        obj.init_index(r[0])
        return obj
    #
    p = r'^S\.\\SGLOBALS\[(.*)\]$'
    p = re.compile(p)
    r = p.findall(name)
    if r:
        assert num == 1
        obj = GlobalInstance(name, ty, raw_value, num=num)
        obj.init_index(r[0])
        return obj
    #
    r = re.compile(r'(.*)\.\\GIVALUE').findall(name)
    if r:
        attrs = {}
        attrs['RefName'] = r[0]
        attrs['ValType'] = 'GETVALUE'
        obj = globalItem(name, ty, raw_value, num=num)
        obj.init_attrs(**attrs)
        return obj
    p = re.compile(r'^(?:(?:F\.\\AMODULE\.\\MITABLES)|(?:C\.\\CTABLES))\[(.*)\]$')
    r = p.findall(name)
    if r:
        assert num == 1
        obj = TableAddrInstance(name, ty, raw_value, num=num)
        obj.init_index(r[0])
        return obj
    #
    p = r'^S\.\\STABLES\[(.*)\]$'
    p = re.compile(p)
    r = p.findall(name)
    if r:
        assert num == 1
        obj = TableInstance(name, ty, raw_value, num=num)
        obj.init_index(r[0])
        return obj
    #
    p = r'^(.*?)\.\\TIELEM\[(.*)\]$'
    p = re.compile(p)
    r = p.findall(name)
    if r:
        r = r[0]
        attrs = {}
        attrs['ValType'] = 'TABLE_ELEMENT'
        attrs['StoreName'] = r[0]
        attrs['index'] = r[1]
        assert num == 1
        obj = OtherValue(name, ty, raw_value, num=num)
        obj.init_attrs(**attrs)
        return obj
    p = r'^(?:(?:F\.\\ALOCALS)|(?:C\.\\CLOCALS))\[(.*)\]$'
    p = re.compile(p)
    r = p.findall(name)
    if r:
        assert num == 1
        obj = LocalAddrInstance(name, ty, raw_value, num=num)
        obj.init_index(r[0])
        return obj
    #
    p = r'^(?:(?:F\.\\AMODULE\.\\MIDATAS)|(?:C\.\\CDATAS))\[(.*)\]$'
    p = re.compile(p)
    r = p.findall(name)
    if r:
        assert num == 1
        obj = DataAddrInstance(name, ty, raw_value, num=num)
        obj.init_index(r[0])
        return obj
    #
    p = r'^(?:(?:F\.\\AMODULE\.\\MIELEMS)|(?:C\.\\CELEMS))\[(.*)\]$'
    p = re.compile(p)
    r = p.findall(name)
    if r:
        assert num == 1
        obj = ElemAddrInstance(name, ty, raw_value, num=num)
        obj.init_index(r[0])
        return obj
    #
    p = r'^(?:(?:F\.\\AMODULE\.\\MIFUNCS)|(?:C\.\\CFUNCS))\[(.*)\]$'
    p = re.compile(p)
    r = p.findall(name)
    if r:
        assert num == 1
        obj = FuncAddrInstance(name, ty, raw_value, num=num)
        obj.init_index(r[0])
        return obj
    #
    p = r'^(?:(?:F\.\\AMODULE\.\\MIMEMS)|(?:C\.\\CMEMS))\[(.*)\]$'
    p = re.compile(p)
    r = p.findall(name)
    if r:
        assert num == 1
        index = r[0]
        obj = MemAddrInstance(name, ty, raw_value, num=num)
        obj.init_index(index)
        return obj
    #
    p = r'^S\.\\SMEMS\[(.*)\]$'
    p = re.compile(p)
    r = p.findall(name)
    if r:
        assert num == 1
        obj = MemInstance(name, ty, raw_value, num=num)
        obj.init_index(r[0])
        return obj
    #
    p = r'^S\.\\SDATAS\[(.*)\]$'
    p = re.compile(p)
    r = p.findall(name)
    if r:
        assert num == 1
        obj = DataInstance(name, ty, raw_value, num=num)
        obj.init_index(r[0])
        return obj
    #
    p = r'^S\.\\SELEMS\[(.*)\]$'
    p = re.compile(p)
    r = p.findall(name)
    if r:
        assert num == 1
        obj = ElemInstance(name, ty, raw_value, num=num)
        obj.init_index(r[0])
        return obj
    if name != 'any' and ty._type != 'ref':
        if _is_val_ref_name(name) or _is_val_ref_name(raw_processor._process_macro(name)):
            obj = ValRefValue(name, ty, raw_value, num=num)
            return obj
    if name != 'any':
        obj = FormulaValue(name, ty, raw_value, num=num)
        return obj
    return Value(name, ty, raw_value, num=num)
