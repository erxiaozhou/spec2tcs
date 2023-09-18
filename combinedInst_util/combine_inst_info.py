import re
from execInst_util import execInsts
from .extract_syntax_names import get_inst_names_from_syntax
from file_util import group_ps, read_json, save_json, check_dir

from process_text import unwrap_math
from process_text import raw_processor
from .extract_syntax_names import inst_syntax
from process_text import process_str
from valid_insts import validInsts


def get_exec_insts_possible_names(debug=False):
    # * just the text infomation has been combined
    exec_insts = execInsts.from_raw_rst_path()
    inst_names = get_inst_names_from_syntax()
    inst_ctgys = list(inst_names.insts_dict.keys())

    all_names = _get_all_names(inst_names, inst_ctgys)
    _check_exec_insts(exec_insts)

    inst_names.init_op_insts()
    print('len(all_names):', len(all_names))
    if debug:
        base_dir = check_dir('./tt/tmp_result')
        save_json(base_dir / 'all_names.json', all_names)
        save_json(base_dir / 'all_names_p.json', [process_str(s,remove_bk=True) for s in all_names])
        inst_names.save_op_inits(base_dir / 'op_insts.json')

    ctgy_exec_inst_dict = {}
    for exec_inst in exec_insts:
        ctgy = exec_inst.ctgy
        ctgy_exec_inst_dict.setdefault(ctgy, []).append(exec_inst)

    match_result = []
    matched_insts_dict = {}
    for ctgy, exec_insts in ctgy_exec_inst_dict.items():
        exec_insts = sorted(exec_insts, key=lambda x : len(x.raw_title), reverse=True)
        matched_insts_dict[ctgy] = []
        for exec_inst in exec_insts:
            inst_match_result = _expand_inst_exec_by_def(exec_inst, inst_names)
            match_result.append([exec_inst, inst_match_result])
            matched_insts_dict[ctgy].extend(inst_match_result)

    if debug:
        save_json(base_dir / 'matched_insts_dict.json', matched_insts_dict)
        matched_inst_names = []
        for mr in match_result:
            matched_inst_names.extend(mr[1])
        print('matched inst num', len(matched_inst_names))
        print('unique matched inst num', len(set(matched_inst_names)))
        print(len(set(all_names)- set(matched_inst_names)))
        print(len(set(matched_inst_names)- set(all_names)))
        lost_insts = [process_str(x) for x in set(all_names)- set(matched_inst_names)]
        save_json(base_dir / 'lost_insts.json', lost_insts)

        # save_json
        matched_data = {}
        for mr in match_result:
            matched_data[mr[0].raw_title] = mr[1]
        save_json(base_dir / 'matched_data.json', matched_data)
    return match_result


def get_valid_insts_possible_names(debug=True):
    # * just the text infomation has been combined
    insts = validInsts.from_raw_rst()
    inst_names = get_inst_names_from_syntax()
    inst_ctgys = list(inst_names.insts_dict.keys())

    all_names = _get_all_names(inst_names, inst_ctgys)
    _check_exec_insts(insts)

    inst_names.init_op_insts()
    print('len(all_names):', len(all_names))
    if debug:
        base_dir = check_dir('./tt/tmp_result_valid_bin')
        save_json(base_dir / 'all_names.json', all_names)
        save_json(base_dir / 'all_names_p.json', [process_str(s,remove_bk=True) for s in all_names])
        inst_names.save_op_inits(base_dir / 'op_insts.json')

    ctgy_exec_inst_dict = {}
    for inst in insts:
        ctgy = inst.ctgy
        ctgy_exec_inst_dict.setdefault(ctgy, []).append(inst)

    match_result = []
    matched_insts_dict = {}
    for ctgy, insts in ctgy_exec_inst_dict.items():
        insts = sorted(insts, key=lambda x : len(x.raw_title), reverse=True)
        matched_insts_dict[ctgy] = []
        for inst in insts:
            inst_match_result = _expand_inst_exec_by_def(inst, inst_names)
            match_result.append([inst, inst_match_result])
            matched_insts_dict[ctgy].extend(inst_match_result)

    if debug:
        save_json(base_dir / 'matched_insts_dict.json', matched_insts_dict)
        matched_inst_names = []
        for mr in match_result:
            matched_inst_names.extend(mr[1])
        print('matched inst num', len(matched_inst_names))
        print('unique matched inst num', len(set(matched_inst_names)))
        print(len(set(all_names)- set(matched_inst_names)))
        print(len(set(matched_inst_names)- set(all_names)))
        lost_insts = [process_str(x) for x in set(all_names)- set(matched_inst_names)]
        save_json(base_dir / 'lost_insts.json', lost_insts)

        # save_json
        matched_data = {}
        for mr in match_result:
            matched_data[mr[0].raw_title] = mr[1]
        save_json(base_dir / 'matched_data.json', matched_data)
    return match_result


def _get_all_names(inst_names, inst_ctgys):
    all_inst_names = []
    for ctgy in inst_ctgys:
        c_inst_names = inst_names.insts_dict[ctgy]
        syntax_insts = [x for x in c_inst_names['\\instr'] if x != '\\dots']
        all_inst_names.extend(syntax_insts)
    return list(set(all_inst_names))


