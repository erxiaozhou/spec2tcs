import time
from pathlib import Path
from file_util import check_dir, save_json, read_json, path_write
from .execConfig import execConfig


class generationResult:
    def __init__(self, config, result_save_base_dir) -> None:
        assert isinstance(config, generationConfig)
        self.result_save_base_dir = check_dir(result_save_base_dir)
        self.config = config
        self.failed_inst_names = []
        self.ok_inst_names = []
        self.start_time = None
        self.end_time = None
        self.num_log = {}

    def init_start_testing_time(self):
        self.start_time = time.time()

    def init_end_testing_time(self):
        self.end_time = time.time()

    def save(self):
        self._save_failed_inst_names()
        self._save_ok_inst_names()
        self._save_num_log()
        self._save_config()
        self._write_time()

    def _save_failed_inst_names(self):
        path = self.result_save_base_dir / 'failed_inst_names.json'
        save_json(path, self.failed_inst_names)

    def _save_ok_inst_names(self):
        path = self.result_save_base_dir / 'ok_inst_names.json'
        save_json(path, self.ok_inst_names)

    def _save_config(self):
        config_path =  self.result_save_base_dir / 'config.json'
        self.config.save_as_json(config_path)

    def _save_num_log(self):
        save_json(self._get_num_log_path, self.num_log)

    @property
    def _get_num_log_path(self):
        return self.result_save_base_dir / 'num_log.json'

    def _write_time(self):
        path = self.result_save_base_dir / 'time.txt'
        path_write(path, repr(self.end_time - self.start_time))


class generationConfig:
    def __init__(self, exec_config, 
                 base_dir, 
                 todolist_path=None, 
                 remove_existing=True, 
                 save_meta_data=False,
                 template_strategy=None,
                 solution_num=5,
                 skip_generation=False,
                 detect_spec_cov_exec=False) -> None:
        self.exec_config = exec_config
        self.base_dir = check_dir(base_dir)
        self.todolist_path = todolist_path
        self.remove_existing = remove_existing
        self.save_meta_data = save_meta_data
        self.template_strategy = template_strategy
        self.solution_num = solution_num
        self.skip_generation = skip_generation
        self.detect_spec_cov_exec = detect_spec_cov_exec

    @property
    def log_dir(self):
        return self.base_dir / 'log'

    @property
    def tcs_dir(self):
        return self.base_dir / 'tcs'

    @property
    def only_exec_todo_list(self):
        return self.todolist_path is not None

    @classmethod
    def from_json(cls, json_path):
        data = read_json(json_path)

        exec_config_para = data.get('exec_condig_para')
        assert exec_config_para is not None
        assert isinstance(exec_config_para, dict)
        exec_config = execConfig.from_dict(exec_config_para)

        paras = {
            'exec_config': exec_config,
            'base_dir': data['base_dir'],
            'todolist_path': data.get('todolist_path'),
            'remove_existing': data['remove_existing'],
            'save_meta_data': data['save_meta_data'],
            'template_strategy': int(data['template_strategy']),
            'solution_num': int(data['solution_num']),
            'skip_generation': data.get('skip_generation', False),
            'detect_spec_cov_exec': data.get('detect_spec_cov_exec', False)
        }
        return cls(**paras)

    def save_as_json(self, json_path):
        raw_dict = self.__dict__
        data = {}
        for name, attr in raw_dict.items():
            if isinstance(attr, execConfig):
                data[name] = attr.to_dict()
            elif isinstance(attr, Path):
                data[name] = str(attr)
            else:
                data[name] = attr
        save_json(json_path, data)
