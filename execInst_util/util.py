from .execInsts import execInsts
from file_util import check_dir, save_json

def save_exec_insts_to_dir(insts, dir_name):
    assert isinstance(insts, execInsts)
    dir_ = check_dir(dir_name, True)
    for inst in insts:
        path = str(dir_ / '.'.join((inst.name, 'json')))
        save_json(path, inst.as_data())


def save_to_file(insts, file_path):
    assert isinstance(insts, execInsts)
    data = []
    for inst in insts:
        data[inst.name] = inst.as_data()
    save_json(file_path, data)
