import threading
import time
from typing import Callable,List,Dict,Union,Optional
import queue
import functools
import os
import sys

_current_dir = os.path.dirname(__file__)
if _current_dir not in sys.path:
    sys.path.append(os.path.join(_current_dir, 'face_rec'))

from custom_logger import CustomLogger, LoggerFilter
from datetime import datetime
from voice import Pyttsx3Engine
from class_decorator import single_class
from voice import VoiceInteractionAsync
from face_rec.webcam_rec_face import get_vedio_result,release_webcam_resource


@single_class
class Time(object):
    _wake_up = [8,30]
    _breakfast = _wake_up
    _lunch = [12,10]
    _dinner = [18,0]
    _sleep_at_night = [23,30]
    _drink_watter_duration = 3600*2
    _current_drink_watter_time = _drink_watter_duration

    _max_hour = 24
    _an_hour_minute = 60

    _all_observers:List[Callable] = []
    
    @property
    def drink_watter_duration(self):
        return self._current_drink_watter_time

    def calculate_duration(self, hour:int, minute:int,_flag=True)->int:
        if _flag:
            self._current_drink_watter_time = self._drink_watter_duration
        elif hour>=self._sleep_at_night[0] :
            self._current_drink_watter_time = (self._max_hour - hour + self._wake_up[0])*self._an_hour_minute \
                                                - (minute - self._wake_up[1])
            self._current_drink_watter_time *= self._an_hour_minute
        elif hour <= self._wake_up[0]:
            self._current_drink_watter_time = (self._wake_up[0]-hour)*self._an_hour_minute \
                                                - (minute - self._wake_up[1])
            self._current_drink_watter_time *= self._an_hour_minute

        if self._current_drink_watter_time == 0:
            self._current_drink_watter_time = self._an_hour_minute**2

        return self._current_drink_watter_time

    def is_work_time(self, hour:int, minute:int)->bool:
        if self._wake_up[0]<hour <self._sleep_at_night[0]:
            self.calculate_duration(hour=hour,
                                    minute=minute)
            return True
        elif self._wake_up[0]==hour and self._wake_up[1]<= minute:
            self.calculate_duration(hour=hour,
                                    minute=minute)
            return True
        elif self._sleep_at_night[0] == hour and self._sleep_at_night[1] >= minute:
            self.calculate_duration(hour=hour,
                                    minute=minute)
            return True
        else:
            self.calculate_duration(hour=hour,
                                    minute=minute,
                                    _flag=False)
            return False

    def add_observer(self, watcher:Callable)->None:
        self._all_observers.append(watcher)

    def send_msg(self, msg:str):
        for one in self._all_observers:
            pass


class LoopSTHBase:
    def __init__(self) -> None:
        self._logger_instance = LoggerFilter(self.__class__.__name__)
        self._logger = self._logger_instance.logger
        self._max_size = 3
        self._queue = queue.Queue(maxsize=self._max_size)

    def send_msg(self, msg:str)->bool:
        try:        
            self._queue.put_nowait(msg)
            return True
        except queue.Full:
            self._logger.exception(f'current queue size is {self._max_size}.'
                                    f'it not statisfic current situtation')
            return False                                

    def get_msg(self, right_now=True) -> Union[str, bool]:
        if right_now:
            try:
                return self._queue.get_nowait()
            except queue.Empty:
                return True
        else:
            return self._queue.get()


class Basic(LoopSTHBase):    
    def __init__(self) -> None:
        super(Basic,self).__init__()
        self._all_schedule:Dict[Callable,List[threading.Thread]] = {}

    def schedule_task(self):
        # pc will lanuch every time_duration
        drink_watter_object = DrinkWatter()
        drink_watter = threading.Thread(target=drink_watter_object.twoh_drik_water)
        self._logger.info(f'drink_watter:current time is {datetime.now()}')
        drink_watter.start()
        self._all_schedule.update({DrinkWatter:[drink_watter_object,drink_watter]})

    def deal_loop_msg(self,loopbase:LoopSTHBase):
        """todo"""
        while True:
            if loopbase.get_msg():
                self._all_schedule[loopbase][0].join()

    def get_schedule(self, class_name:Callable)->Optional[Callable]:
        result = self._all_schedule.get(class_name)
        if result is not None:
            return result[0]
        else:
            return None

