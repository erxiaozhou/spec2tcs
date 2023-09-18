from .combine_inst_info import get_exec_insts_possible_names
from .combine_inst_info import get_valid_insts_possible_names
from combinedInst_util import combinedInst
from extract_binary_inst import binaryInst
from extract_binary_inst import binaryInsts
from file_util import check_dir
from .get_processed_production_info import get_sorted_production_list
from process_text import process_str
from copy import deepcopy
from extract_binary_inst import parsed_result2str


class combinedInsts(list):
    def __init__(self, insts):
        super().__init__(insts)
        self.sorted_production_list = get_sorted_production_list()
        self.name2index_dict = {}
        for i, inst in enumerate(self):
            self.name2index_dict[inst.name] = i
        self.infer_paras()

    def infer_paras(self):
        for inst in self:
            assert isinstance(inst, combinedInst)
            inst.init_exec_title_paras(self.sorted_production_list)

    def get_inst_by_inst_name(self, name):
        return self[self.name2index_dict[name]]

    def save_to_dir(self, dir_name):
        dir_ = check_dir(dir_name, True)
        for inst in self:
            inst.save(path=f'{dir_}/{inst.name}.json')

    @classmethod
    def get_combined_insts(cls):
        combined_exec_info = get_exec_insts_possible_names(debug=True)
        name_to_exec_inst_dict = _get_name_to_exec_inst_dict(combined_exec_info)
        combined_valid_info = get_valid_insts_possible_names(debug=True)
        name_to_valid_inst_dict = _get_name_to_exec_inst_dict(combined_valid_info)
        bin_insts = binaryInsts.from_raw_rst_path()
        visited_names = set()
        combined_insts = []
        for bin_inst in bin_insts:
            assert isinstance(bin_inst, binaryInst)
            name = bin_inst.name
            if name not in visited_names:
                visited_names.add(name)
            else:
                name = _get_name_with_binInst_info(bin_inst)
            cur_combined_inst = combinedInst(
                bin_inst, 
                deepcopy(name_to_valid_inst_dict[bin_inst.name]),
                deepcopy(name_to_exec_inst_dict[bin_inst.name]), 
                name=name)
            combined_insts.append(cur_combined_inst)

        return cls(combined_insts)


def _get_name_to_exec_inst_dict(combined_info_list):
    result = {}
    for exec_inst, inst_names in combined_info_list:
        for name in inst_names:
            result[process_str(name, True).split('~')[0]] = exec_inst
    return result


def _get_name_with_binInst_info(inst: binaryInst):
    name = inst.name
    additional_info = parsed_result2str(inst.binary_info)
    return f'{name}_{additional_info}'
