class SValue:
    def __init__(self, v_value=None, ty_value=None, self_constraints=None):
        self.v_value = v_value
        self.ty_value = ty_value
        if self_constraints is None:
            self_constraints = []
        else:
            assert isinstance(self_constraints, list)
        self.self_constraints = self_constraints

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.v_value}, {self.ty_value}, {self.self_constraints})'