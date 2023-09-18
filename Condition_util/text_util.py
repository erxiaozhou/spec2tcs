import re


def relation_str2sg(relation_str):
    s2sg = {
        r'^smaller(?: than)?$': '<',
        r'^larger(?: than)?$': '>',
        r'^the same as$': '=='
    }
    s2sg = {re.compile(k): v for k, v in s2sg.items()}
    matched_result = None
    for k, v in s2sg.items():
        if k.findall(relation_str):
            matched_result = v
    assert matched_result is not None, print(relation_str)
    return matched_result
