import pytest
from extract_binary_inst.binaryInsts import _get_ctgy2bin_inst_texts
from file_util import save_json, read_json
from pathlib import Path
from extract_binary_inst.binaryInst import binaryInst
from extract_binary_inst.binaryInst_util import binInstText
from extract_binary_inst import binEncoding
from process_text import raw_processor
from spec_src_file_path_util import bin_inst_rst_path


last_extracted_data_path = 'tests/testing_data/inst_binary_info.json'


def test_get_ctgy2bin_inst_texts():
    if not Path(last_extracted_data_path).exists():
        _save_inst_binary_info(last_extracted_data_path)
    data = _get_ctgy2bin_inst_texts_wrap()
    assert data == read_json(last_extracted_data_path)


def _save_inst_binary_info(extracted_data_path):
    data = _get_ctgy2bin_inst_texts_wrap()
    save_json(extracted_data_path, data)


def _get_ctgy2bin_inst_texts_wrap():
    raw_result = _get_ctgy2bin_inst_texts(bin_inst_rst_path)
    processed_data = {}
    for ctgy, bin_inst_texts in raw_result.items():
        processed_data[ctgy] = []
        for bin_inst_text in bin_inst_texts:
            texts = [bin_inst_text.bin_part, bin_inst_text.repr_part]
            processed_data[ctgy].append(texts)
    return processed_data


