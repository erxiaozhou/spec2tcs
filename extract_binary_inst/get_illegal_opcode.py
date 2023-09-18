from file_util import save_json
from .binaryInsts import binaryInsts


def get_illegal_opcode():
    opcodes = _get_opcodes()
    illegal_opcodes = {
        'single': [],
        'fd': []
    }
    legal_opcodes = {
        'single': [],
        'fd': []
    }
    control_ops = [0, 1, 2, 3, 4, 0x0C, 0x0D, 0x0E, 0x0F, 0x11, 0x10]
    legal_opcodes['single'].extend(control_ops)
    for opcode in opcodes:
        if len(opcode) == 1:
            legal_opcodes['single'].append(opcode[0])
        else:
            if opcode[0] == 0xfd:
                legal_opcodes['fd'].append(opcode[1])
    illegal_opcodes['single'] = [i for i in range(0, 255) if i not in legal_opcodes['single']]
    illegal_opcodes['fd'] = [i for i in range(0, 255) if i not in legal_opcodes['fd']]
    return illegal_opcodes


def _get_opcodes():
    bis = binaryInsts.from_raw_rst_path()
    opcodes = [b_inst.opcode for b_inst in bis]
    save_json('tt/t3.json', opcodes)
    return opcodes
