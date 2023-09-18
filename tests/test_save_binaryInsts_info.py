from extract_binary_inst import binaryInsts


def test_binaryInsts_save_info():
    insts = binaryInsts.from_raw_rst_path()
    insts.save_brief_info('./tests/generated_data/binInsts.json')
