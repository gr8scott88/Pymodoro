import tkinter as tk
from tkinter import messagebox
import time
import pyautogui
from loguru import logger
import math
from enum import Enum
import PIL.Image
import PIL.ImageTk
import sys


class State(Enum):
    Ready = 0
    Working = 1
    Rest = 2
    LongRest = 3


timerdict = {'Ready': 25*60,
            'Working': 25*60,
             'Rest': 5*60,
             'LongRest': 15*60}


# timerdict = {'Ready': 5,
#              'Working': 5,
#              'Rest': 3,
#              'LongRest': 10}

imagedict = {'Ready': 'res/ReadyState.png',
             'Working1': 'res/Working1State.png',
             'Rest1': 'res/Rest1State.png',
             'Working2': 'res/Working2State.png',
             'Rest2': 'res/Rest2State.png',
             'Working3': 'res/Working3State.png',
             'Rest3': 'res/Rest3State.png',
             'Working4': 'res/Working4State.png',
             'LongRest1': 'res/Rest4State.png',
             }


# globalbg = '#47b9db'  # Light Blue
globalbg = '#1e81b0'  # Darker Bl]ue
# buttonbg = '#eab676'  # Tan
buttonbg = '#abdbe3'  # Light Blue
# tkFont.Font(family="Helvetica",size=36,weight="bold")
buttonfont = ("Arial", 15, 'bold')


def configure_logger(loglevel='Debug'):

    logger.remove()
    if loglevel.lower == 'debug':
        logger.add(sys.stderr, level="DEBUG")
    if loglevel.lower == 'trace':
        logger.add(sys.stderr, level="TRACE")
    if loglevel.lower == 'info':
        logger.add(sys.stderr, level="INFO")


