import traceback
import os
import sys
from custom_logger import CustomLogger
current_path, filename = os.path.split(os.path.abspath(__file__))
from basic import Basic
logger = CustomLogger(filename).logger
logger.info(f'before start,current python sys.path is {sys.path}')

def no_window_run(key:str,venv_path=None,no_venv=False):
    if key is None:
        key = 'pythonw'
    else:
        key = 'python'
    if venv_path is None:
        if no_venv is False:
            venv_path = 'c:/d_file/python_projection/ai/venv/Scripts'
            os.system(f'cd /d {venv_path} && activate && {key} {os.path.join(current_path, "basic.py")}')
        else:
            os.system(f'{key} {os.path.join(current_path, "basic.py")}')

def window_run(venv_path=None,no_venv=False):
    no_window_run(key='python -u', venv_path=venv_path,no_venv=no_venv)

def no_venv_win_run():
    window_run(venv_path=None, no_venv=True)

def win_lanuch_from_start():
    from win32com.shell import shell, shellcon
    start_up_path = shell.SHGetPathFromIDList(
        shell.SHGetSpecialFolderLocation(0, shellcon.CSIDL_STARTUP))
    start_up_path = str(start_up_path, encoding='utf-8')
    logger.info(start_up_path)

try:
    logger.info('this is window mode')
    # no_venv_win_run()
    Basic().schedule_task()
except Exception:
    logger.info(traceback.format_exc())
    input()