import re


def is_int_number(content):
    p = r'^[0-9]{1,3}$'
    if re.search(p, content):
        return True
    else:
        return False


def is_hex_number(content):
    p = r'^[0-9A-F]{1,2}$'
    if re.search(p, content):
        return True
    else:
        return False


def s_match_p(s, p):
    if re.search(p, s):
        return True
    else:
        return False
