from Condition_util import Condition


class Step():
    def __init__(self, hier, elems, ty, raw_line=None):
        self.raw_line = raw_line
        self.type = ty.upper()
        self.elems = elems
        self.hier = hier

    def __repr__(self):
        hier_repr = ' ' * self.hier * 2
        type_repr = self.type
        elem_repr = '{}'.format(self.elems)
        s = '{}{:<10}: {}'.format(hier_repr, type_repr, elem_repr)
        return s

    def execute(self, *args, **kwargs):
        print('UNIMPLEMENTED STEP: self.type:', self.type)

    def contains_condition(self):
        for elem in self.elems:
            if isinstance(elem, Condition):
                return True
            if isinstance(elem, list):
                for e in elem:
                    if isinstance(e, Condition):
                        return True
        return False
