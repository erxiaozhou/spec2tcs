from file_util import save_json
import re
from extract_binary_inst import extract_category_paragraph
from spec_src_file_path_util import syntax_inst_rst_path


def extend_Profuctions(productions):
    extended_index = []
    sigs = [p.sig for p in productions]
    for i, p in enumerate(productions):
        if p.is_extended(sigs):
            extended_index.append(i)
    unextended_index = [x for x in range(
        len(productions)) if x not in extended_index]
    while unextended_index:
        i = unextended_index[0]
        unextended_p = productions[i]
        for j in extended_index:
            extended_p = productions[j]
            unextended_p.extend_by_other(extended_p)
        if p.is_extended(sigs):
            unextended_index.remove(i)
            extended_index.append(i)


class Production:
    def __init__(self, sig, replace_sigs, name=None):
        self.name = name
        self.sig = sig
        self.replace_sigs = replace_sigs

    @staticmethod
    def extract_replace_sigs(content):
        content = re.sub(r'\\\\', '', content)
        r_sigs = content.split('|')
        r_sigs = [x.strip(' \n~&') for x in r_sigs]
        return r_sigs

    def is_extended(self, sigs_for_check):
        for sig in sigs_for_check:
            if self.can_extend_by_sig(sig):
                return False
        return True

    def can_extend_by_other(self, other_p):
        o_sig = other_p.sig
        for r in self.replace_sigs:
            if o_sig in r:
                return True
        return False

    def can_extend_by_sig(self, sig):
        if sig == self.sig:
            return False
        for r in self.replace_sigs:
            if sig in r:
                return True
        return False

    def extend_by_other(self, other_p):
        if not self.can_extend_by_other(other_p):
            return
        new_replace_sigs = []
        other_sig = other_p.sig
        other_r_sigs = other_p.replace_sigs
        for sig_to_be_r in self.replace_sigs:
            if other_sig in sig_to_be_r:
                for other_r_sig in other_r_sigs:
                    new_replace_sig = sig_to_be_r.replace(
                        other_sig, other_r_sig)
                    new_replace_sigs.append(new_replace_sig)
            else:
                new_replace_sigs.append(sig_to_be_r)
        self.replace_sigs = new_replace_sigs

    @classmethod
    def from_extracted(cls, sig, replace_content, name=None):
        replace_sigs = Production.extract_replace_sigs(replace_content)
        return cls(sig, replace_sigs, name)

    def __repr__(self) -> str:
        p = '{} <--> {}'
        s = p.format(self.sig, self.replace_sigs)
        return s


class inst_syntax():
    def __init__(self, inst_dict=None):
        '''
        inst_dict : {inst_ctgy: insts}
        '''
        if inst_dict is None:
            inst_dict = {}
        self.insts_dict = inst_dict

    def insert_insts(self, inst_ctgy, inst_productions):
        if self.insts_dict.get(inst_ctgy) is None:
            self.insts_dict[inst_ctgy] = {}
        target_dict = self.insts_dict[inst_ctgy]
        for p in inst_productions:
            assert isinstance(p, Production)
            if target_dict.get(p.sig) is None:
                target_dict[p.sig] = []
            target_dict[p.sig].extend(p.replace_sigs)

    @property
    def productions(self):
        global_ps = {}
        check_ps = {}
        for ctgy, ps in self.insts_dict.items():
            for k, v in ps.items():
                if k == '\\instr':
                    continue
                assert check_ps.get(k) is None, print(k)
                global_ps[(ctgy, k)] = v
                check_ps[k] = v
        return global_ps

    @property
    def productions_without_cgty(self):
        check_ps = {}
        for ctgy, ps in self.insts_dict.items():
            for k, v in ps.items():
                if k == '\\instr':
                    continue
                assert check_ps.get(k) is None, print(k)
                check_ps[k] = v
        return check_ps


    def production_keys(self):
        return list(self.productions_without_cgty.keys())

    def get_insts(self, ctgy=None):
        if ctgy is not None:
            insts = self.insts_dict[ctgy]['\\instr']
        else:
            insts = []
            for v in self.insts_dict.values():
                insts.extend(v['\\instr'])
        insts = [inst for inst in insts if inst != '\\dots']
        return insts

    def init_op_insts(self):
        self.op_insts = {}
        assert self.insts_dict
        for ctgy_data in self.insts_dict.values():
            insts = ctgy_data['\\instr']
            for k, op_names in ctgy_data.items():
                if 'op' in k:
                    self.op_insts[k] = []
                    for inst in insts:
                        for name in op_names:
                            if name in inst:
                                self.op_insts[k].append(inst)

    def save_as_json(self, path=None):
        if path is None:
            return self.insts_dict
        else:
            save_json(path, self.insts_dict)

    def save_op_inits(self, path=None):
        if path is None:
            return self.op_insts
        else:
            save_json(path, self.op_insts)


def _extract_inst_blocks_from_syx_ct_paragraph(content):
    inst_block_p = r' +\\begin\{array\}(.*?)\\end\{array\}'
    inst_block_p = re.compile(inst_block_p, re.S)
    inst_blocks = inst_block_p.findall(content)
    return inst_blocks


def _extract_inst_names_from_block(block):
    production_p = r' \\production\{(.*?)\}.*?& +(.*?) &::=&(.*?)$'
    production_p = re.compile(production_p, re.S)
    paras = []
    lines = block.split('\n')
    para_lines = []
    for line in lines:
        if re.search(r'^ + \\production', line):
            if len(para_lines):
                paras.append('\n'.join(para_lines))
                para_lines = []
            para_lines.append(line)
        else:
            if para_lines:
                para_lines.append(line)
    paras.append('\n'.join(para_lines))
    matched_productions = [production_p.findall(para)[0] for para in paras]

    ps = []
    for pp in matched_productions:
        sigs = pp[1].split(', ')
        for sig in sigs:
            product = Production.from_extracted(sig, pp[2], name=pp[0])
            ps.append(product)
    extend_Profuctions(ps)
    return ps


def get_inst_names_from_syntax():
    ct_paras = extract_category_paragraph(syntax_inst_rst_path)
    inst_names = inst_syntax()
    other_ps = []
    instr_ps = {}
    ct_names = []
    for ct_name, content in ct_paras:
        ct_names.append(ct_name)
        blocks = _extract_inst_blocks_from_syx_ct_paragraph(content)
        for block in blocks:
            ps = _extract_inst_names_from_block(block)
            for p in ps:
                if p.sig == '\\instr':
                    pass
                    assert instr_ps.get(ct_name) is None
                    instr_ps[ct_name] = p
                else:
                    other_ps.append(p)
    appended_p = Production('{N}', ['8', '16', '32'], 'append_z')
    other_ps.append(appended_p)
    other_ps_sigs = [x.sig for x in other_ps]
    assert len(other_ps_sigs) == len(set(other_ps_sigs))
    extend_Profuctions(other_ps)

    for ct_name, content in ct_paras:
        ct_names.append(ct_name)
        current_ps = []
        blocks = _extract_inst_blocks_from_syx_ct_paragraph(content)
        for block in blocks:
            current_ps.extend(_extract_inst_names_from_block(block))
        current_instr_p = [x for x in current_ps if x.sig == '\\instr'][0]
        current_ps_sigs = [x.sig for x in current_ps if x.sig != '\\instr']
        current_ps = [x for x in other_ps if x.sig in current_ps_sigs]
        extend_Profuctions(other_ps + [current_instr_p])
        current_ps.append(current_instr_p)
        inst_names.insert_insts(ct_name, current_ps)
    return inst_names
