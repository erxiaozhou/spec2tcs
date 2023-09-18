from random import randint
import struct
from Value_util import valueType
import leb128
import numpy as np


class value_holder:
    def __init__(self, constant=None, type_str=None, generated_value=None, *args, **kwads):
        assert constant is not None or type_str is not None
        self.constant = constant
        self.type_str = _process_type(type_str)
        self.generated_value = generated_value

    @property
    def encode(self):
        raise ValueError('Have not implemented the method encode')

    def __repr__(self):
        fmt = '{}:{}:{}'
        type_str = _process_possible_none(self.type_str)
        constant = _process_possible_none(self.constant)
        generated_value = _process_possible_none(self.generated_value)
        return fmt.format(repr(type_str), repr(constant), repr(generated_value))

    def __hash__(self) -> int:
        return hash((self.type_str, repr(self.encode)))

    def __eq__(self, __o: object) -> bool:
        return hash(self) == hash(__o)

    @property
    def const_line(self):
        result = bytearray()
        if isinstance(self.const_op, int):
            result.append(self.const_op)
        else:
            assert isinstance(self.const_op, list)
            result.extend(self.const_op)
        result.extend(self.encode)
        return result


class i32_holder(value_holder):
    const_op = 65

    @property
    def encode(self):
        if self.generated_value is not None:
            return self.generated_value
        else:
            assert self.constant is not None
            assert self.type_str == 'i32'
            return leb128.i.encode(self.constant)


class ref_null_holder(value_holder):
    const_op = 0xD0
    @property
    def encode(self):
        assert self.constant in [0x70, 0x6F]
        return bytearray([self.constant])


class i64_holder(value_holder):
    const_op = 66

    @property
    def encode(self):
        if self.generated_value is not None:
            return self.generated_value
        else:
            assert self.constant is not None
            assert self.type_str == 'i64'
            return leb128.i.encode(self.constant)


class f32_holder(value_holder):
    const_op = 67

    @property
    def encode(self):
        if self.generated_value is not None:
            return self.generated_value
        else:
            assert self.constant is not None
            assert self.type_str == 'f32'
            return bytearray(struct.pack('<f', self.constant))


class f64_holder(value_holder):
    const_op = 68

    @property
    def encode(self):
        if self.generated_value is not None:
            return self.generated_value
        else:
            assert self.constant is not None
            assert self.type_str == 'f64'
            return bytearray(struct.pack('<d', self.constant))


class v128_holder(value_holder):
    const_op = [0xfd, 12]
    def __init__(self, *args, **kwads):
        super().__init__(*args, **kwads)
        if self.generated_value is None:
            assert isinstance(self.constant, (list, int)), print(self.constant)
            if isinstance(self.constant, list):
                assert len(self.constant) == 16

    @property
    def encode(self):
        if self.generated_value is not None:
            return self.generated_value
        elif self.constant is not None and isinstance(self.constant, list):
            return bytearray([x for x in self.constant])
        elif self.constant is not None and isinstance(self.constant, int):
            return bytearray(int.to_bytes(self.constant, 16, byteorder='little'))
        else:
            raise ValueError('self.constant should not be none')


class ref_holder(value_holder):
    const_op = 0xD2  # ref.func
    @property
    def encode(self):
        if self.generated_value is not None:
            return self.generated_value
        elif self.constant is not None:
            return leb128.u.encode(self.constant)
        else:
            raise ValueError('self.constant should not be none')


class u8_holder(value_holder):
    @property
    def encode(self):
        if self.generated_value is not None:
            return self.generated_value
        else:
            assert self.constant is not None
            return leb128.u.encode(self.constant)

class vec_holder(value_holder):
    @property
    def encode(self):
        if self.generated_value is not None:
            return self.generated_value
        else:
            assert self.constant is not None
            constant = leb128.u.encode(self.constant)
            len_encoding = leb128.u.encode(len(constant))
            return len_encoding + constant


class u32_holder(value_holder):
    @property
    def encode(self):
        if self.generated_value is not None:
            return self.generated_value
        else:
            assert self.constant is not None
            return leb128.u.encode(self.constant)

class blocktype_holder(value_holder):
    @property
    def encode(self):
        return bytearray([0x40])

class instr_holder(value_holder):
    @property
    def encode(self):
        return bytearray([0x0] * 5)

def holder_factory(constant=None, type_str=None, generated_value=None, *args, **kwads):
    ty_str2ty_holder = {
        'i32': i32_holder,
        'i64': i64_holder,
        'f32': f32_holder,
        'f64': f64_holder,
        'v128': v128_holder,
        'byte': u8_holder,
        'laneidx': u8_holder
    }
    u32_strs = ['memarg_offset', 'memarg_align', 'globalidx', 'localidx', 'funcidx', 'tableidx', 'elemidx', 'dataidx', 'labelidx']
    if type_str in ['i32', 'i64', 'f32', 'f64', 'v128', 'u8', 'laneidx']:
        return ty_str2ty_holder[type_str](constant, type_str, generated_value, *args, **kwads)
    elif type_str == 'ref':
        return ref_holder(constant, type_str, generated_value, *args, **kwads)
    elif type_str in u32_strs:
        return u32_holder(constant, type_str, generated_value, *args, **kwads)
    elif type_str == 'reftype':
        return u8_holder(constant, type_str, generated_value, *args, **kwads)
    elif type_str == 'ref_null':
        return ref_null_holder(constant, type_str, generated_value, *args, **kwads)
    elif type_str == 'vec(valtype)':
        return vec_holder(constant, type_str, generated_value, *args, **kwads)
    elif type_str == 'blocktype':
        return blocktype_holder(constant, type_str, generated_value, *args, **kwads)
    elif type_str == 'instr':
        return instr_holder(constant, type_str, generated_value, *args, **kwads)
    else:
        raise Exception(f'Unexpected type_str {type_str}')


