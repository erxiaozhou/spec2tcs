import re
from .execInst import execInst
from file_util import path_read
from spec_src_file_path_util import exec_inst_rst_path


class execInsts(list):
    @classmethod
    def from_raw_rst_content(cls, content):
        # get type
        p = r'([a-zA-Z]+?) Instructions\n~+\n(.*?)(?=\n[a-zA-Z ]+\n~+\n)'
        p = re.compile(p, re.S)
        r = p.findall(content)
        instructions_ = []
        for ctgy, content in r:
            lines = content.split('\n')
            line_num = len(lines)
            break_line_p = re.compile(r'^\.+$')
            title_line_p = re.compile(r'^:math:.*$')
            break_line_indexs = []
            title_line_indexs = []
            for i in range(line_num):
                if break_line_p.findall(lines[i]):
                    break_line_indexs.append(i)
                if title_line_p.findall(lines[i]):
                    title_line_indexs.append(i)

            for i in range(len(title_line_indexs)):
                i_title_line = title_line_indexs[i]
                assert i_title_line+1 in break_line_indexs
                raw_title = lines[i_title_line]
                if i < len(title_line_indexs) - 1:
                    part_lines = lines[title_line_indexs[i]+2:title_line_indexs[i+1]]
                else:
                    part_lines = lines[title_line_indexs[i]+2:]
                raw_content = '\n'.join(part_lines)
                instructions_.append(execInst.from_raw_rst(ctgy, raw_title, raw_content))
        return cls(instructions_)

    @classmethod
    def from_raw_rst_path(cls):
        content = _get_instruction_exec_content()
        instructions = cls.from_raw_rst_content(content)
        return instructions


def _get_instruction_exec_content():
    content = path_read(exec_inst_rst_path)
    instruction_content_p = re.compile(
        r'Numeric Instructions\n.*\nBlocks\n~+\n', re.S)
    instruction_content_p = re.compile(instruction_content_p)
    instruction_content = instruction_content_p.findall(content)
    assert len(instruction_content) == 1
    instruction_content = instruction_content[0]
    return instruction_content
