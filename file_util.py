import os
import json
import time
from pathlib import Path
import struct
import logging


def check_dir(path, mkdir=True):
    if not isinstance(path, Path):
        path = Path(path)
    if mkdir:
        parent_path = path.parent
        if not parent_path.exists():
            check_dir(parent_path)
        if not path.exists():
            path.mkdir()
        return path
    return path.exists()


def read_json(path):
    if isinstance(path, str):
        path = Path(path)
    data = json.load(path.open(encoding="utf8"))
    return data


def save_json(path, data):
    if isinstance(path, str):
        path = Path(path)
    json.dump(data,
              path.open("w", encoding="utf8"),
              ensure_ascii=False,
              indent=4)


def write_bytes(path, byte_seq):
    path = str(path)
    with open(path, 'wb') as fwriter:
        fwriter.write(byte_seq)


def path_write(path, content):
    if isinstance(path, str):
        path = Path(path)
    with path.open('w', encoding='utf8') as f:
        f.write(content)


def path_read(path):
    if isinstance(path, str):
        path = Path(path)
    with path.open('r', encoding='utf8') as f:
        content = f.read()
    return content


def rm_dir(dir):
    os.system("rm -rf {}".format(dir))


def get_time_string():
    return time.strftime('%m-%d-%H-%M-%S', time.localtime())


def group_ps(ps, just_search=True):
    wrap_fmt = '(?:{})'
    if just_search:
        grouped_fmt = '(?:{})'
    else:
        grouped_fmt = '({})'
    raw_combined = '|'.join(wrap_fmt.format(p) for p in ps)
    grouped_p = grouped_fmt.format(raw_combined)
    return grouped_p


def print_ba(ba):
    ba = bytearray(ba)
    print([hex(x) for x in ba])


def uint2bytes(val, int_byte_num):
    # int_byte_num: 4, 8, ...
    return bytearray(int.to_bytes(val, int_byte_num,
              byteorder='little', signed=False))


def bytes2f32(bs):
    return struct.unpack('=f', bs)


def bytes2f64(bs):
    return struct.unpack('=d', bs)

def get_logger(logger_name, log_file_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel('DEBUG')
    file = logging.FileHandler(log_file_name, mode='w', encoding='utf8')
    fmt = logging.Formatter(
        fmt="%(levelname)-9s - %(filename)-8s : %(lineno)s line - %(message)s")
    file.setFormatter(fmt)
    logger.addHandler(file)
    return logger
