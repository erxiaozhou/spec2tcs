import claripy


def _prepare_len(len_num, bw, symbal_name, fixed_len=True):
    if fixed_len:
        len_value = len_num
    else:
        len_value = claripy.BVS(symbal_name, bw)
    return len_value


class tableInstanceModel:
    def __init__(self, length=10):
        self.len = _prepare_len(length, 64, 'table_len', fixed_len=False)


class memoryInstanceModel:
    def __init__(self, length=1):
        self.len = _prepare_len(length, 64, 'memory_len')


class dataInstanceModel:
    def __init__(self, length=3):
        self.len = _prepare_len(length, 64, 'data_len', fixed_len=False)


class elementInstanceModel:
    def __init__(self, length=3):
        self.len = _prepare_len(length, 64, 'elem_len', fixed_len=False)

class globalValModel: pass
class localValModel: pass
class funcModel: pass
