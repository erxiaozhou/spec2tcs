import re
from file_util import path_read, save_json
from .binaryInst import binInstText, binaryInst
from file_util import path_read
from spec_src_file_path_util import bin_inst_rst_path


class binaryInsts(list):
    @classmethod
    def from_raw_rst_path(cls, rst_path=None):
        insts = []
        if rst_path is None:
            rst_path = bin_inst_rst_path
        ctgy2bin_inst_text_pairs = _get_ctgy2bin_inst_texts(rst_path)

        for ctgy, bin_inst_texts in ctgy2bin_inst_text_pairs.items():
            for bin_inst_text in bin_inst_texts:
                assert isinstance(bin_inst_text, binInstText)
                bin_inst_text.ctgy = ctgy
                binary_inst = binaryInst.from_bin_inst_text(bin_inst_text)
                insts.append(binary_inst)
        return cls(insts)

    def get_brief_info(self):
        to_save_data = {}
        for inst in self:
            ctgy = inst.ctgy
            to_save_data.setdefault(ctgy, []).append(inst.data)
        return to_save_data

    def save_brief_info(self, path):
        to_save_data = self.get_brief_info()
        save_json(path, to_save_data)


def _get_ctgy2bin_inst_texts(rst_path):
    ctgy_content_pairs = extract_category_paragraph(rst_path)
    ctgy2bin_inst_texts = {}
    for ctgy, content in ctgy_content_pairs:
        inst_blocks = _extract_inst_blocks_from_ct_paragraph(content)
        assert len(inst_blocks)
        ctgy2bin_inst_texts[ctgy] = []
        for block in inst_blocks:
            bbin_inst_texts = _extract_inst_lines_from_inst_block(block)
            bbin_inst_texts = [binInstText(*x) for x in bbin_inst_texts]
            ctgy2bin_inst_texts[ctgy].extend(bbin_inst_texts)
    return ctgy2bin_inst_texts


def _extract_inst_blocks_from_ct_paragraph(content):
    inst_block_p = r' +\\begin\{array\}.*?\\production\{instruction\}(.*?)\\end\{array\}'
    inst_block_p = re.compile(inst_block_p, re.S)
    inst_blocks = inst_block_p.findall(content)
    return inst_blocks


def _extract_inst_lines_from_inst_block(block):
    p = r'(\\hex\{[0-9A-Za-z]+?\}.*?)&\\Rightarrow& ?(.*?) ?\\{2}'
    p = re.compile(p, re.S)
    bin_inst_text_pairs = p.findall(block)
    return bin_inst_text_pairs


def extract_category_paragraph(path):
    content = path_read(path)
    p = r'\n([a-zA-Z]+?) Instructions\n~+\n(.*?)(?=\n[a-zA-Z ]+\n~+\n)'
    p = re.compile(p, re.S)
    ctgy_content_pairs = p.findall(content)
    return ctgy_content_pairs