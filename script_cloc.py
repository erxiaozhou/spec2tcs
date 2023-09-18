import subprocess
from pathlib import Path


def exec_cmd(e_dir, e_ext):
    e_dir_txt = ','.join(e_dir)
    e_ext_txt = ','.join(e_ext)
    cmd = 'cloc --exclude-dir={} --exclude-ext={} .'.format(e_dir_txt, e_ext_txt)
    subprocess.run(cmd, shell=True)
    return cmd

exculde_dir = [
    'content_dir', 'tt', 'about_operation_lines', 'tt.py', 'generated_tcs', 'for_test', 'tmp_result', 'wasms_test', 'spec_coverage_calculator', 'tests', 'check_ori_tcs_executable.py', 'save_something', 'script_detect_opcode_isdefined.py', '.git', 'script_cloc.py', 'test_se_inst.py', 'extracted_raw', 'inst_info_log', 'pd_type_paras', 'get_Values_from_exec_insts.py', 'get_value_condition_from_steps_for_analysis.py', 'file_util.py'
]
'''
cloc  --exclude-dir=
tt,save_something,for_test,about_operation_lines,
script_detect_opcode_isdefined.py,
check_ori_tcs_executable.py,generated_tcs,.git .
'''
exclude_ext = ['wasm', 'wat', 'json']

# tmp_*.py
tmp_fnames = [f.name for f in Path('.').glob('tmp_*.py')]
save_fnames = [f.name for f in Path('.').glob('save*.py')]
see_fnames = [f.name for f in Path('.').glob('see*.py')]
script_fnames = [f.name for f in Path('.').glob('script*.py')]
test_fnames = [f.name for f in Path('.').glob('test*.py')]
expended_exclude_dir = exculde_dir + tmp_fnames + save_fnames + script_fnames + test_fnames


if __name__ == '__main__':
    exec_cmd(expended_exclude_dir, exclude_ext)
