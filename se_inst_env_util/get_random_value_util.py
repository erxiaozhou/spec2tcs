from random import randint
import numpy as np
from file_util import bytes2f32, bytes2f64, uint2bytes


def generate_value_by_type_str(ty_str):
    if ty_str == 'i32':
        return _generate_random_int(32)
    elif ty_str == 'i64':
        return _generate_random_int(64)
    elif ty_str == 'f32':
        return get_a_random_f32()
    elif ty_str == 'f64':
        return get_a_random_f64()
    elif ty_str == 'v128':
        return [_generate_random_byte() for i in range(16)]


def _generate_random_int(bw):
    gi = randint(-(2**(bw-1)), 2**(bw-1)-1)
    return gi


def _generate_random_byte():
    return randint(0, 255)


def get_a_random_f32():
    val = None
    while val is None or val == np.nan or val == -np.nan:
        random_int = np.random.randint(0, 2**32)
        bs = uint2bytes(random_int, 4)
        val = bytes2f32(bs)[0]
    # return random_int
    return val

def get_a_random_f64():
    val = None
    while val is None or val == np.nan or val == -np.nan:
        bs = uint2bytes(np.random.randint(0, 2**32), 4) + uint2bytes(np.random.randint(0, 2**32), 4)
        val = bytes2f64(bs)[0]
    # return random_int
    return val
