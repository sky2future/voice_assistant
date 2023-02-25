import pyttsx3
from queue import Queue, Empty
from custom_logger import CustomLogger
import threading
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError, URLError
import json
from pprint import pprint
import speech_recognition as sr
from speech_recognition import AudioSource, WaitTimeoutError,AudioData, RequestError, UnknownValueError


class Pyttsx3Engine:
    def __init__(self):
        self._engine = pyttsx3.init()
        is_run_queue = Queue(maxsize=10)
        # rate = self._engine.getProperty('rate')
        # print(rate)
        self._engine.setProperty('rate', 200)

        # volume = self._engine.getProperty('volume')
        # print(volume)
        self._engine.setProperty('volume', 1)
        self._engine.setProperty('voice', 'zh')

    def say(self, texts: str = 'test'):
        self._engine.say(texts)
        self._engine.runAndWait()

    def say_txt_to_file(self, text, filepath=None):
        if filepath is None:
            filepath = './data/audio/engine_saved_file.mp3'
        if isinstance(text, str):
            self._engine.save_to_file(text, filepath)
            self._engine.runAndWait()
        else:
            raise TypeError

    def engine_stop(self):
        self._engine.stop()

    def __enter__(self):
        return self

    def __exit__(self, exec_type, exec_value, traceback):
        self.engine_stop()
        if exec_type is not None:
            return False


class BackListenRecognizer(sr.Recognizer):
    def listen_in_background(self, source, callback, phrase_time_limit=None):
        assert isinstance(source, AudioSource), "Source must be an audio source"
        running = [True]

        def threaded_listen():
            with source as s:
                self.adjust_for_ambient_noise(s)
                while running[0]:
                    try:  # listen for 1 second, then check again if the stop function has been called
                        audio = self.listen(source=s, phrase_time_limit=10)
                    except WaitTimeoutError:  # listening timed out, just try again
                        pass
                    else:
                        if running[0]: callback(self, audio)

        def stopper(wait_for_stop=True):
            running[0] = False
            if wait_for_stop:
                listener_thread.join()  # block until the background thread is done, which can take around 1 second

        listener_thread = threading.Thread(target=threaded_listen)
        listener_thread.daemon = True
        listener_thread.start()
        return stopper

    def recognize_google(self, audio_data, key=None, language="en-US", pfilter=0, show_all=False, with_confidence=False):
        assert isinstance(audio_data, AudioData), "``audio_data`` must be audio data"
        assert key is None or isinstance(key, str), "``key`` must be ``None`` or a string"
        assert isinstance(language, str), "``language`` must be a string"

        flac_data = audio_data.get_flac_data(
            convert_rate=None if audio_data.sample_rate >= 8000 else 8000,  # audio samples must be at least 8 kHz
            convert_width=2  # audio samples must be 16-bit
        )
        if key is None: key = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
        url = "http://www.google.com/speech-api/v2/recognize?{}".format(urlencode({
            "client": "chromium",
            "lang": language,
            "key": key,
            "pFilter": pfilter
        }))
        request = Request(url, data=flac_data, headers={"Content-Type": "audio/x-flac; rate={}".format(audio_data.sample_rate)})

        # obtain audio transcription results
        try:
            response = urlopen(request, timeout=self.operation_timeout)
        except HTTPError as e:
            raise RequestError("recognition request failed: {}".format(e.reason))
        except URLError as e:
            raise RequestError("recognition connection failed: {}".format(e.reason))
        response_text = response.read().decode("utf-8")
        # print('response_text:')
        # pprint(response_text, indent=4)

        # ignore any blank blocks
        actual_result = []
        for line in response_text.split("\n"):
            if not line: continue
            result = json.loads(line)["result"]            
            # print('result1:')
            # pprint(result, indent=4)
            if len(result) != 0:
                actual_result = result[0]
                break

        # return results
        if show_all:
            return actual_result
        print('result2:')
        pprint(actual_result, indent=4)
        if not isinstance(actual_result, dict) or len(actual_result.get("alternative", [])) == 0: raise UnknownValueError()

        if "confidence" in actual_result["alternative"]:
            # return alternative with highest confidence score
            best_hypothesis = max(actual_result["alternative"], key=lambda alternative: alternative["confidence"])
        else:
            # when there is no confidence available, we arbitrarily choose the first hypothesis.
            best_hypothesis = actual_result["alternative"][0]
        if "transcript" not in best_hypothesis: raise UnknownValueError()
        # https://cloud.google.com/speech-to-text/docs/basics#confidence-values
        # "Your code should not require the confidence field as it is not guaranteed to be accurate, or even set, in any of the results."
        confidence = best_hypothesis.get("confidence", 0.5)
        if with_confidence:
            return best_hypothesis["transcript"], confidence
        return best_hypothesis["transcript"]