def _get_expected_attrs():
    paras = [
        {
            'name': ['unreachable', 'block', 'if', 'if', 'br', 'br_table', 'call_indirect'],
            'opcode': [[0x00], [0x02], [0x04], [0x04], [0x0C], [0x0E], [0x11]],
            'binary_info': [
                [('00', 'hex')],
                [('02', 'hex'), ('bt', 'blocktype'), ('in', 'instr', True), ('0B', 'hex')],
                [('04', 'hex'), ('bt', 'blocktype'), ('in', 'instr', True), ('0B', 'hex')],
                [('04', 'hex'), ('bt', 'blocktype'), ('in_1', 'instr', True), ('05', 'hex'), ('in_2', 'instr', True), ('0B', 'hex')],
                [('0C', 'hex'), ('l', 'labelidx')],
                [('0E', 'hex'), ('l', 'vec(labelidx)', True), ('l_N', 'labelidx')],
                [('11', 'hex'), ('y', 'typeidx'), ('x', 'tableidx')]
            ],
            'repr_info': [
                ['unreachable'],
                ['block', 'bt', 'in', 'end'],
                ['if', 'bt', 'in', 'else', '\\epsilon', 'end'],
                ['if', 'bt', 'in_1', 'else', 'in_2', 'end'],
                ['br', 'l'],
                ['br_table', 'l', 'l_N'],
                ['call_indirect', 'x', 'y']
            ]
        },
        {
            'name': ['ref.null'],
            # 'ctgy': ['Reference'],
            'opcode': [[0xD0]],
            'binary_info': [[('D0', 'hex'), ('t', 'reftype')]],
            'repr_info': [['ref.null', 't']]
        }, 
        {
            'name': ['select'],
            # 'ctgy': ['Parametric'],
            'opcode': [[0x1C]],
            'binary_info': [[('1C', 'hex'), ('t', 'vec(valtype)', True)]],
            'repr_info': [['select', 't']]

        }, 
        {
            'name': ['global.set'],
            # 'ctgy': ['Variable'],
            'opcode': [[0x24]],
            'binary_info': [[('24', 'hex'), ('x', 'globalidx')]],
            'repr_info': [['global.set', 'x']]
        }, 
        {
            'name': ['table.get', 'table.init', 'table.copy', 'table.grow'],
            # 'ctgy': ['Table', 'Table', 'Table', 'Table'],
            'opcode': [[0x25], [0xFC, 12], [0xFC, 14], [0xFC, 15]],
            'binary_info': [
                [('25', 'hex'), ('x', 'tableidx')], 
                [('FC', 'hex'), ('12', 'u32'), ('y', 'elemidx'), ('x', 'tableidx')], 
                [('FC', 'hex'), ('14', 'u32'), ('x', 'tableidx'), ('y', 'tableidx')], 
                [('FC', 'hex'), ('15', 'u32'), ('x', 'tableidx')]],
            'repr_info': [
                ['table.get', 'x'], 
                ['table.init', 'x', 'y'], 
                ['table.copy', 'x', 'y'], 
                ['table.grow', 'x']]
        }, 
        {
            'name': ['i32.load', 'i32.load8_s', 'memory.grow', 'memory.init', 'data.drop', 'memory.fill'],
            # 'ctgy': ['Memory', 'Memory', 'Memory', 'Memory', 'Memory', 'Memory'],
            'opcode': [[0x28], [0x2C], [0x40, 0x00], [0xFC, 8], [0xFC, 9], [0xFC, 11, 0x00]],
            'binary_info': [
                [('28', 'hex'), (raw_processor._process_macro('\\memarg.\\ALIGN'), 'memarg_align'), (raw_processor._process_macro('\\memarg.\\OFFSET'), 'memarg_offset')], 
                [('2C', 'hex'), (raw_processor._process_macro('\\memarg.\\ALIGN'), 'memarg_align'), (raw_processor._process_macro('\\memarg.\\OFFSET'), 'memarg_offset')], 
                [('40', 'hex'), ('00', 'hex')], 
                [('FC', 'hex'), ('8', 'u32'), ('x', 'dataidx'), ('00', 'hex')], 
                [('FC', 'hex'), ("9", 'u32'), ('x', 'dataidx')], 
                [('FC', 'hex'), ("11", 'u32'), ('00', 'hex')]],
            'repr_info': [
                ['i32.load', '\\X{memarg}.\\K{align}', '\\X{memarg}.\\K{offset}'],  # ['i32.load', 'm']
                ['i32.load8_s', '\\X{memarg}.\\K{align}', '\\X{memarg}.\\K{offset}'],  # ['i32.load8_s', 'm'] 
                ['memory.grow'], 
                ['memory.init', 'x'], 
                ['data.drop', 'x'], 
                ['memory.fill']]
        }, 
        {
            'name': ['i32.const', 'i32.ne', 'i32.gt_s', 'i32.trunc_f32_s', 'i64.trunc_sat_f64_u'],
            # 'ctgy': ['Numeric', 'Numeric', 'Numeric', 'Numeric', 'Numeric'],
            'opcode': [[0x41], [0x47], [0x4A], [0xA8], [0xFC, 7]],
            'binary_info': [
                [('41', 'hex'), ('n', 'i32')], 
                [('47', 'hex')], 
                [('4A', 'hex')], 
                [('A8', 'hex')], 
                [('FC', 'hex'), ('7', 'u32')]],
            'repr_info': [
                ['i32.const', 'n'], 
                ['i32.ne'], 
                ['i32.gt_s'], 
                ['i32.trunc_f32_s'], 
                ['i64.trunc_sat_f64_u']]
        },
        {
            'name': ['v128.load8x8_u', 'v128.load64_lane', 'v128.const', 'i8x16.shuffle'],
            'opcode': [[0xFD, 2], [0xFD, 87], [0xFD, 12], [0xFD, 13]],
            'binary_info': [
                [('FD', 'hex'), ('2', 'u32'), (raw_processor._process_macro('\\memarg.\\ALIGN'), 'memarg_align'), (raw_processor._process_macro('\\memarg.\\OFFSET'), 'memarg_offset')],
                [('FD', 'hex'), ('87', 'u32'), (raw_processor._process_macro('\\memarg.\\ALIGN'), 'memarg_align'), (raw_processor._process_macro('\\memarg.\\OFFSET'), 'memarg_offset'), ('l', 'laneidx')],
                [('FD', 'hex'), ('12', 'u32'), ('b', 'byte', False, 16)],
                [('FD', 'hex'), ('13', 'u32'), ('l', 'laneidx', False, 16)],
            ],
            'repr_info': [
                ['v128.load8x8_u', '\\X{memarg}.\\K{align}', '\\X{memarg}.\\K{offset}'],  # ['v128.load8x8_u', 'm']
                ['v128.load64_lane', '\\X{memarg}.\\K{align}', '\\X{memarg}.\\K{offset}', 'l'],  # ['v128.load64_lane', 'm', 'l']
                ['v128.const', 'bytes_i128^-1(b_0~\\dots~b_15)'],
                ['i8x16.shuffle', 'l^16']
            ]
        }
    ]

    for para_idx, para in enumerate(paras):
        bin_infos = para['binary_info']
        for bin_info_idx, bin_info in enumerate(bin_infos):
            paras[para_idx]['binary_info'][bin_info_idx] = [binEncoding(*x) for x in bin_info]

    expected_attrs = []
    keys = list(paras[0].keys())
    for para in paras:
        value_num = len(para[keys[0]])
        for i in range(value_num):
            d = {k:v[i] for k, v in para.items()}
            expected_attrs.append(d)
    return expected_attrs


# paras = [x for x in paras if x[0] == 'Variable']
bin_inst_texts = read_json('tests/testing_data/testing_data4binaryInst/to_test_binary_list.json')
expected_attrs = _get_expected_attrs()
paras = list(zip(bin_inst_texts, expected_attrs))

non_control_paras = paras[8:]
@pytest.mark.parametrize('text, expected_attrs', paras)
def test_binaryInst_on_ctgy_insts(text, expected_attrs: list):
    text = binInstText(*text)
    inst = binaryInst.from_bin_inst_text(text)
    for attr, expected_value in expected_attrs.items():
        assert getattr(inst, attr) == expected_value, print(f'attr: {attr} ; expected_value : {expected_value} ; getattr(inst, attr) : {getattr(inst, attr)}')
