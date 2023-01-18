import threading
import time
from logger import Logger
from datetime import datetime
from voice import Pyttsx3Engine
from class_decorator import single_class

@single_class
class Time(object):
    _wake_up = [8,30]
    _breakfast = _wake_up
    _lunch = [12,10]
    _dinner = [18,0]
    _sleep_at_night = [23,30]
    _drink_watter_duration = 3600*2
    
    @property
    def drink_watter_duration(self):
        return self._drink_watter_duration

    def is_work_time(self, hour:int, minute:int)->bool:
        if self._wake_up[0]<hour <self._sleep_at_night[0]:
            return True
        elif self._wake_up[0]==hour and self._wake_up[1]<= minute:
            return True
        elif self._sleep_at_night[0] == hour and self._sleep_at_night[1] >= minute:
            return True
        else:
            return False

class Basic:    
    def __init__(self) -> None:
        self._logger_instance = Logger(__name__)
        self._logger = self._logger_instance.logger
        self._all_schedule = []

    def schedule_task(self):
        # pc will lanuch every time_duration
        drink_watter = threading.Thread(target=DrinkWatter()._2h_drik_water)
        self._logger.info(f'drink_watter:current time is {datetime.now()}')
        drink_watter.start()
        self._all_schedule.append(drink_watter)

class DrinkWatter:
    def __init__(self) -> None:
        self._logger_instance = Logger(self.__class__.__name__)
        self._logger = self._logger_instance.logger
        self._time = Time()
        self._drink_watter_duration = self._time.drink_watter_duration

    def _2h_drik_water(self):
        while True:
            with Pyttsx3Engine() as speaker:
                speaker.say(f'current time is {str(datetime.now()).split(".")[0]}, start 2h!')
            self._logger.info(f'lanuch time is {datetime.now()}')
            time.sleep(self._drink_watter_duration)
            self._logger.info(f'end time is {datetime.now}')
            if self._check_time():
                with Pyttsx3Engine() as speaker:
                    speaker.say(f'current time is {str(datetime.now()).split(".")[0]}, end 2h!')
    
    def _check_time(self):
        current_time = datetime.now()
        return self._time.is_work_time(current_time.hour, current_time.minute)        

if __name__ == '__main__':
    Basic().schedule_task()