from .valueType import valueType
POP_TYPE = -1
PUSH_TYPE = 1

class tySeq:
    def __init__(self, ty_seq):
        assert isinstance(ty_seq, list)
        ty_seq = [tuple(x) for x in ty_seq]
        for ty, num in ty_seq:
            assert isinstance(ty, valueType), print(ty_seq)
            assert isinstance(num, (int, str))
        self.ty_seq = ty_seq

    def __eq__(self, o):
        return self.ty_seq == o.ty_seq

    def __hash__(self):
        return hash(tuple(self.ty_seq))

    def __repr__(self):
        return f'{self.__class__.__name__}({self.ty_seq})'

    def __getitem__(self, i):
        return self.ty_seq[i]

    def __iter__(self):
        return iter(self.ty_seq)

    @classmethod
    def from_ty_str_seq(cls, ty_str_seq):
        ty_seq = []
        for ty_str in ty_str_seq:
            ty = valueType(ty_str)
            ty_seq.append((ty, 1))
        return cls(ty_seq)

    @property
    def num(self):
        num_seq = [num for ty, num in self]
        all_num = True
        for num in num_seq:
            if not isinstance(num, int):
                all_num = False
                break
        if all_num:
            return sum(num_seq)
        else:
            return num_seq

    @property
    def as_expanded_seq(self):
        result = []
        for ty, num in self:
            if isinstance(num, int):
                result.extend([ty] * num)
            else:
                raise Exception('Meaninhless operation for poly stack type')
        return result

