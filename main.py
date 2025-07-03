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
import os
from datetime import datetime
import pygame # Added for pygame mixer
import json # Added for options persistence

script_dir = os.path.dirname(os.path.abspath(__file__))
OPTIONS_FILE = os.path.join(script_dir, 'options.json')

# Get the directory containing the script

# logger.debug(f'Current working directory: {script_dir}')

class State(Enum):
    Ready = 0
    Working = 1
    Rest = 2
    LongRest = 3


timer_dict = {'Ready': 25*60,
            'Working': 25*60,
             'Rest': 5*60,
             'LongRest': 15*60}


image_dict = {'Ready': os.path.join(script_dir, 'res/ReadyState.png'),
             'Working1': os.path.join(script_dir, 'res/Working1State.png'),
             'Rest1': os.path.join(script_dir, 'res/Rest1State.png'),
             'Working2': os.path.join(script_dir, 'res/Working2State.png'),
             'Rest2': os.path.join(script_dir, 'res/Rest2State.png'),
             'Working3': os.path.join(script_dir, 'res/Working3State.png'),
             'Rest3': os.path.join(script_dir, 'res/Rest3State.png'),
             'Working4': os.path.join(script_dir, 'res/Working4State.png'),
             'LongRest1': os.path.join(script_dir, 'res/Rest4State.png'),
             }


# global_bg = '#47b9db'  # Light Blue
global_bg = '#1e81b0'  # Darker Bl]ue
# button_bg = '#eab676'  # Tan
button_bg = '#abdbe3'  # Light Blue
# tkFont.Font(family="Helvetica",size=36,weight="bold")
button_font = ("Arial", 15, 'bold')


def configure_logger(log_level='Debug'):

    logger.remove()
    if log_level.lower == 'debug':
        logger.add(sys.stderr, level="DEBUG")
    if log_level.lower == 'trace':
        logger.add(sys.stderr, level="TRACE")
    if log_level.lower == 'info':
        logger.add(sys.stderr, level="INFO")


