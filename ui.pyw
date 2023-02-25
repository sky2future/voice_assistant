import tkinter
import tkinter.messagebox
import threading
import time
import pystray 
import PIL.Image 
import os

from basic import Basic,DrinkWatter

_multi_lock = threading.RLock()


class UI:
    def __init__(self) -> None:
        self._basic = Basic()
        self._drink_watter_instanse:DrinkWatter = None
        
        threading.Thread(target=self._basic.schedule_task,
                        daemon=True).start()
        threading.Thread(target=self.ui_interactive,
                        daemon=True).start()                        
        
        self._root = tkinter.Tk()

        self.set_button()

        self._root.protocol('WM_DELETE_WINDOW',self.shrink_win_to_tray)

        self._root.mainloop()

    def shrink_win_to_tray(self):
        pic_path = os.path.join( os.path.dirname(__file__),"liuyifei.jpg")
        self._root.withdraw()
        if os.path.exists(pic_path):
            image=PIL.Image.open(pic_path)
        else:
            image = None
        menu=(pystray.MenuItem('Quit', self.quit_window), 
                pystray.MenuItem('Show', self.show_window))
        icon=pystray.Icon("name", image, "My System Tray Icon", menu)
        icon.run()

    def quit_window(self, icon, item):
        icon.stop()
        self._root.destroy()

    def show_window(self,icon, item):
        icon.stop()
        self._root.after(0,self._root.deiconify())

    def set_button(self):
        self._button_start_text = 'start time for drink watter'
        self._button_start_bg = 'white'
        self._button_timing_text = 'timing for drink watter'
        self._button_timing_bg = 'red'
        self._button_not_end_time = 'now not to time for drink watter'

        self._button = tkinter.Button(text=self._button_timing_text,
                                        command=self.button_event,
                                        bg=self._button_timing_bg)
        self._button.pack()

    def button_event(self):
        if self._drink_watter_instanse is None:
            self._drink_watter_instanse = self._basic.get_schedule(class_name=DrinkWatter)
            if self._drink_watter_instanse is None:
                error = 'drink watter instanse is None'
                tkinter.messagebox.showerror(title=error,message=error);
                return

        if not self._drink_watter_instanse.is_end:
            self._drink_watter_instanse.save_is_end(is_end=True)
            self.change_button_style(color=self._button_start_bg,
                                    text=self._button_start_text)
        else:
            tkinter.messagebox.showinfo(title=self._button_not_end_time,
                                        message=self._button_not_end_time)

    def change_button_style(self, color:str, text:str):
        with _multi_lock:
            self._button['bg'] = color 
            self._button['text'] = text

    def ui_interactive(self):
        while True:
            if self._drink_watter_instanse is None:
                self._drink_watter_instanse = self._basic.get_schedule(class_name=DrinkWatter)
                if self._drink_watter_instanse is None:
                    time.sleep(1)
                    continue

            result = self._drink_watter_instanse.get_msg(right_now=False) 
            if result:
                self.change_button_style(color=self._button_timing_bg,
                                        text=self._button_timing_text)
            else:
                self.change_button_style(color=self._button_start_bg,
                                        text=self._button_start_text)
                

if __name__ == '__main__':
    UI()