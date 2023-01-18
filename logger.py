import logging
from logging.handlers import RotatingFileHandler
class Logger:
    def __init__(self,log_name:str, is_same_file=True) -> None:
        self._logger = logging.getLogger(log_name)
        level = logging.DEBUG
        self._logger.setLevel(level=level)
        self._deafult_file_name = 'default.log'

        if is_same_file:
            filename=self._deafult_file_name
        else:
            filename=f'{log_name}.log'
        self._file_handler = RotatingFileHandler(filename=filename,
                                maxBytes=1024*1024*40,
                                backupCount=4)
        self._file_handler.setLevel(level=level)
        self._formatter = logging.Formatter(
                            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self._file_handler.setFormatter(self._formatter)
        self._logger.addHandler(self._file_handler)

        self._console_handler = logging.StreamHandler()
        self._console_handler.setLevel(level=level)
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
