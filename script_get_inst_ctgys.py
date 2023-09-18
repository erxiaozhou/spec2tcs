from combinedInst_util import combinedInsts
from combinedInst_util import combinedInst
from file_util import save_json

d = {}
insts = combinedInsts.get_combined_insts()
for inst in insts:
    assert isinstance(inst, combinedInst)
    name = inst.name
    ctgy = inst.ctgy
    if name.startswith('v128.'):
        ctgy = 'Vector'
    if ctgy not in d:
        d[ctgy] = []

    d[ctgy].append(name)
save_json('inst2ctgys.json', d)