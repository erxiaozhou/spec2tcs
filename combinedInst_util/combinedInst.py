from copy import deepcopy
import re
from Step_util import LetStep
from Step_util import get_steps_skip_repeat
from Value_util import valueType
from execInst_util import execInst
from extract_binary_inst import binaryInst
from extract_binary_inst import binEncoding
from file_util import save_json
from process_text import process_str, raw_processor, unwrap_math
from Value_util import ModuleInstance, constType
from collections import Counter
from Value_util import tySeq, POP_TYPE, PUSH_TYPE
from valid_insts import validInst

class combinedInst():
    def __init__(self, bin_inst, valid_inst, exec_inst, name):
        assert isinstance(bin_inst, binaryInst)
        assert isinstance(valid_inst, validInst)
        assert isinstance(exec_inst, execInst)
        self.bin_inst = bin_inst
        self.exec_inst = exec_inst
        self.valid_inst = valid_inst
        self.name = name
        self.ctgy = exec_inst.ctgy
        self._init_imm_name2encoding()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.name})'

    @property
    def require_state_variables(self):
        for v in self.exec_inst.all_values:
            if isinstance(v, ModuleInstance):
                return True
        return False

    @property
    def opcode(self):
        return self.bin_inst.opcode

    @property
    def binary_info(self):
        binary_info = []
        for encoding in self.bin_inst.binary_info:
            binary_info.append(encoding)
        return binary_info

    def _init_imm_name2encoding(self):
        imm_repr_binary_info = self.bin_inst.repr_imm_with_encoding
        for encoding in imm_repr_binary_info:
            assert encoding.is_imm, print(self.name, encoding)
        self.exec_imm_name2encoding = self.get_imm_name2encoding(self.exec_inst.exec_imms, imm_repr_binary_info)
        self.valid_imm_name2encoding = self.get_imm_name2encoding(self.valid_inst.valid_imms, imm_repr_binary_info)

    def get_imm_name2encoding(self, imms, imm_repr_binary_info):
        imm_name2encoding = {}
        for imm_name, encoding in zip(imms, imm_repr_binary_info):
            new_encoding_para = encoding.__dict__.copy()
            new_encoding_para['text'] = imm_name
            new_encoding = binEncoding(**new_encoding_para)
            imm_name2encoding[imm_name] = new_encoding
        return imm_name2encoding

    def init_exec_title_paras(self, sorted_production_list):
        paras_in_title = infer_op_name_from_binary_name(
            self.exec_inst.name, self.bin_inst.name, sorted_production_list)
        another_paras_in_title = infer_op_name_from_binary_name(
            self.exec_inst.another_name, self.bin_inst.name, sorted_production_list)
        if len(another_paras_in_title) > len(paras_in_title):
            paras_in_title = another_paras_in_title
        assert isinstance(paras_in_title, dict)
        self.exec_title_paras = paras_in_title
        # valid title paras
        self.valid_title_paras = infer_op_name_from_binary_name(self.valid_inst.name, self.bin_inst.name, sorted_production_list)

    def save(self, path):
        imms = {name: repr(encoding) for name, encoding in self.exec_imm_name2encoding.items()}
        all_data = {}
        all_data['exec_data'] = self.exec_inst.as_data()
        all_data['valid_data'] = self.valid_inst.as_data()
        all_data['imms'] = imms
        all_data['exec_title_paras'] = self.exec_title_paras
        all_data['binary_info'] = [repr(e) for e in self.bin_inst.binary_info]
        save_json(path, all_data)

    @property
    def push_type_with_exec_title_info(self):
        inferred_ty = self.exec_inst.vstack_vt_num_seq
        has_push_tys = [(ty, n) for (ty, n), in_or_out in inferred_ty if in_or_out == PUSH_TYPE]
        if len(has_push_tys) == 0:
            has_push_ty = None
        else:
            try:
                assert len(has_push_tys) == 1
            except Exception as e:
                if self.name == 'local.tee':
                    has_push_tys = [has_push_tys[0]]
                else:
                    raise e
            has_push_ty = has_push_tys[0][0]
            try:
                has_push_ty = self.simplify_one_ty(has_push_ty)
            except:
                assert 0
        return has_push_ty

    def simplify_one_ty(self, has_push_ty, add_extend=False):
        ty_paras = {k:v for k,v in self.exec_title_paras.items()}
        if add_extend:
            ty_paras.update(self._get_init_expand_type())
        assert isinstance(has_push_ty, valueType)
        if has_push_ty.type_sig:
            if 'extract_lane' in self.name:
                has_push_ty = ty_paras['t_1']
                has_push_ty = has_push_ty.split('x')[0]
            else:
                assert has_push_ty.type_sig in ty_paras, print(ty_paras, has_push_ty.type_sig)
                has_push_ty = ty_paras[has_push_ty.type_sig]
        elif has_push_ty._type == 'ref' and has_push_ty.detail_info == 'ref_func':
            has_push_ty = 'funcref'
        else:
            has_push_ty = has_push_ty._type
        if has_push_ty == 'i8' or has_push_ty == 'i16':
            has_push_ty = 'i32'
        return has_push_ty

    def _get_init_expand_type(self):
        let_steps = [x for x in self.exec_inst.steps if isinstance(x, LetStep)]
        let_steps = [x for x in let_steps if isinstance(x.val_2, constType)]
        d = {}
        for let_step in let_steps:
            assert isinstance(let_step, LetStep)
            name = let_step.val_1.name
            ty_val = deepcopy(let_step.val_2)
            assert isinstance(ty_val, constType)
            ty_val.update_name(self.exec_title_paras)
            ty_val.infer_value()
            ty_val = ty_val.constant_value
            d[name] = ty_val
        return d

    @property
    def infer_std_pop_ty_seq(self):
        seq = []
        for (ty, num), push_pop_ty in self.exec_inst.vstack_vt_num_seq:
            if push_pop_ty == POP_TYPE:
                ty_str = self.simplify_one_ty(ty, add_extend=True)
                ty = valueType(ty_str)
                seq.append((ty, num))
        return tySeq(seq)

    @property
    def skip_repeat_exec_steps(self):
        return get_steps_skip_repeat(self.exec_inst.steps)

    @property
    def infer_std_type_for_opcodes(self):
        pop_ty = self.infer_std_pop_ty_seq
        push_ty = self.push_type_with_exec_title_info
        type_sig = str([pop_ty, push_ty])
        return type_sig


