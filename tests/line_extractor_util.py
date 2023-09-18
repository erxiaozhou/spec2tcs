from functools import partial
from Step_util import line_extractor
from file_util import path_read, read_json
from pathlib import Path
import re
from process_text import unwrap_math
from Step_util.line_extractor import _ps


def _read_target_lines(target):
    base_dir = Path('./content_dir')
    lines = path_read(base_dir / target).split('\n')
    return lines


def _count_not_empty_result(func_to_test, lines):
    match_mun = 0
    for line in lines:
        if func_to_test(line=line):
            match_mun += 1
    return match_mun


def get_all_lines():
    lines = []
    content_dir = Path('./tests/testing_data/content_dir')
    for path in content_dir.glob('*'):
        lines.extend(path.read_text().split('\n'))
    lines = set(line for line in lines if line)
    return lines


def extract_data_by_p(p_name):
    lines = get_all_lines()
    results = set()
    for line in lines:
        r = _ps[p_name].findall(line)
        if r:
            results.add(r[0])
    return results


def get_gt_data_for_p_name(p_name):
    p = 'tests/testing_data/testingdata_for_line_extractor.json'
    gt_data = read_json(p)[p_name]
    gt_data_set = set()
    for item in gt_data:
        if isinstance(item, list):
            gt_data_set.add(tuple(item))
        elif isinstance(item, str):
            gt_data_set.add(item)
        else:
            raise Exception(f'wrong type: {item}')
    return gt_data_set


def get_processed_unique_lines():
    unique_lines = path_read('./tests/testing_data/unique_lines').split('\n')
    lines = [re.sub(r' *\* ', '', line) for line in unique_lines]
    return lines
