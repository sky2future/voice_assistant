import pyttsx3
from queue import Queue
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

    # say_voice_to_file('gougshi 狗屎')

    def engine_stop(self):
        self._engine.stop()

    def __enter__(self):
        return self

    def __exit__(self, exec_type, exec_value, traceback):
        self.engine_stop()
        if exec_type is not None:
            return False