class Pymodoro:
    def __init__(self):
        configure_logger(loglevel='INFO')
        self.root = tk.Tk()
        self.timer_active = False
        self.state = State.Ready
        self.sec_remaining = timerdict[self.state.name]
        self.build_window()
        self.rests = 0
        self.start()

    def start(self):
        self.continuous_increment()
        self.root.mainloop()

    def continuous_increment(self):
        if self.timer_active:
            self.decrease()
            if self.time_remaining <= 0:
                self.transition_state()

        self.root.after(1000, self.continuous_increment)

    def transition_state(self):
        if self.state == State.Ready:
            logger.debug('Transitioning to Working...')
            self.play_pause_media()
            self.state = State.Working
            self.set_time_remaining()
            self.set_state_label()
            self.update_state_graphic()
            self.timer_active = True
        elif self.state == State.Working:
            if self.rests < 3:
                logger.debug('Transitioning to Rest...')
                self.play_pause_media()
                self.state = State.Rest
                self.set_time_remaining()
                self.set_state_label()
                self.update_state_graphic()
                self.rests += 1
            else:
                logger.debug('Transitioning to Long Rest...')
                self.play_pause_media()
                self.rests = 0
                self.state = State.LongRest
                self.set_time_remaining()
                self.set_state_label()
                self.update_state_graphic()
        elif self.state == State.Rest or self.state == State.LongRest:
            logger.debug('Transitioning to Working...')
            self.play_pause_media()
            self.state = State.Working
            self.set_time_remaining()
            self.set_state_label()
            self.update_state_graphic()

    def set_time_remaining(self):
        self.time_remaining = timerdict[self.state.name]
        self.update_timer_label()

    def set_state_label(self):
        self.statelbl['text'] = self.state.name

    def build_window(self):
        self.root.title("Pymodoro")
        self.root.geometry("700x325")
        self.root.configure(bg=globalbg)

        self.mainframe = tk.Frame(master=self.root, bg=globalbg)
        self.mainframe.pack(fill='both', expand=False)

        self.add_state_widget(self.mainframe)
        self.add_timer_widget(self.mainframe)
        self.add_pomodoro_widget(self.mainframe)
        self.add_control_widget(self.mainframe)

    def rebuild_window(self):
        self.stateframe.destroy()
        self.timerframe.destroy()
        self.pomodoroframe.destroy()
        self.controlframe.destroy()

        self.add_state_widget(self.mainframe)
        self.add_timer_widget(self.mainframe)
        self.add_pomodoro_widget(self.mainframe)
        self.add_control_widget(self.mainframe)

    def add_state_widget(self, parent):
        self.stateframe = tk.Frame(master=parent, height=100, bg=globalbg, relief=tk.RAISED, borderwidth=1)
        self.stateframe.pack(fill='x', padx=5, pady=5)
        self.statelbl = tk.Label(master=self.stateframe, text=self.state.name, padx='10', font=("Arial", 40), bg=globalbg)
        self.statelbl.pack(anchor='center', pady='10')

    def add_timer_widget(self, parent):
        self.timerframe = tk.Frame(master=parent, height=100, bg=globalbg)
        self.timerframe.pack(fill='x')
        self.timerlbl = tk.Label(master=self.timerframe, text="00:00", padx='10', font=("Arial", 25), bg=globalbg)
        self.timerlbl.pack(anchor='center', pady='10')

    def add_pomodoro_widget(self, parent):
        self.pomodoroframe = tk.Frame(master=parent, height=100, bg=globalbg)
        self.pomodoroframe.pack(fill='x')

        if self.state == State.Ready:
            im = PIL.Image.open(imagedict['Ready'])
        else:
            dictkey = f'{self.state.name}{str(self.rests + 1)}'
            im = PIL.Image.open(imagedict[dictkey])
        photo = PIL.ImageTk.PhotoImage(im)

        # canvas = tk.Canvas(master=self.pomodoroframe, width=im.size[0], height=im.size[1])
        # canvas.pack()
        # canvas.create_image(im.size[0], im.size[1], image=photo)

        self.stateimagelbl = tk.Label(master=self.pomodoroframe, image=photo, bg=globalbg)
        self.stateimagelbl.image = photo  # keep a reference!
        self.stateimagelbl.pack(anchor='center')

    def add_control_widget(self, parent):
        if self.state == State.Ready:
            self.controlframe = tk.Frame(master=parent, height=125, bg=globalbg)
            self.controlframe.pack(anchor='center', pady='25')

            self.gobutton = tk.Button(master=self.controlframe, text='Go!', width='15', pady='5', command=self.go, bg=buttonbg, font=buttonfont)
            self.gobutton.pack(side='left', padx='5')

        else:
            self.controlframe = tk.Frame(master=parent, height=125, bg=globalbg)
            self.controlframe.pack(anchor='center', pady='25')

            self.startstopbutton = tk.Button(master=self.controlframe, text='Pause', width='15', pady='5',
                                             command=self.start_stop, bg=buttonbg, font=buttonfont)
            self.startstopbutton.pack(side='left', padx='5')

            skipbutton = tk.Button(master=self.controlframe, text='Skip', width='15', pady='5', command=self.skip, bg=buttonbg, font=buttonfont)
            skipbutton.pack(side='left', padx='5')

            resetbutton = tk.Button(master=self.controlframe, text='Restart', width='15', pady='5', command=self.reset, bg=buttonbg, font=buttonfont)
            resetbutton.pack(side='left', padx='5')

    def play_pause_media(self):
        pyautogui.press("playpause")

    def go(self):
        self.transition_state()
        self.rebuild_window()
        self.set_time_remaining()

    def skip(self):
        self.transition_state()

    def reset(self):
        self.state = State.Ready
        self.rests = 0
        self.rebuild_window()
        self.set_time_remaining()
        self.set_state_label()
        self.timer_active = False

    def update_timer_label(self):
        self.timerlbl['text'] = f'{self.format_time_value()}'

    def update_state_graphic(self):

        dictkey = f'{self.state.name}{str(self.rests+1)}'
        im = PIL.Image.open(imagedict[dictkey])

        logger.debug(f'Updating state graphic to {imagedict[dictkey]}')
        photo = PIL.ImageTk.PhotoImage(im)
        self.stateimagelbl.configure(image=photo)
        self.stateimagelbl.image = photo  # keep a reference!
        # self.stateimagelbl.pack(anchor='center')

    def start_stop(self):
        if self.timer_active:
            self.timer_active = False
            self.startstopbutton['text'] = 'Start'
            self.statelbl['text'] = f'{self.state.name} - Paused'
        else:
            self.timer_active = True
            self.startstopbutton['text'] = 'Pause'
            self.set_state_label()

    def increase(self):
        self.time_remaining += 1
        self.update_timer_label()

    def decrease(self):
        logger.debug('Decrementing timer...')
        self.time_remaining -= 1
        self.update_timer_label()

    def format_time_value(self):
        secconds = self.time_remaining % 60
        mininutes = math.floor(self.time_remaining / 60)
        logger.debug(f'Timer value: {mininutes:0>2}:{secconds:0>2}')
        return f'{mininutes:0>2}:{secconds:0>2}'


if __name__ == '__main__':
    pymo = Pymodoro()
