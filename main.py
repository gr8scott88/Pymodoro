import tkinter as tk
from tkinter import messagebox
import time
import pyautogui
from loguru import logger
import math
from enum import Enum


class State(Enum):
    Ready = 0
    Working = 1
    Rest = 2
    LongRest = 3


# timerdict = {'Working': 25*60,
#              'Rest': 5*60,
#              'LongRest': 15*60}

timerdict = {'Ready': 5,
             'Working': 5,
             'Rest': 3,
             'LongRest': 10}


def configure_logger(loglevel='Debug'):
    pass


class Pymodoro:
    def __init__(self):
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
            self.timer_active = True
        elif self.state == State.Working:
            if self.rests < 3:
                logger.debug('Transitioning to Rest...')
                self.play_pause_media()
                self.rests += 1
                self.state = State.Rest
                self.set_time_remaining()
                self.set_state_label()
            else:
                logger.debug('Transitioning to Long Rest...')
                self.play_pause_media()
                self.rests = 0
                self.state = State.LongRest
                self.set_time_remaining()
                self.set_state_label()
        elif self.state == State.Rest or self.state == State.LongRest:
            logger.debug('Transitioning to Working...')
            self.play_pause_media()
            self.state = State.Working
            self.set_time_remaining()
            self.set_state_label()

    def set_time_remaining(self):
        self.time_remaining = timerdict[self.state.name]
        self.update_timer_label()

    def set_state_label(self):
        self.statelbl['text'] = self.state.name

    def build_window(self):
        self.root.title("Pymodoro")
        self.root.geometry("600x300")

        self.mainframe = tk.Frame(master=self.root, bg='green')
        self.mainframe.pack(fill='both', expand=False)

        self.add_state_widget(self.mainframe)
        self.add_timer_widget(self.mainframe)
        self.add_pomodoro_widget(self.mainframe)
        self.add_control_widget(self.mainframe)

    def reuild_window(self):
        self.stateframe.destroy()
        self.timerframe.destroy()
        self.pomodoroframe.destroy()
        self.controlframe.destroy()

        self.add_state_widget(self.mainframe)
        self.add_timer_widget(self.mainframe)
        self.add_pomodoro_widget(self.mainframe)
        self.add_control_widget(self.mainframe)

    def add_state_widget(self, parent):
        self.stateframe = tk.Frame(master=parent, height=100, bg='red')
        self.stateframe.pack(fill='x')
        self.statelbl = tk.Label(master=self.stateframe, text=self.state.name, padx='10', font=("Arial", 40))
        self.statelbl.pack(anchor='center', pady='10')

    def add_timer_widget(self, parent):
        self.timerframe = tk.Frame(master=parent, height=100, bg='yellow')
        self.timerframe.pack(fill='x')
        self.timerlbl = tk.Label(master=self.timerframe, text="00:00", padx='10', font=("Arial", 25))
        self.timerlbl.pack(anchor='center', pady='10')

    def add_pomodoro_widget(self, parent):
        self.pomodoroframe = tk.Frame(master=parent, height=100, bg='purple')
        self.pomodoroframe.pack(fill='x')

    def add_control_widget(self, parent):
        if self.state == State.Ready:
            self.controlframe = tk.Frame(master=parent, height=100, bg='blue')
            self.controlframe.pack(anchor='center', pady='10')

            self.gobutton = tk.Button(master=self.controlframe, text='Go!', width='25', pady='5', command=self.go)
            self.gobutton.pack(side='left', padx='10')

        else:
            self.controlframe = tk.Frame(master=parent, height=100, bg='blue')
            self.controlframe.pack(anchor='center', pady='10')

            self.startstopbutton = tk.Button(master=self.controlframe, text='Pause', width='25', pady='5',
                                             command=self.start_stop)
            self.startstopbutton.pack(side='left', padx='10')

            skipbutton = tk.Button(master=self.controlframe, text='Skip', width='25', pady='5', command=self.skip)
            skipbutton.pack(side='left', padx='10')

            resetbutton = tk.Button(master=self.controlframe, text='Reset', width='25', pady='5', command=self.reset)
            resetbutton.pack(side='left', padx='10')

    def play_pause_media(self):
        pyautogui.press("playpause")

    def go(self):
        self.transition_state()
        self.reuild_window()

    def skip(self):
        self.transition_state()

    def reset(self):
        self.set_time_remaining()

    def update_timer_label(self):
        self.timerlbl['text'] = f'{self.format_time_value()}'

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
    pymo = Pymodoro



