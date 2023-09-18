import re
from .binaryInst_util import binInstText
from .binaryInst_util import binInstStrParser
from .binaryInst_util import skip_words
from process_text import process_str
from process_text.raw_processor import _process_bk
from process_text import raw_processor


class binaryInst:
    def __init__(self, name, repr_info, opcode, binary_info, ctgy=None):
        self.name = name
        self.ctgy = ctgy
        self.binary_info = binary_info
        self.repr_info = repr_info
        self.opcode = opcode

    @classmethod
    def from_bin_inst_text(cls, bin_inst_text):
        assert isinstance(bin_inst_text, binInstText)
        bin_part_text = bin_inst_text.bin_part
        repr_part_text = bin_inst_text.repr_part
        # bin_part
        binary_info = binary_info = binInstStrParser.process_one(bin_part_text)
        # repr_part
        repr_info = get_repr_info(repr_part_text, bin_part_text)
        # name
        name = repr_info[0]
        # opcode
        opcode = get_opcode(binary_info)
        return cls(name, repr_info, opcode, binary_info, ctgy=bin_inst_text.ctgy)

    @property
    def repr_imms(self):
        imms = [w for w in self.repr_info[1:] if w not in skip_words]
        return imms

    @property
    def bin_imms(self):
        imms = []
        for encoding in self.binary_info:
            if encoding.is_imm:
                imms.append(encoding)
        return imms

    def __repr__(self):
        return repr(self.binary_info)

    @property
    def data(self):
        return {self.name: [x.to_tuple() for x in self.binary_info]}

    @property
    def imm_new_index(self):
        return _get_imm_new_index(self.repr_imms, self.bin_imms)

    @property
    def repr_imm_with_encoding(self):
        if len(self.repr_imms) == 0:
            return []
        elif len(self.repr_imms) == 1:
            return [e for e in self.binary_info if e.is_imm]
        else:    
            encoding_info = []
            d = {e.text: e for e in self.binary_info if e.is_imm}
            for imm in self.repr_imms:
                assert imm in d, print(imm, d, self.name, len(self.repr_imms), self.repr_imms)
                encoding_info.append(d[imm])
            return encoding_info


def _get_imm_new_index(imm_texts_in_name, imm_paras_in_encoding):
    imm_texts_in_encoding = [x.text for x in imm_paras_in_encoding]
    if len(imm_texts_in_encoding) > 1 and (imm_texts_in_encoding != imm_texts_in_name):
        imm_new_index = [imm_texts_in_name.index(x) for x in imm_texts_in_encoding]
    else:
        imm_new_index = None
    return imm_new_index


def get_opcode(binary_info):
    ds = []
    for encoding in binary_info:
        if encoding.is_determined():
            ds.extend(encoding.digit_determined_encoding)
        else:
            break
    return ds


def get_repr_info(repr_part_text, bin_part_text=None):
    text_parts = split_considering_bracket(repr_part_text.strip(' \n'))
    text_parts = [part.strip(' \n').replace('^\\ast', '') for part in text_parts]
    text_parts = [process_str(part, remove_bk=True) for part in text_parts]
    if bin_part_text is None:
        pass
    else:
        has_memarg = False
        for idx, text in enumerate(text_parts):
            if f'{text}:memarg' in _process_bk(process_str(bin_part_text)):
                has_memarg = True
                break
        if has_memarg:
            text_parts = text_parts[:idx] + [raw_processor._process_macro('\\memarg.\\ALIGN'), raw_processor._process_macro('\\memarg.\\OFFSET')] + text_parts[idx+1:]
    return text_parts


def split_considering_bracket(s):
    lb_num = 0
    sb_num = 0
    positions = []
    for i, c in enumerate(s):
        if c == '{':
            lb_num += 1
        elif c == '}':
            lb_num -= 1
        elif c == '(':
            sb_num += 1
        elif c == ')':
            sb_num -= 1
        elif c == '~' and lb_num == 0 and sb_num == 0:
            positions.append(i)
    if not positions:
        return [s]
    strs = []
    for i in range(len(positions) + 1):
        if i == 0:
            strs.append(s[:positions[i]])
        elif i == len(positions):
            strs.append(s[positions[i-1]+1:])
        else:
            strs.append(s[positions[i-1]+1:positions[i]])
    return strs


