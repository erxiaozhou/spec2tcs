from pathlib import Path
from extract_binary_inst import binEncoding
from file_util import save_json
from .generate_wasm_tc import wasm_direct_generator
from value_encoder import value_holder
import logging


class instEncodingParas:
    def __init__(self, cur_opcode, imm_vs, imm_new_index, binary_info, control_stack=None) -> None:
        self.cur_opcode = cur_opcode
        self.imm_vs = imm_vs
        self.reset_imm_vs = self.get_reset_imm_vs(imm_new_index)
        self.binary_info = binary_info
        if control_stack is None:
            control_stack = []
        self.control_stack = control_stack

    def get_reset_imm_vs(self, imm_new_index):
        if imm_new_index is None:
            imm_vs = self.imm_vs
        else:
            imm_vs = [self.imm_vs[imm_new_index[i]] for i in range(len(self.imm_vs))]
        return imm_vs


def generate_one_tc(template_config, stack_vs, tgt_path, push_ty, inst_en_paras, save_meta_data):
    template_path = template_config['template_path']
    add_data_count = template_config['add_data_count']
    template_generator = wasm_direct_generator(template_path, add_data_count, template_config['data_num'])
    new_part = _generate_new_part(stack_vs, inst_en_paras)
    template_generator.wasm_generator(tgt_path, push_ty, new_part)
    if save_meta_data:
        debug_data = {}
        debug_data['stack_vs'] = repr(stack_vs)
        debug_data['imm_vs'] = repr(inst_en_paras.imm_vs)
        debug_data['cur_opcode'] = repr(inst_en_paras.cur_opcode)
        debug_data['new_part'] = repr([hex(x) for x in new_part])
        json_path = str(tgt_path)[:-5] + '.json'
        save_json(json_path, debug_data)


def _generate_new_part(stack_vs, inst_en_paras):
    result = bytearray()
    stack_vs = stack_vs[::-1]
    for v in stack_vs:
        assert isinstance(v, value_holder), print(v, type(v), stack_vs)
        result.extend(v.const_line)
    opcode_imm_part = _get_opcode_imm_part(inst_en_paras)
    result.extend(opcode_imm_part)
    return result


def _get_opcode_imm_part(inst_en_paras: instEncodingParas):
    reset_imm_vs = inst_en_paras.reset_imm_vs
    binary_info = inst_en_paras.binary_info
    assert len([x for x in binary_info if x.is_imm]) == len(reset_imm_vs), print([x for x in binary_info if x.is_imm], len(reset_imm_vs))
    assert isinstance(inst_en_paras.cur_opcode, (list, tuple))
    visited_imm_num = 0
    opcode_imm_part = bytearray()
    opcode_imm_part.extend(inst_en_paras.cur_opcode)
    met_first_imm = False
    for i, bin_encoding in enumerate(binary_info):
        if bin_encoding.is_imm:
            opcode_imm_part.extend(reset_imm_vs[visited_imm_num].encode)
            visited_imm_num += 1
            met_first_imm = True
        elif met_first_imm and bin_encoding.attr in ['hex', 'u32']:
            opcode_imm_part.extend(bin_encoding.digit_determined_encoding)
        elif met_first_imm:
            raise Exception('unknown bin_encoding: {}'.format(bin_encoding))
    return opcode_imm_part
