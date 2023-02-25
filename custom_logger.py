import logging
from logging.handlers import RotatingFileHandler
import os

class CustomLogger:
    def __init__(self,log_name:str, is_same_file=True) -> None:
        self._logger = logging.getLogger(log_name)
        self._level = logging.DEBUG
        self._logger.setLevel(level=self._level)
        self._abs_log_dir_path = os.path.split(os.path.abspath(__file__))[0]
        self._deafult_file_name = 'default.log'
        self._deafult_file_path = os.path.join(self._abs_log_dir_path, self._deafult_file_name)
        if is_same_file:
            filename=self._deafult_file_path
        else:
            filename=os.path.join(self._abs_log_dir_path, f'{log_name}.log')
        self._file_handler = RotatingFileHandler(filename=filename,
                                maxBytes=1024*1024*40,
                                backupCount=4,
                                encoding='utf-8')
        self._file_handler.setLevel(level=self._level)
        self._formatter = logging.Formatter(
                            '%(asctime)s - %(name)s - %(levelname)s - line %(lineno)d - %(message)s')
        self._file_handler.setFormatter(self._formatter)
        self._logger.addHandler(self._file_handler)

        self._console_handler = logging.StreamHandler()
        self._console_handler.setLevel(level=self._level)
        self._console_handler.setFormatter(self._formatter)
        self._logger.addHandler(self._console_handler)

    @property
    def logger(self):
        return self._logger
    
    @property
    def deafult_file_name(self):
        return self._deafult_file_name

    @property
    def file_handler(self)->RotatingFileHandler:
        return self._file_handler

    @property
    def formatter(self):
        return self._formatter
    
    @property
    def console_handler(self):
        return self.console_handler

class FilterMsg(logging.Filter):
    _recognize = 'recognize'
    _filter_keys = list(map(lambda x:'result is '+x, ['', '[]', 'None']))
    def filter(self, record: logging.LogRecord) -> bool:
        extra = record.__dict__.get(self._recognize)
        if extra is not None:
            msg = record.msg
            if msg in self._filter_keys:
                return False
            else:
                return True
        else:
            return False

    @property
    def recognize_key(self)->str:
        return self._recognize

class LoggerFilter(CustomLogger):
    def __init__(self, log_name: str, is_same_file=True) -> None:
        super().__init__(log_name, is_same_file)
        
        if is_same_file:
            filename = os.path.join(self._abs_log_dir_path, 
                                    'filter_' + self._deafult_file_name)
        else:
            filename = os.path.join(self._abs_log_dir_path, 
                                    'filter_' + log_name + '.log')

        self._filter_handle = RotatingFileHandler(filename=filename,
                                                    maxBytes=1024*1024*40,
                                                    backupCount=4,
                                                    encoding='utf-8')
        self._filter_handle.setFormatter(self._formatter)
        self._filter_handle.setLevel(self._level)

        self._filter = FilterMsg(log_name)
        self._filter_handle.addFilter(self._filter)
        self._logger.addHandler(self._filter_handle)

    @property
    def filter_handle(self):
        return self._filter_handle

    @property
    def recognize_key(self)->str:
        return self._filter.recognize_key