class VoiceInteraction:
    def __init__(self) -> None:
        self._r = BackListenRecognizer()
        self._m = sr.Microphone()
        self._logger_instance = CustomLogger(self.__class__.__name__)
        self._logger = self._logger_instance.logger

    def recognize(self, audio:AudioData):
        return self._r.recognize_google(audio_data=audio,
                                        show_all=True,
                                        language='cmn-Hans-CN')

    def listen(self, all_result=False):
        with self._m as source:
            self._r.adjust_for_ambient_noise(source=source)
            while True:
                audio = self._r.listen(source)
                try:
                    self._logger.info('get audio date')
                    result=self.recognize(audio=audio)
                    self._logger.info(f'result is {result}')
                    if all_result:
                        if len(result)!=0:
                            result = result['alternative'][0]['transcript'] 
                        else:
                            result = ''
                        yield result
                    elif len(result)!=0:
                        yield result['alternative'][0]['transcript']  
                except sr.UnknownValueError:
                    self._logger.exception('sr.UnknownValueError')
                except sr.RequestError:
                    self._logger.exception('sr.RequestError')
        

class VoiceInteractionAsync(VoiceInteraction):
    def __init__(self) -> None:
        super(VoiceInteractionAsync, self).__init__()
        self._init()

    def _init(self):
        self._stop_background_listen = None
        self._audio_queue=Queue(maxsize=44)
        self._result_queue=Queue(maxsize=44)
        self._time = 1

    def listen(self):
        with self._m as source:
            self._r.adjust_for_ambient_noise(source=source)
        self._stop_background_listen = self._r.listen_in_background(self._m, self._listen_callback)
        threading.Thread(target=self._recognize,daemon=True).start()

    def clear_queue(self):
        self.stop_background_listen()
        self._init()

    def _listen_callback(self, self_, audio):
        self._audio_queue.put(audio)
    
    def _recognize(self):
        while True:
            audio = self._audio_queue.get()
            try:
                self._logger.info(f'{self._time},has get audio')
                result=self.recognize(audio=audio)
                self._logger.info(f'{self._time},result is {str(result)}')
                self._time += 1
                self._put_result(result=result)
            except sr.UnknownValueError:
                self._logger.exception('sr.UnknownValueError')
            except sr.RequestError:
                self._logger.exception('sr.RequestError')

    def _put_result(self, result):
        if len(result)!=0:
            self._result_queue.put(result['alternative'][0]['transcript'])

    def get_recognize_result(self, timeout=None)->str:
        try:
            result=self._result_queue.get(timeout=timeout)
        except Empty:
            self._logger.error('Empty')
            result = None
        return result

    def __enter__(self):
        return self

    def __exit__(self, exec_type, exec_value, traceback):
        self.stop_background_listen()
        if exec_type is not None:
            return False

    def is_listen(self)->bool:
        if self._stop_background_listen is None:
            return False
        return True
    
    def stop_background_listen(self):
        if self._stop_background_listen is not None:
            self._stop_background_listen(wait_for_stop=False)

class VoiceAsynSphinx(VoiceInteractionAsync):
    def recognize(self, audio: AudioData):
        return self._r.recognize_sphinx(audio_data=audio,
                                        language='zh-CN')

    def _put_result(self, result):
        self._result_queue.put(result)


if __name__ == '__main__':
    # voice=VoiceInteraction()
    # while True:
    #     result=next(voice.listen())
    #     print(result)
    with VoiceInteractionAsync() as voice:
        voice.listen()
        while True:
            print(voice.get_recognize_result())