class Pymodoro:
    def __init__(self):
        # configure_logger(log_level='INFO')
        logger.debug('Initializing pygame')
        pygame.mixer.init() # Initialize pygame mixer
        logger.debug('Pygame initialized')
        self.root = tk.Tk()
        self.voice_active_var = tk.BooleanVar(value=True) # For the voice active checkbutton
        self.load_options() # Load options before building window
        
        # Set the Windows taskbar icon if running on Windows
        if sys.platform == 'win32':
            try:
                import ctypes
                my_app_id = 'pymodoro.timer.1.0' # arbitrary string
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)
                
                # Set window icon using the tomato image
                tomato_icon = os.path.join(script_dir, 'res/tomato.png')
                if os.path.exists(tomato_icon):
                    # Set the window icon directly using the image
                    icon = PIL.Image.open(tomato_icon)
                    photo = PIL.ImageTk.PhotoImage(icon)
                    if hasattr(photo, 'width') and hasattr(photo, 'height'):
                        self.root.iconphoto(True, photo)
            except Exception as e:
                logger.error(f"Failed to set Windows taskbar icon: {e}")
        
        self.timer_active = False
        self.state = State.Ready
        self.sec_remaining = timer_dict[self.state.name]
        self.build_window()
        self.rests = 0
        self.last_interaction = time.time()
        self.root.bind('<Key>', self.update_interaction)
        self.root.bind('<Button>', self.update_interaction)
        self.start()

    def update_interaction(self, event=None):
        self.last_interaction = time.time()

    def check_inactivity(self):
        current_hour = datetime.now().hour
        if (self.state == State.Working and
            self.timer_active and
            time.time() - self.last_interaction > 3600 and
            (current_hour < 7 or current_hour >= 16)):  # 60 minutes

            self.play_sound("are_you_still_listening") # Added voice prompt
            response = messagebox.askyesno("Still there?",
                                         "Are you still listening?")
            if response:
                self.update_interaction()
            else:
                self.reset()
                self.play_pause_media()  # Stop media playback

    def start(self):
        self.continuous_increment()
        self.root.mainloop()

    def continuous_increment(self):
        if self.timer_active:
            self.decrease()
            if self.time_remaining <= 0:
                self.transition_state()
            self.check_inactivity()

        self.root.after(1000, self.continuous_increment)

    def transition_state(self):
        if self.state == State.Ready:
            logger.debug('Transitioning to Working...')
            # For Ready -> Working, no specific sound in requirements, but play_pause_media might make a sound.
            # If a "start work" sound is desired, it would go here.
            self.play_pause_media()
            self.state = State.Working
            self.set_time_remaining()
            self.set_state_label()
            self.update_state_graphic()
            self.timer_active = True
        elif self.state == State.Working:
            logger.debug(f'Current Rest -> {self.rests}')
            if self.rests < 3:
                logger.debug('Transitioning to Rest...')
                self.play_sound("lets_take_a_quick_break") # Changed voice prompt
                self.play_pause_media()
                self.state = State.Rest
                self.set_time_remaining()
                self.set_state_label()
                self.update_state_graphic()
                self.rests += 1
            else:
                logger.debug('Transitioning to Long Rest...')
                self.play_sound("lets_take_a_longer_break") # Changed voice prompt
                self.play_pause_media()
                self.rests = 0
                self.state = State.LongRest
                self.set_time_remaining()
                self.set_state_label()
                self.update_state_graphic()
        elif self.state == State.Rest or self.state == State.LongRest:
            logger.debug('Transitioning to Working...')
            self.play_sound("lets_get_back_to_work") # Changed voice prompt
            self.play_pause_media()
            self.state = State.Working
            self.set_time_remaining()
            self.set_state_label()
            self.update_state_graphic()

    def set_time_remaining(self):
        self.time_remaining = timer_dict[self.state.name]
        self.update_timer_label()

    def set_state_label(self):
        self.state_lbl['text'] = self.state.name

    def build_window(self):
        self.root.title("Pymodoro")
        self.root.geometry("700x325")
        self.root.configure(bg=global_bg)

        self.main_frame = tk.Frame(master=self.root, bg=global_bg)
        self.main_frame.pack(fill='both', expand=False)

        self.add_state_widget(self.main_frame)
        self.add_timer_widget(self.main_frame)
        self.add_pomodoro_widget(self.main_frame)
        self.add_control_widget(self.main_frame)
        self.add_options_widget(self.main_frame)

    def rebuild_window(self):
        self.state_frame.destroy()
        self.timer_frame.destroy()
        self.pomodoro_frame.destroy()
        self.control_frame.destroy()

        self.add_state_widget(self.main_frame)
        self.add_timer_widget(self.main_frame)
        self.add_pomodoro_widget(self.main_frame)
        self.add_control_widget(self.main_frame)
        self.add_options_widget(self.main_frame)

    def add_state_widget(self, parent):
        self.state_frame = tk.Frame(master=parent, height=100, bg=global_bg, relief=tk.RAISED, borderwidth=1)
        self.state_frame.pack(fill='x', padx=5, pady=5)
        self.state_lbl = tk.Label(master=self.state_frame, text=self.state.name, padx='10', font=("Arial", 40), bg=global_bg)
        self.state_lbl.pack(anchor='center', pady='10')

    def add_timer_widget(self, parent):
        self.timer_frame = tk.Frame(master=parent, height=100, bg=global_bg)
        self.timer_frame.pack(fill='x')
        self.timer_lbl = tk.Label(master=self.timer_frame, text="00:00", padx='10', font=("Arial", 25), bg=global_bg)
        self.timer_lbl.pack(anchor='center', pady='10')

    def add_pomodoro_widget(self, parent):
        self.pomodoro_frame = tk.Frame(master=parent, height=100, bg=global_bg)
        self.pomodoro_frame.pack(fill='x')

        if self.state == State.Ready:
            im = PIL.Image.open(image_dict['Ready'])
        else:
            dict_key = f'{self.state.name}{str(self.rests + 1)}'
            im = PIL.Image.open(image_dict[dict_key])
        photo = PIL.ImageTk.PhotoImage(im)

        # canvas = tk.Canvas(master=self.pomodoro_frame, width=im.size[0], height=im.size[1])
        # canvas.pack()
        # canvas.create_image(im.size[0], im.size[1], image=photo)

        self.state_image_lbl = tk.Label(master=self.pomodoro_frame, image=photo, bg=global_bg)
        self.state_image_lbl.image = photo  # keep a reference!
        self.state_image_lbl.pack(anchor='center')

    def add_control_widget(self, parent):
        if self.state == State.Ready:
            self.control_frame = tk.Frame(master=parent, height=125, bg=global_bg)
            self.control_frame.pack(anchor='center', pady='25')

            self.go_button = tk.Button(master=self.control_frame, text='Go!', width='15', pady='5', command=self.go, bg=button_bg, font=button_font)
            self.go_button.pack(side='left', padx='5')

        else:
            self.control_frame = tk.Frame(master=parent, height=125, bg=global_bg)
            self.control_frame.pack(anchor='center', pady='25')

            self.start_stop_button = tk.Button(master=self.control_frame, text='Pause', width='15', pady='5',
                                             command=self.start_stop, bg=button_bg, font=button_font)
            self.start_stop_button.pack(side='left', padx='5')

            skip_button = tk.Button(master=self.control_frame, text='Skip', width='15', pady='5', command=self.skip, bg=button_bg, font=button_font)
            skip_button.pack(side='left', padx='5')

            reset_button = tk.Button(master=self.control_frame, text='Restart', width='15', pady='5', command=self.reset, bg=button_bg, font=button_font)
            reset_button.pack(side='left', padx='5')

    def add_options_widget(self, parent):
        self.options_frame = tk.Frame(master=parent, bg=global_bg)
        self.options_frame.pack(fill='x', side='bottom', pady=5)
        self.options_button = tk.Button(master=self.options_frame, text='⚙', width='5', pady='0', command=self.open_options_menu, bg=button_bg, font=button_font)
        self.options_button.pack(side='right', padx=10)

    def open_options_menu(self):
        options_window = tk.Toplevel(self.root)
        options_window.title("Options")
        options_window.geometry("300x200")
        options_window.configure(bg=global_bg)

        # Prevent multiple option windows
        options_window.transient(self.root) # Set to be transient to the main window
        options_window.grab_set() # Grab focus

        voice_checkbutton = tk.Checkbutton(
            options_window,
            text="Voice Active",
            variable=self.voice_active_var,
            command=self.save_options, # Save options when checkbutton state changes
            bg=global_bg,
            font=button_font, # Using button_font, can be changed if a different style is preferred
            selectcolor=button_bg, # To make the check mark background more visible if needed
            activebackground=global_bg,
            activeforeground='white', # fg when mouse is over
            fg='white' # text color
        )
        voice_checkbutton.pack(pady=20, padx=20, anchor='w')

        # Make sure the window is brought to the front and focused
        options_window.lift()
        options_window.focus_force()

        # Example: Close button for the options window
        close_button = tk.Button(
            options_window,
            text="Close",
            command=options_window.destroy,
            bg=button_bg,
            font=button_font
        )
        close_button.pack(pady=10)

    def load_options(self):
        should_save_defaults = False
        try:
            with open(OPTIONS_FILE, 'r') as f:
                options = json.load(f)
                if "voice_active" in options:
                    self.voice_active_var.set(options["voice_active"])
                    logger.info(f"Loaded 'voice_active': {options['voice_active']} from {OPTIONS_FILE}")
                else:
                    logger.info(f"'voice_active' key missing in {OPTIONS_FILE}. Using default True.")
                    self.voice_active_var.set(True)
                    should_save_defaults = True # Mark to save the file with the new default key
        except FileNotFoundError:
            logger.info(f"{OPTIONS_FILE} not found. Creating with default settings.")
            self.voice_active_var.set(True)
            should_save_defaults = True
        except json.JSONDecodeError:
            logger.warning(f"Error decoding JSON from {OPTIONS_FILE}. Using default settings and overwriting.")
            self.voice_active_var.set(True)
            should_save_defaults = True
        except Exception as e: # Catch any other unexpected error during loading
            logger.error(f"Unexpected error loading options: {e}. Using default settings.")
            self.voice_active_var.set(True)
            should_save_defaults = True

        if should_save_defaults:
            self.save_options()


    def save_options(self):
        options_to_save = {
            "voice_active": self.voice_active_var.get()
        }
        try:
            with open(OPTIONS_FILE, 'w') as f:
                json.dump(options_to_save, f, indent=4)
            logger.info(f"Saved options to {OPTIONS_FILE}")
        except IOError as e:
            logger.error(f"Error saving options to {OPTIONS_FILE}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving options: {e}")


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
        self.timer_lbl['text'] = f'{self.format_time_value()}'

    def update_state_graphic(self):

        dict_key = f'{self.state.name}{str(self.rests+1)}'
        im = PIL.Image.open(image_dict[dict_key])

        logger.debug(f'Updating state graphic to {image_dict[dict_key]}')
        photo = PIL.ImageTk.PhotoImage(im)
        self.state_image_lbl.configure(image=photo)
        self.state_image_lbl.image = photo  # keep a reference!
        # self.state_image_lbl.pack(anchor='center')

    def start_stop(self):
        if self.timer_active:
            self.timer_active = False
            self.start_stop_button['text'] = 'Start'
            self.state_lbl['text'] = f'{self.state.name} - Paused'
        else:
            self.timer_active = True
            self.start_stop_button['text'] = 'Pause'
            self.set_state_label()

    def increase(self):
        self.time_remaining += 1
        self.update_timer_label()

    def decrease(self):
        logger.trace('Decrementing timer...')
        self.time_remaining -= 1
        self.update_timer_label()

    def format_time_value(self):
        secconds = self.time_remaining % 60
        mininutes = math.floor(self.time_remaining / 60)
        logger.trace(f'Timer value: {mininutes:0>2}:{secconds:0>2}')
        return f'{mininutes:0>2}:{secconds:0>2}'

    def play_sound(self, sound_name):
        """Plays a sound from the res directory using pygame.mixer."""
        if not self.voice_active_var.get():
            logger.debug("Voice Active is False, skipping sound.")
            return
        try:
            path = os.path.join(script_dir, 'res', f"{sound_name}.mp3")
            if not os.path.exists(path):
                logger.warning(f"Audio file not found: {path}")
                return
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            logger.debug(f"Playing sound: {path}")
        except pygame.error as e:
            logger.error(f"Could not play sound {sound_name}. Pygame error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while trying to play sound {sound_name}: {e}")


if __name__ == '__main__':
    pymo = Pymodoro()
