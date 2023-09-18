def get_template(mode):
    mode2template = {
        'non_v128': template_nonv128,
        'nonv128_empty': template_nonv128_empty,
        'template_nonv128_add_data_count': template_nonv128_add_data_count
    }
    assert mode in mode2template
    return mode2template[mode]


template_nonv128 = {
    'global_len': 12,
    'local_len': 4,
    'mem_num': 1,
    'mem_lens': [1],
    'table_num': 1,
    'table_lens': [10],
    'func_num':3,

    'elem_num': 3,  
    'elem_lens': [5, 4, 1],
    'data_num': 3,
    'data_lens': [8, 9, 9],
    'template_path': './wat_templates/hw_z2_without_v128_v2.wat',
    'global_type' : ['i32', 'i32', 'f32', 'f32', 'i64', 'i64', 'f64', 'f64', 'i32', 'f32', 'i64', 'f64'],
    'local_type' : ['i32', 'f32', 'i64', 'f64'],
    'add_data_count' : False
}


template_nonv128_add_data_count = {
    'global_len': 12,
    'local_len': 4,
    'mem_num': 1,
    'mem_lens': [1],
    'table_num': 1,
    'table_lens': [10],
    'func_num':3,

    'elem_num': 3,  
    'elem_lens': [5, 4, 1],
    'data_num': 3,
    'data_lens': [8, 9, 9],
    'template_path': './wat_templates/hw_z2_without_v128_v2.wat',
    'global_type' : ['i32', 'i32', 'f32', 'f32', 'i64', 'i64', 'f64', 'f64', 'i32', 'f32', 'i64', 'f64'],
    'local_type' : ['i32', 'f32', 'i64', 'f64'],
    'add_data_count' : True
}


template_nonv128_empty = {
    'global_len': 0,
    'local_len': 0,
    'mem_num': 0,
    'table_num': 0,
    'func_num':0,
    'mem_lens': [],
    'elem_lens': [],
    'data_lens': [],

    'elem_num': 0,
    'data_num': 0,
    'template_path': './wat_templates/hw_z2_without_v128_empty.wat', 
    'add_data_count' : False
}
