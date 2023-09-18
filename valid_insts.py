'''
extract the information of each instruction from the file valid/instructions.rst`. The information of each instruction is organized in an instance of `validInst` class. All `validInst` instances are organized in an instance of `validInsts` class.
'''
from spec_src_file_path_util import vaiid_inst_rst_path
import re
from Value_util import Value
from file_util import save_json
from process_text import raw_processor
from process_text import unwrap_math
from Value_util import valueType
from file_util import path_read
from Step_util import StepFactory
from Step_util import Steps
from execInst_util.execInst import _extract_imm_from_exec_name_from_title


class validInst():
    def __init__(self, raw_title, steps, ctgy) -> None:
        self.raw_title = raw_title
        self.name = raw_processor.process_raw_title(raw_title)
        self.steps = steps
        self.ctgy = ctgy
        self.valid_imms = _extract_imm_from_exec_name_from_title(raw_title)

    @classmethod
    def from_raw_rst(cls, ctgy, inst_title, inst_text):
        steps = Steps.from_valid_inst_text(inst_text)
        return cls(inst_title, steps, ctgy)

    def as_data(self):
        d = {
            'raw_title': self.raw_title,
            'name': self.name,
            'ctgy': self.ctgy,
            'steps': self.steps.as_data()
        }
        return d


class validInsts(list):
    @classmethod
    def from_raw_rst(cls, path=vaiid_inst_rst_path):
        ctgy_name_and_texts = _extract_inst_contents(path)
        assert len(ctgy_name_and_texts) == 8, print (len(ctgy_name_and_texts))
        insts = []
        for ctgy, ctgy_text in ctgy_name_and_texts:
            inst_title_texts = extract_insts_text_from_ctgy_text(ctgy_text)
            for inst_title_text in inst_title_texts:
                inst_title, inst_text = inst_title_text
                insts.append(validInst.from_raw_rst(ctgy, inst_title, inst_text))
        return insts


def _extract_inst_contents(path):
    text = path_read(path)
    p = re.compile(r"Numeric Instructions.*?(?=Instruction Sequences)", re.S)
    text = p.findall(text)[0]
    ctgy_p = r'([a-zA-Z]+?) Instructions\n~+\n(.*?)(?:(?=\n[a-zA-Z ]+\n~+\n)|$)'
    ctgy_name_and_texts = re.compile(ctgy_p, re.S).findall(text)
    return ctgy_name_and_texts


def extract_insts_text_from_ctgy_text(ctgy_text):
    insts_p = r'(?:\n|^)(:math:`.*?`)\n\.+\n(.*?)(?:(?=\n:math:`.*?`\n\.+)|$)'
    insts_texts = re.compile(insts_p, re.S).findall(ctgy_text)
    return insts_texts


if __name__ == '__main__':
    insts = validInsts.from_raw_rst()
    print(len(insts))
