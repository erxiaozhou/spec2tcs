from .raw_processor import process_char_bracket_fmt
import re
from math import log2, ceil


def custom_isdigit(s):
    for c in s:
        if c not in [str(i) for i in range(10)] + ['*']:
            return False
    return True


def find_all_vals(s):
    # 1. assumption: there exist spaces between variables and symbols
    # 2. assumption: each string represents a variable or symbol
    s = re.sub(r' +', ' ', s)
    sgs = ['+', '*', '-', '/', '<=', '>=', '==', '>', '<', '^']
    substrs = s.split(' ')
    r = [sp for sp in substrs if sp not in sgs]
    r = [sp for sp in r if not custom_isdigit(sp)]
    return r


def process_dim(s):
    if '\\dim' in s:
        def func(s_):
            s_ = s_.group(0)
            p = r'^.*x(.*)\)$'
            r = re.compile(p).findall(s_)
            if r:
                return r[0]
            else:
                return s_
        s = re.sub(r'\\dim\(.+?\)', func, s)
    else:
        s_no_bracket = process_char_bracket_fmt(s)
        p = r'dim\([a-z]\d+x(\d+)\)'
        r = re.compile(p).findall(s_no_bracket)
        if r:
            s = re.sub(p, r[0], s_no_bracket)
    return s


def process_condition_text(s):
    s = s.replace('\\cdot ', ' * ')
    s = s.replace(' \\leq ', '<=')
    for sg in ['+', '*', '-', '/', '<=', '>=']:
        s = s.replace(sg, sg.join((' ', ' ')))
    s = s.replace('2^{32}', '2**32')
    s = process_power(s)
    s = s.replace(' ^ ', ' ** ')
    s = s.replace(' = ', ' == ')
    s = process_dim(s)
    s = re.sub(r' +', ' ', s).strip(' ')
    return s

def process_power(s):
    p = r'(?:(?<=^)|(?<=\s))(\d+)(\^) *\{([^ ]*)\}'
    p = re.compile(p)
    if p.search(s):
        s = p.sub(lambda m: f'{m.group(1)} {m.group(2)} {m.group(3)}', s)
    return s

def process_power_eqieq(s):
    # possible_cmp_sgs = ['<', '<=', '>', '>=', '==']
    num_p = r'(?:\d+)|(?:0[xX][a-zA-Z\d]+)'
    p = f'({num_p}) \*\* (.*) ([<=>]=?) (.*)'
    print(p)
    p = re.compile(p)
    print('========', s)
    r = p.findall(s)
    if r:
        r = r[0]
        n1_str, sybl, cmp_str, n2_str = r
        n1 = _get_int(n1_str)
        try:
            n2 = eval(n2_str)
        except:
            return s
        rval = log2(n2) / log2(n1)
        assert rval == int(rval)
        s = f'{sybl} {cmp_str} {int(rval)}'
        return s
    else:
        return s

def _get_int(s):
    if s.startswith('0x') or s.startswith('0X'):
        return int(s, 16)
    else:
        return int(s)