def _generate_pattern_from_str(inst_text):
    inst_text_base = inst_text.split('~')[0]
    inst_text_base = process_str(inst_text_base, remove_bk=True)
    inst_text_base = _generate_pattern_from_str_core(inst_text_base)
    inst_text_base = re.sub(r'\^\?', '?', inst_text_base)
    return inst_text_base


def _generate_pattern_for_exec_inst(exec_inst):
    raw_title = exec_inst.raw_title
    p = r':math:`(.*?)` and :math:`(.*?)`'
    r = re.compile(p).findall(raw_title)
    if not len(r):
        inst_text = unwrap_math(raw_title)
        r_pattern = _generate_pattern_from_str(inst_text)
    else:
        r1, r2 = r[0]
        r_pattern1 = _generate_pattern_from_str(r1)
        r_pattern2 = _generate_pattern_from_str(r2)
        r_pattern = group_ps([r_pattern1, r_pattern2])
    r_pattern = ''.join(('^', r_pattern, '$'))
    return r_pattern


def _generate_pattern_from_str_core(inst_text_base):
    if re.search(r't(?:_\d)?(?=[\.x])', inst_text_base):
        inst_text_base = re.sub(r't(?:_\d)?(?=[\.x])', r'(?:(?:[if]\\d{1,2})|(?:v128))', inst_text_base)
    if re.search(r'_t_\d', inst_text_base):
        inst_text_base = re.sub(r'_t_\d', r'_(?:(?:[if]\\d{1,2})|(?:v128))', inst_text_base)
    if re.search(r'ishape(?:_\d)?(?=[\.x])', inst_text_base):
        inst_text_base = re.sub(r'ishape(?:_\d)?(?=[\.x])', r'[i]\\d{1,2}x\\d{1,2}', inst_text_base)
    if re.search(r'_ishape(?:_\d)?', inst_text_base):
        inst_text_base = re.sub(r'_ishape(?:_\d)?', r'_[i]\\d{1,2}x\\d{1,2}', inst_text_base)
    if re.search(r'shape(?:_\d)?(?=[\.x])', inst_text_base):
        inst_text_base = re.sub(r'shape(?:_\d)?(?=[\.x])', r'[if]\\d{1,2}x\\d{1,2}', inst_text_base)
    if re.search(r'_shape(?:_\d)?', inst_text_base):
        inst_text_base = re.sub(r'_shape(?:_\d)?', r'_[if]\\d{1,2}x\\d{1,2}', inst_text_base)
    if re.search(r'_half', inst_text_base):
        inst_text_base = re.sub(r'_half', r'(?:(?:_high)|(?:_low))', inst_text_base)
    if re.search(r'[NM]', inst_text_base):
        inst_text_base = re.sub(r'[NM]', r'\\d{1,2}', inst_text_base)
    if re.search(r'_sx(?:\^\?)?', inst_text_base):  # (?<!_)sx'
        inst_text_base = re.sub(r'_sx(?:\^\?)?', r'(?:_[us])?', inst_text_base)
    if re.search(r'_zero', inst_text_base):
        inst_text_base = re.sub(r'_zero', r'(?:_zero)', inst_text_base)
    return inst_text_base


def _expand_inst_exec_by_def(inst, syntax_insts):
    assert isinstance(syntax_insts, inst_syntax)
    ctgy = inst.ctgy
    inst_text = unwrap_math(inst.raw_title)
    ps = syntax_insts.productions
    op_keys = [k for k in ps.keys() if 'op' in k[1]]
    related_op_keys = [x[1] for x in op_keys]
    related_op_keys = sorted(related_op_keys, key=lambda x: len(x), reverse=True)

    inst_op_str = re.compile(r'(\\[a-z]+op)').findall(inst_text)
    if inst_op_str:
        inst_op_str = inst_op_str[0]
    else:
        inst_op_str = None

    sytax_inst_names = syntax_insts.get_insts(ctgy)
    op_related_insts = []
    for op_key in related_op_keys:
        op_related_insts.extend(syntax_insts.op_insts[op_key])

    match_result = []
    generated_pattern_str = _generate_pattern_for_exec_inst(inst)
    if inst_op_str is not None:
        if inst_op_str in related_op_keys:
            assert process_str(inst_op_str) in generated_pattern_str
            current_ps = ps[(ctgy, inst_op_str)]
            current_ps = [process_str(x, remove_bk=True) for x in current_ps]
            current_ps_p = group_ps(current_ps)
            # * current_ps_p example : (?:(?:abs)|(?:neg)|(?:abs)|(?:neg)|(?:sqrt)|(?:ceil)|(?:floor)|(?:trunc)|(?:nearest)|(?:popcnt))
            generated_pattern_str = generated_pattern_str.replace(process_str(inst_op_str), current_ps_p)
            generated_pattern_str = _generate_pattern_from_str_core(generated_pattern_str)
    generated_pattern = re.compile(generated_pattern_str)
    for ori_name in sytax_inst_names:
        name = process_str(ori_name, remove_bk=True).split('~')[0]
        r = generated_pattern.findall(name)
        if r:
            match_result.append(ori_name)
    return match_result


def _check_exec_insts(insts):
    for inst in insts:
        assert raw_processor.has_macro(inst.raw_title)
