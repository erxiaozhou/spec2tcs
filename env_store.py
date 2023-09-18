from copy import deepcopy
import claripy
from env_store_util import get_value_name_in_store_dict
from extract_binary_inst import get_illegal_opcode
from Value_util import generate_val_for_one_imm
from Value_util import tySeq


class env_store_config:
    def __init__(self, title_info, template_config, cinst, visited_illegalop_ty, consider_illegal_op):
        self.title_info = title_info
        self.template_config = template_config
        self.cinst = cinst
        self.consider_illegal_op = consider_illegal_op
        assert isinstance(visited_illegalop_ty, list)
        self.visited_illegalop_ty = visited_illegalop_ty
        self.exec_imm_encoding = cinst.exec_imm_name2encoding
        self.valid_imm_encoding = cinst.valid_imm_name2encoding
        self.opcode = cinst.opcode
        if cinst.name in ['br']:
            self.need_control_stack = True
        else:
            self.need_control_stack = False

class env_store:
    def __init__(self, store_config:env_store_config):
        self._opcode_candidates = None
        self.stack = []
        if store_config.need_control_stack:
            self.control_stack = [
                [['i32', 'i32'], ['i32']],
                [['i32', 'i32'], ['i32']],
                [['i32', 'i32'], ['i32']]
            ]
            self.control_stack = [[tySeq.from_ty_str_seq(in_type), tySeq.from_ty_str_seq(out_type)] for in_type, out_type in self.control_stack]
            self.control_stack_len = len(self.control_stack)
            self.outest_input = self.control_stack[0][0]
            self.outest_output = self.control_stack[0][1]
        else:
            self.control_stack = []
            self.control_stack_len=0
        self.global_obj = {}
        self.local_obj = {}
        self.memory_obj = {}
        self.table_obj = {}
        self.func_obj = {}
        self.elem_obj = {}
        self.data_obj = {}
        self.value_relation = {}
        self.stack_top = 0
        self.explored_top = 0
        self.stack_max = None
        self.imm_values = []
        self.is_defined_block_type = True

        self.init_title_info(store_config.title_info)
        self.template_config = store_config.template_config.copy()
        self.cinst = store_config.cinst
        self.consider_illegal_op = store_config.consider_illegal_op
        self.visited_illegalop_ty = store_config.visited_illegalop_ty
        self._init_exec_imm(store_config.exec_imm_encoding, store_config.valid_imm_encoding)
        self.opcode_default = store_config.opcode

    def init_title_info(self, title_info):
        self.title_info = deepcopy(title_info)
        self.propagate_info = deepcopy(title_info)

    def _init_exec_imm(self, exec_imm_name2encoding, valid_imm_name2encoding):
        assert isinstance(exec_imm_name2encoding, dict)
        imm_exec_symbols = get_imm_sybl_dict(exec_imm_name2encoding)
        self.imm_values = list(imm_exec_symbols.values())
        for imm_name, v in imm_exec_symbols.items():
            new_name = get_value_name_in_store_dict(imm_name, self.value_relation)
            self.value_relation[new_name] = v
        for imm_name, v in zip(valid_imm_name2encoding.keys(), self.imm_values):
            if imm_name not in self.value_relation:
                new_name = get_value_name_in_store_dict(imm_name, self.value_relation)
                self.value_relation[new_name] = v

    @property
    def opcode_candidates(self):
        if (self._opcode_candidates is None):
            return [self.opcode_default]
        else:
            assert isinstance(self._opcode_candidates, list)
            return self._opcode_candidates

    def get_opcode_candidates(self, is_legal):
        illegal_ops = get_illegal_opcode()
        self._opcode_candidates = []
        assert isinstance(self.visited_illegalop_ty, list)
        print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
        type_has_been_visited = self.cinst.infer_std_type_for_opcodes in self.visited_illegalop_ty
        if is_legal:
            assert isinstance(self.opcode_default, list)
            self._opcode_candidates.append(self.opcode_default)
            return True
        elif (not type_has_been_visited) and self.consider_illegal_op:
            if len(self.opcode_default) == 1:
                self._opcode_candidates = [[x] for x in illegal_ops['single'][:]]
            else:
                # single opcode strategy
                assert self.opcode_default[0] in [0xfc, 0xfd], print(self.cinst,'\n\n', self.opcode_default)
                self._opcode_candidates = [[x] for x in illegal_ops['single'][:]]
            return True
        else:
            return False


def get_imm_sybl_dict(imm_name2encoding):
    assert isinstance(imm_name2encoding, dict)
    new_dict = {}
    for name, encoding in imm_name2encoding.items():
        new_dict[name] = generate_val_for_one_imm(name, encoding)
    return new_dict