def infer_op_name_from_binary_name(exec_name, binary_name, processed_productions):
    redirect_dict = {}
    op_matched = False
    for exec_sg, binary_sgs in processed_productions:
        if op_matched and exec_sg.endswith('op'):
            continue
        if exec_sg in exec_name:
            for binary_sg in binary_sgs:
                if binary_sg in binary_name:
                    redirect_dict[exec_sg] = binary_sg
                    if exec_sg.endswith('op'):
                        op_matched = True
            if redirect_dict.get(exec_sg) is None:
                redirect_dict[exec_sg] = ''
    t_p_sum = r'(?:(?:(t)[\.x])|(?:(t_\d)))'
    type_in_binary_name = r'((?:v128)|(?:[if](?:(?:8)|(?:16)|(?:32)|(?:64))))'
    t_p_sum = re.compile(t_p_sum)
    type_in_binary_name = re.compile(type_in_binary_name)
    exec_r = t_p_sum.findall(exec_name)
    binary_r = type_in_binary_name.findall(binary_name)
    if exec_r:
        assert len(exec_r) == len(binary_r), print(f'{exec_name}', binary_name, len(exec_r), len(binary_r), exec_r[0], '<>', f'<{exec_r[1]}>', f'{binary_r}')
        added_type_dict = {}
        for exec_type, binary_type in zip(exec_r, binary_r):
            if exec_type[0]:
                exec_type = exec_type[0]
            else:
                exec_type = exec_type[1]
            added_type_dict[exec_type] = binary_type
        redirect_dict.update(added_type_dict)

    if 'N' in exec_name or 'M' in exec_name:
        if redirect_dict.get('sx') == '':
            partly_replaced_p = re.sub('_sx', '', exec_name)
        else:
            partly_replaced_p = exec_name
        for k, v in redirect_dict.items():
            partly_replaced_p = partly_replaced_p.replace(k, '.*?')
        partly_replaced_p = partly_replaced_p.replace('N', '(?P<N>\d+)')
        partly_replaced_p = partly_replaced_p.replace('M', '(?P<M>\d+)')
        r = re.search(partly_replaced_p, binary_name)
        if r:
            redirect_dict.update(r.groupdict())
    return redirect_dict
