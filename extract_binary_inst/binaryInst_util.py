import re
import leb128
from .util import s_match_p
from process_text import process_char_bracket_fmt
from process_text import raw_processor


skip_words = ['else', 'end', '\\epsilon']


class binEncoding:
    def __init__(self, text, attr, has_ast=False, num=1) -> None:
        self.text = text
        self.attr = attr
        self.has_ast = has_ast
        self.num = num

    def to_tuple(self):
        return (self.text, self.attr, self.has_ast, self.num)

    def __repr__(self) -> str:
        ast_str = ' *' if self.has_ast else ''
        num_str = f': {self.num}' if self.num > 1 else ''
        return f'<{self.text}: {self.attr}{ast_str}{num_str}>'

    def __eq__(self, o) -> bool:
        return self.to_tuple() == o.to_tuple()

    def __hash__(self) -> int:
        return hash(self.to_tuple())

    @property
    def digit_determined_encoding(self):
        assert self.is_determined()
        if self.attr == 'hex':
            return [int(self.text, 16)]
        elif self.attr == 'u32':
            bs = leb128.u.encode(int(self.text))
            return [int(b) for b in bs]
        # elif self.attr in ['i32', 'i64']:
        else:
            raise Exception(f'unknown attr: {self.attr}')

    def is_determined(self):
        if self.attr == 'hex':
            return True
        elif self.text.isdigit():
            return True
        else:
            return False

    @property
    def is_imm(self):
        if self.is_determined():
            return False
        if self.text in skip_words:
            return False
        return True


class binInstText:
    def __init__(self, bin_part, repr_part, ctgy=None) -> None:
        self.bin_part = bin_part
        self.repr_part = repr_part
        self.ctgy = ctgy

    def __repr__(self) -> str:
        return f'{self.ctgy}: {self.bin_part} ==> {self.repr_part}'


class binInstStrParser:
    hex_context_p = re.compile(r'^\\hex\{([0-9A-F]+)\}$')
    with_type_p = re.compile(r'^([^\()]+)\{:\}(.+)$')
    with_seq_p = re.compile(r'^\((.+)\{:\}(.+)\)\^\{(\d+)\}$')

    @staticmethod
    def process_one(bin_text, expand_memarg=True):
        hex_context_p = binInstStrParser.hex_context_p
        with_type_p = binInstStrParser.with_type_p
        with_seq_p = binInstStrParser.with_seq_p

        results = []
        texts = bin_text.replace('~~', '~').split('~')
        texts = [part.strip(' \n') for part in texts]
        for text in texts:
            if '^\\ast' in text:
                has_ast = True
                text = text.replace('^\\ast', '')
            else:
                has_ast = False
            # 
            if text.startswith('(') and text.endswith(')'):
                text = text[1:-1]
            # parse text
            if s_match_p(text, hex_context_p):
                hex_str = hex_context_p.findall(text)
                encoding = binEncoding(hex_str[0], 'hex')
            elif s_match_p(text, with_type_p):
                with_type_paras = with_type_p.findall(text)[0]
                imm_name = process_char_bracket_fmt(with_type_paras[0])
                imm_type = re.sub(r'\\B', '', with_type_paras[1])
                encoding = binEncoding(imm_name, imm_type, has_ast)
            elif s_match_p(text, with_seq_p):
                paras = with_seq_p.findall(text)[0]
                imm_name = process_char_bracket_fmt(paras[0])
                imm_type, num = [re.sub(r'\\B', '', p) for p in paras[1:]]
                encoding = binEncoding(imm_name, imm_type, has_ast, int(num))
            else:
                raise Exception(f'unknown pattern: <{text}>')
            if not expand_memarg:
                results.append(encoding)
            else:
                if encoding.attr == 'memarg':
                    # ALIGN
                    results.append(binEncoding(raw_processor._process_macro('\\memarg.\\ALIGN'), 'memarg_align'))
                    results.append(binEncoding(raw_processor._process_macro('\\memarg.\\OFFSET'), 'memarg_offset'))
                else:
                    results.append(encoding)
        return results

def parsed_result2str(parsed_result):
    strs = []
    for r in parsed_result:
        assert isinstance(r, binEncoding)
        strs.append(r.text)
    return '~'.join(strs)
