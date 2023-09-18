class valueType:
    numeric_v_types = ['i32', 'i64', 'f32', 'f64', 'v128']
    legal_types = ['i32', 'i64', 'f32', 'f64', 'v128', 'any', 'ref', 'other', 'u8', 'u32', 'blocktype', 'instr', 'funcref', 'externref']

    def __init__(self, _type, detail_info=None, type_sig=None):
        assert _type in valueType.legal_types, print(f'_type: <{_type}>')
        self._type = _type
        self.type_sig = _determine_type_sig(type_sig)
        self.detail_info = _determine_detail_info(detail_info)

    def renew_type_with_type_sig_info(self, title_info):
        assert isinstance(title_info, dict), print(title_info)
        ori_type_sig = self.type_sig
        if ori_type_sig in title_info:
            self.type_sig = ''
            self._type = title_info[ori_type_sig]

    @property
    def is_ref_null(self):
        if self._type == 'ref':
            if self.detail_info == 'ref_null':
                return True
        else:
            return False

    @property
    def need_infer(self):
        if self.type_sig == '':
            return False
        else:
            return True

    def __repr__(self):
        return f'Type({self._type}:{self.detail_info}:{self.type_sig})'

    def __eq__(self, __o):
        if self._type == __o._type:
            if self.type_sig == __o.type_sig:
                if self.detail_info == __o.detail_info:
                    return True
        return False

    def __hash__(self):
        return hash((self._type, self.detail_info, self.type_sig))

    def is_unconstrained_ty(self):
        if self._type == 'any':
            if self.type_sig == '' and self.detail_info == '':
                return True
        return False

    @classmethod
    def generate_any_ty(cls):
        return cls('any')


def _determine_type_sig(type_sig):
    if type_sig is not None:
        assert type_sig != ''
        assert isinstance(type_sig, str)
    else:
        type_sig = ''
    return type_sig

def _determine_detail_info(detail_info):
    if detail_info is not None:
        assert detail_info != ''
        assert isinstance(detail_info, str)
    else:
        detail_info = ''
    return detail_info