class DrinkWatter(LoopSTHBase):
    def __init__(self) -> None:
        super(DrinkWatter, self).__init__()
        self._time = Time()
        self._drink_watter_duration = self._time.drink_watter_duration
        self._listen_thread = None
        self._sleeping = True
        self._listening = False
        self._is_end = self._sleeping
        self._wait_timeout = 3
        self._speak_thread_flag = True
        self._is_end_queue = queue.Queue()
        self._is_check_person_time_gap = 60*5
        self._vedio_thread = None

    @property
    def is_end(self):
        try:
            self._is_end = self._is_end_queue.get_nowait()
        except queue.Empty:
            pass
        return self._is_end

    def save_is_end(self, is_end:bool):
        self._is_end_queue.put(is_end)

    def _clear_queue(self):
        del self._is_end_queue
        self._is_end_queue = queue.Queue()

    def twoh_drik_water(self):
        with Pyttsx3Engine() as speaker:
            speaker.say(f'current time is {str(datetime.now()).split(".")[0]}, start 2h!')
            self._logger.info(f'lanuch time is {datetime.now()}')
            while True:
                self.ui_interative(msg=self._sleeping)
                while True:
                    if self.need_sleep():
                        break
                self._logger.info(f'end time is {datetime.now()}')
                if self.check_time():
                    self.ui_interative(msg=self._listening)

                    self._is_end = self._listening

                    self._speak_thread_flag = True
                    threading.Thread(target=self.end_speaker_thread,daemon=True).start()
                    start_time = time.time()
                    self._logger.info(f'start time is {start_time}')
                    
                    while not self.is_end:
                        speaker.say(f'current time is {str(datetime.now()).split(".")[0]}, end 2h!'
                                        'please you drink watter')
                        end_time = time.time()
                        self.check_is_vedio_detective(start=start_time, end=end_time)

                    if self._listen_thread is not None:
                        self._speak_thread_flag = False
                        self._clear_queue()

                        self._listen_thread.stop_background_listen()
                        self._listen_thread.clear_queue()

                    if self._vedio_thread is not None:
                        self._vedio_thread = None
                        release_webcam_resource()
                else:
                    self._logger.info(f'current time is {str(datetime.now()).split(".")[0]},not speak!')
    
    def ui_interative(self,msg:bool):
        self.send_msg(msg=msg)

    def need_sleep(self)->bool:
        """true means the sleep time is change.otherwise not"""
        self._logger.info(f'sleep time is {self._time.drink_watter_duration}')
        return split_sleep(s_time=self._time.drink_watter_duration)(self.get_msg)()

    def end_speaker_thread(self):
        while self._speak_thread_flag:
            try:
                if self.end_speaker():
                    self.save_is_end(is_end=self._sleeping)
            except AssertionError:
                self._logger.exception(msg='speech recognition need 1 seconde to stop thread')
                time.sleep(1)
    
    def end_speaker(self)->bool:
        if self._listen_thread is None:
            self._listen_thread = VoiceInteractionAsync()
        if not self._listen_thread.is_listen():
            self._listen_thread.listen()
        try:
            result = self._listen_thread.get_recognize_result(timeout=self._wait_timeout)
        except Exception:
            self._logger.exception('exception')
            return False
        return self.check_result(result=result)

        # self._logger.info(f'start listen time is {datetime.now()}')
        # voice = VoiceInteraction()
        # result = voice.listen(all_result=True)
        # for i in range(3):
        #     if self._check_result(next(result)):
        #         self._logger.info(f'end listen time is {datetime.now()}')
        #         return True
        #     else:
        #         self._logger.info(f'listen {i}, current time is {datetime.now()}')
        # self._logger.info(f'end listen time is {datetime.now()}')
        # return False

    def check_result(self, result)->bool:
        self._logger.info(f'result is {result}', 
                            extra={self._logger_instance.recognize_key:True})
        if result is None:
            return False
        else:
            for one in ['end','stop', '结束','喝水']:
                if one in result:
                    return True
            return False

    def check_time(self):
        current_time = datetime.now()
        return self._time.is_work_time(current_time.hour, current_time.minute)  

    def check_is_vedio_detective(self,start:float,end:float):
        if end - start >= self._is_check_person_time_gap:
            if self._vedio_thread is None:
                self._vedio_thread = threading.Thread(target=self.check_vedio_person, daemon=True)
                self._vedio_thread.start()

    def check_vedio_person(self):
        result = get_vedio_result()
        self.save_is_end(is_end=result)


def split_sleep(s_time:int, duration=3):
    """s_time unit is second"""
    def work(func:Callable):
        @functools.wraps(func)
        def _work(*arg, **kwargs)->Union[str, bool]:
            if s_time > duration:
                for i in range(0, int(s_time/duration)):
                    time.sleep(duration)
                    if not func(*arg, **kwargs):
                        return False
                rest_time = s_time - (i+1)*duration
                if rest_time > 0:
                    time.sleep(rest_time)
            else:
                time.sleep(s_time)
            return func(*arg, **kwargs)
        return _work
    return work

if __name__ == '__main__':
    Basic().schedule_task()