class execConfig:
    supported_ks = ['consider_illegal_op', 
                    'only_non_trap', 
                    'limit_ty_candidates_on_failed_ty_trap', 
                    'limit_val_cnaditaions_on_failed_ty_trap',
                    'debug_add_valid'
                ]

    def __init__(self, 
                 consider_illegal_op, 
                 only_non_trap, 
                 limit_ty_candidates_on_failed_ty_trap,
                 limit_val_cnaditaions_on_failed_ty_trap,
                 debug_add_valid=False
                 ) -> None:
        self.consider_illegal_op = consider_illegal_op
        self.only_non_trap = only_non_trap
        self.limit_ty_candidates_on_failed_ty_trap = limit_ty_candidates_on_failed_ty_trap
        self.limit_val_cnaditaions_on_failed_ty_trap = limit_val_cnaditaions_on_failed_ty_trap
        self.debug_add_valid = debug_add_valid

    def to_dict(self):
        d = {k: v for k, v in self.__dict__.items() if k in execConfig.supported_ks}
        return d

    @classmethod
    def from_dict(cls, d):
        paras = {k: d[k] for k in execConfig.supported_ks if k in d}
        return cls(**paras)