def _get_special_values():
    p0_32 = bytearray([0] * 4)
    p0_64 = bytearray([0] * 8)
    n0_32 = bytearray([0] * 3 + [0x80])
    n0_64 = bytearray([0] * 7 + [0x80])
    _special_value_dict = {
        'i32': [0, 1, 2**31-1, -2**31, -1],  # 2**32-1
        'i64': [0, 1, 2**63-1, -2**63, -1],  # 2**64-1
        'f32': [np.inf, -np.inf, p0_32, n0_32,
                np.nan, -np.nan,
                 ],
        'f64': [np.inf, -np.inf, p0_64, n0_64, 
                np.nan, -np.nan,
                ],
        'v128': [bytearray([0xff]*16), bytearray([0x0]*16)],
        'ref': [0, 1],
        'memarg_offset': [0, 65535],
        'memarg_align': [0, 2, 4],
        'u8': [0, 1, 255, 254],
        'reftype': [0x6F, 0x70],
        'ref_null': [0x6F, 0x70],
        'vec(valtype)': [0x70, 0x6F, 0x7B, 0x7C, 0x7D, 0x7E, 0x7F],
        'labelidx': [0, 1],
        'laneidx': [0,1, 16]
        # ''
    }
    return _special_value_dict


class candidate_values(list):
    _special_value_dict = _get_special_values()

    def __init__(self, ty, values, added_special=False):
        super().__init__(values)
        self.ty = _process_type(ty)
        for v in values:
            assert isinstance(v, value_holder)
        self.added_special = added_special

    def append_special_values(self, template_config=None):
        assert self.ty != 'any'
        assert not self.added_special
        if self.ty in candidate_values._special_value_dict:
            to_append = candidate_values._special_value_dict[self.ty]
            self.added_special = True
        else:
            ty_name2len_name = {
                'globalidx': 'global_len',
                'localidx': 'local_len',
                'funcidx': 'func_num',
                'tableidx': 'table_num',
                'elemidx': 'elem_num',
                'dataidx': 'data_num'
            }
            assert self.ty in ty_name2len_name, print(self.ty)
            assert template_config is not None
            len_name = ty_name2len_name[self.ty]
            to_append = [0, template_config[len_name] - 1]
            self.added_special = True
        to_append = to_append[:]
        for val in to_append:
            if isinstance(val, bytearray):
                val = holder_factory(type_str=self.ty, generated_value=val)
                self.append(val)
            else:
                val = holder_factory(type_str=self.ty, constant=val)
                self.append(val)

    def set_added_special(self):
        self.added_special = True

    def __repr__(self):
        values_str = super().__repr__()
        s = f'{self.__class__.__name__}({self.ty}: {values_str})'
        return s

    @classmethod
    def from_raw_data_list(cls, ty, data_list, add_special=False, template_config_for_special_val=None):
        vals = [holder_factory(constant=val, type_str=ty) for val in data_list]
        obj = cls(ty, vals, False)
        if add_special:
            obj.append_special_values(template_config_for_special_val)
        return obj

    @classmethod
    def from_blocktype_raw_list(cls, data_list, add_special=False, template_config_for_special_val=None):
        ty = 'blocktype'
        vals = [holder_factory(constant=val, type_str=ty) for val in data_list]
        obj = cls(ty, vals, False)
        obj.set_added_special()
        return obj

    @classmethod
    def from_instr_raw_list(cls, data_list, add_special=False, template_config_for_special_val=None):
        ty = 'instr'
        vals = [holder_factory(constant=val, type_str=ty) for val in data_list]
        obj = cls(ty, vals, False)
        obj.set_added_special()
        if 0:
            obj.append_special_values(template_config_for_special_val)
        return obj


def _process_type(ty):
    if isinstance(ty, valueType):
        ty = ty._type
    elif isinstance(ty, str):
        pass
    return ty


def _process_possible_none(s):
    if s is None:
        return ''
    else:
        return s


def _append_anans(ty, to_append):
    if ty == 'f32':
        nan32_p_head = 0b0111111111 << 22
        nan32_n_head = 0b1111111111 << 22
        random_part = randint(0, 2**22-1)
        a_nan32_p_v = random_part + nan32_p_head
        a_nan32_p =  a_nan32_p_v.to_bytes(4, byteorder="little")
        a_nan32_p = bytearray(a_nan32_p)
        to_append.append(a_nan32_p)
        random_part = randint(0, 2**22-1)
        a_nan32_n_v = random_part + nan32_n_head
        a_nan32_n =  a_nan32_n_v.to_bytes(4, byteorder="little")
        a_nan32_n = bytearray(a_nan32_n)
        to_append.append(a_nan32_n)
    if ty == 'f64':
        nan64_p_head = 0b0111111111111 << 51
        nan64_n_head = 0b1111111111111 << 51
        random_part = randint(0, 2**51-1)
        a_nan64_p_v = random_part + nan64_p_head
        a_nan64_p =  a_nan64_p_v.to_bytes(8, byteorder="little")
        a_nan64_p = bytearray(a_nan64_p)
        to_append.append(a_nan64_p)
        random_part = randint(0, 2**51-1)
        a_nan64_n_v = random_part + nan64_n_head
        a_nan64_n =  a_nan64_n_v.to_bytes(8, byteorder="little")
        a_nan64_n = bytearray(a_nan64_n)
        to_append.append(a_nan64_n)
