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
from ui_utils import create_rounded_button_image # Added for rounded buttons

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
        # Default window geometry
        self.window_geometry = {"width": 700, "height": 325, "x": None, "y": None}
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
        self.root.protocol("WM_DELETE_WINDOW", self.on_close) # Handle window close event
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

        # Apply loaded or default geometry
        width = self.window_geometry["width"]
        height = self.window_geometry["height"]
        x = self.window_geometry["x"]
        y = self.window_geometry["y"]

        if x is not None and y is not None:
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        else:
            # Fallback to centering if position is not set (e.g., first run)
            self.root.geometry(f"{width}x{height}")
            self.root.update_idletasks() # Ensure window is drawn before centering
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            center_x = int(screen_width/2 - width / 2)
            center_y = int(screen_height/2 - height / 2)
            self.root.geometry(f"{width}x{height}+{center_x}+{center_y}")

        self.root.configure(bg=global_bg)

        self.main_frame = tk.Frame(master=self.root, bg=global_bg)
        self.main_frame.pack(fill='both', expand=False)

        self.add_state_widget(self.main_frame)      # Creates self.state_frame
        self.add_options_widget(self.state_frame)   # Places options_button in self.state_frame
        self.add_timer_widget(self.main_frame)
        self.add_pomodoro_widget(self.main_frame)
        self.add_control_widget(self.main_frame)
        # self.add_options_widget(self.main_frame) # Old call, no longer needed here

    def rebuild_window(self):
        # Destroy frames. Since options_button is a child of state_frame,
        # destroying state_frame will handle the options_button.
        if hasattr(self, 'control_frame') and self.control_frame.winfo_exists():
            self.control_frame.destroy()
        if hasattr(self, 'pomodoro_frame') and self.pomodoro_frame.winfo_exists():
            self.pomodoro_frame.destroy()
        if hasattr(self, 'timer_frame') and self.timer_frame.winfo_exists():
            self.timer_frame.destroy()
        if hasattr(self, 'state_frame') and self.state_frame.winfo_exists():
            self.state_frame.destroy()
            # self.options_button is child of state_frame, so it's gone too.

        # Re-create UI elements in correct order
        self.add_state_widget(self.main_frame)      # Recreates self.state_frame
        self.add_options_widget(self.state_frame)   # Re-places options_button in new self.state_frame
        self.add_timer_widget(self.main_frame)
        self.add_pomodoro_widget(self.main_frame)
        self.add_control_widget(self.main_frame)
        # self.add_options_widget(self.main_frame) # Old call

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
        self.control_frame = tk.Frame(master=parent, height=125, bg=global_bg)
        self.control_frame.pack(anchor='center', pady='25')

        # Define standard dimensions and style for control buttons
        btn_width_px = 207  # Increased by another 50% from 138
        btn_height_px = 69  # Increased by another 50% from 46
        corner_radius_px = 5 # Keeping radius, could also scale if desired
        font_name_str, font_size_int, font_weight_str = button_font # Font size might need adjustment later
        text_color_str = '#000000' # Black text for light blue button

        if self.state == State.Ready:
            # Go Button
            self.go_button_img = create_rounded_button_image(
                text='Go!', width=btn_width_px, height=btn_height_px, corner_radius=corner_radius_px,
                bg_color=button_bg, text_color=text_color_str, font_name=font_name_str,
                font_size=font_size_int, font_weight=font_weight_str
            )
            self.go_button = tk.Button(master=self.control_frame, image=self.go_button_img,
                                       command=self.go, borderwidth=0, relief=tk.FLAT, bg=global_bg)
            self.go_button.image = self.go_button_img # Keep reference
            self.go_button.pack(side='left', padx='5')
        else:
            # Pause/Start Button
            current_text = 'Pause' if self.timer_active else 'Start'
            self.start_stop_button_img = create_rounded_button_image(
                text=current_text, width=btn_width_px, height=btn_height_px, corner_radius=corner_radius_px,
                bg_color=button_bg, text_color=text_color_str, font_name=font_name_str,
                font_size=font_size_int, font_weight=font_weight_str
            )
            self.start_stop_button = tk.Button(master=self.control_frame, image=self.start_stop_button_img,
                                             command=self.start_stop, borderwidth=0, relief=tk.FLAT, bg=global_bg)
            self.start_stop_button.image = self.start_stop_button_img # Keep reference
            self.start_stop_button.pack(side='left', padx='5')

            # Skip Button
            self.skip_button_img = create_rounded_button_image(
                text='Skip', width=btn_width_px, height=btn_height_px, corner_radius=corner_radius_px,
                bg_color=button_bg, text_color=text_color_str, font_name=font_name_str,
                font_size=font_size_int, font_weight=font_weight_str
            )
            self.skip_button = tk.Button(master=self.control_frame, image=self.skip_button_img,
                                        command=self.skip, borderwidth=0, relief=tk.FLAT, bg=global_bg)
            self.skip_button.image = self.skip_button_img # Keep reference
            self.skip_button.pack(side='left', padx='5')

            # Reset Button (Restart)
            self.reset_button_img = create_rounded_button_image(
                text='Restart', width=btn_width_px, height=btn_height_px, corner_radius=corner_radius_px,
                bg_color=button_bg, text_color=text_color_str, font_name=font_name_str,
                font_size=font_size_int, font_weight=font_weight_str
            )
            self.reset_button = tk.Button(master=self.control_frame, image=self.reset_button_img,
                                         command=self.reset, borderwidth=0, relief=tk.FLAT, bg=global_bg)
            self.reset_button.image = self.reset_button_img # Keep reference
            self.reset_button.pack(side='left', padx='5')

    def add_options_widget(self, state_frame_as_master):
        options_btn_size_px = 53 # Increased by 50% from 35 (52.5 -> 53)
        options_font_size = 25   # Increased from 15 to better fit larger button
        corner_radius_px = 5
        font_name_str, _, font_weight_str = button_font # Use bold from global button_font
        text_color_str = '#000000'

        self.options_button_img = create_rounded_button_image(
            text='⚙', width=options_btn_size_px, height=options_btn_size_px, corner_radius=corner_radius_px,
            bg_color=button_bg, text_color=text_color_str, font_name=font_name_str, # Arial
            font_size=options_font_size, font_weight=font_weight_str # Bold
        )
        self.options_button = tk.Button(
            master=state_frame_as_master,
            image=self.options_button_img,
            command=self.open_options_menu,
            borderwidth=0,
            relief=tk.FLAT,
            bg=global_bg # Match parent frame for seamless look if image has transparency
        )
        self.options_button.image = self.options_button_img # Keep reference
        # Place the button on the right side, vertically centered, with some padding from the edge.
        # Using relx=1.0 and anchor='ne' (top-right) or 'e' (east/center-right)
        # Let's try anchor='ne' and then adjust with x, y padding.
        # x is pixels from the right edge (negative moves left), y is pixels from top edge.
        self.options_button.place(relx=1.0, rely=0.0, x=-5, y=5, anchor='ne')


    def open_options_menu(self):
        options_window = tk.Toplevel(self.root)
        options_window.title("Options")
        # options_window.geometry("300x200") # Initial size, position will be set below
        options_window.configure(bg=global_bg)

        # Calculate position relative to the main window
        self.root.update_idletasks() # Ensure main window geometry is up to date
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()

        popup_width = 300
        popup_height = 200 # Default height, can be adjusted by content later if needed

        # Center the popup window relative to the main window
        popup_x = main_x + (main_width // 2) - (popup_width // 2)
        popup_y = main_y + (main_height // 2) - (popup_height // 2)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        if popup_x < 0: popup_x = 0
        if popup_y < 0: popup_y = 0
        if popup_x + popup_width > screen_width: popup_x = screen_width - popup_width
        if popup_y + popup_height > screen_height: popup_y = screen_height - popup_height

        options_window.geometry(f"{popup_width}x{popup_height}+{int(popup_x)}+{int(popup_y)}")

        # Prevent multiple option windows
        options_window.transient(self.root) # Set to be transient to the main window
        options_window.grab_set() # Grab focus

        # Import the ToggleSwitch class
        from toggle_switch import ToggleSwitch

        # Define a font for the label next to the toggle switch
        toggle_label_font = ("Arial", 16)

        # Create a frame to hold the label and the toggle switch for better alignment
        voice_option_frame = tk.Frame(options_window, bg=global_bg)
        # Pack it to fill x to allow centering of its content if window is wider,
        # or just pack normally if a fixed width for options_window is always used.
        # Given popup_width is fixed at 300, fill='x' is good.
        voice_option_frame.pack(pady=20, padx=20, fill='x')


        voice_label = tk.Label(
            voice_option_frame,
            text="Voice Active:",
            bg=global_bg,
            font=toggle_label_font,
            fg='white'
        )
        voice_label.pack(side=tk.LEFT, padx=(0, 10))

        # Instantiate the ToggleSwitch
        voice_toggle = ToggleSwitch(
            voice_option_frame,
            variable=self.voice_active_var,
            command=self.save_options,
            width=44,
            height=22
        )
        voice_toggle.pack(side=tk.LEFT)

        # Make sure the window is brought to the front and focused
        options_window.lift()
        options_window.focus_force()

        # Example: Close button for the options window
        btn_width_px = 173  # Increased by 50% from 115 (172.5 -> 173)
        btn_height_px = 60  # Increased by 50% from 40
        corner_radius_px = 5
        font_name_str, font_size_int, font_weight_str = button_font # Font size might need adjustment
        text_color_str = '#000000'

        self.options_close_button_img = create_rounded_button_image(
            text="Close", width=btn_width_px, height=btn_height_px, corner_radius=corner_radius_px,
            bg_color=button_bg, text_color=text_color_str, font_name=font_name_str,
            font_size=font_size_int, font_weight=font_weight_str
        )
        close_button = tk.Button(
            options_window,
            image=self.options_close_button_img,
            command=options_window.destroy,
            borderwidth=0,
            relief=tk.FLAT,
            bg=global_bg # Match parent for seamless look
        )
        close_button.image = self.options_close_button_img # Keep reference
        close_button.pack(pady=10)

    def load_options(self):
        should_save_defaults = False
        try:
            with open(OPTIONS_FILE, 'r') as f:
                options = json.load(f)

                # Load voice_active option
                if "voice_active" in options:
                    self.voice_active_var.set(options["voice_active"])
                    logger.info(f"Loaded 'voice_active': {options['voice_active']} from {OPTIONS_FILE}")
                else:
                    logger.info(f"'voice_active' key missing in {OPTIONS_FILE}. Using default True.")
                    self.voice_active_var.set(True) # Default value
                    should_save_defaults = True

                # Load window geometry
                self.window_geometry["width"] = options.get("window_width", self.window_geometry["width"])
                self.window_geometry["height"] = options.get("window_height", self.window_geometry["height"])
                self.window_geometry["x"] = options.get("window_x", self.window_geometry["x"])
                self.window_geometry["y"] = options.get("window_y", self.window_geometry["y"])
                if any(key not in options for key in ["window_width", "window_height", "window_x", "window_y"]):
                    logger.info("One or more window geometry keys missing. Will use defaults and save them.")
                    should_save_defaults = True
                else:
                    logger.info(f"Loaded window geometry: {self.window_geometry} from {OPTIONS_FILE}")

        except FileNotFoundError:
            logger.info(f"{OPTIONS_FILE} not found. Creating with default settings for all options.")
            # Set defaults for all options explicitly here
            self.voice_active_var.set(True)
            # self.window_geometry remains as its initialized defaults
            should_save_defaults = True
        except json.JSONDecodeError:
            logger.warning(f"Error decoding JSON from {OPTIONS_FILE}. Using default settings for all options and overwriting.")
            self.voice_active_var.set(True)
            # self.window_geometry remains as its initialized defaults
            should_save_defaults = True
        except Exception as e: # Catch any other unexpected error during loading
            logger.error(f"Unexpected error loading options: {e}. Using default settings for all options.")
            self.voice_active_var.set(True)
            # self.window_geometry remains as its initialized defaults
            should_save_defaults = True

        if should_save_defaults:
            # Call save_options ensuring current (default or loaded) geometry is included
            self.save_options()


    def save_options(self):
        # Ensure current geometry is captured if not already set by on_close
        # This is more of a fallback; ideally, on_close updates self.window_geometry before calling save_options.
        try:
            # This might fail if root window is not fully initialized or already destroyed
            current_width = self.root.winfo_width()
            current_height = self.root.winfo_height()
            current_x = self.root.winfo_x()
            current_y = self.root.winfo_y()
            # Update self.window_geometry only if these values are sensible (e.g. >0 for width/height)
            # However, this check is tricky as winfo_x/y can be 0.
            # For now, let's assume on_close is the primary source for geometry before saving.
        except tk.TclError: # Window might not exist when save_options is called (e.g. during initial load_options)
             pass # Keep existing self.window_geometry values

        options_to_save = {
            "voice_active": self.voice_active_var.get(),
            "window_width": self.window_geometry["width"],
            "window_height": self.window_geometry["height"],
            "window_x": self.window_geometry["x"],
            "window_y": self.window_geometry["y"],
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
            # self.start_stop_button['text'] = 'Start' # Original text update
            self.state_lbl['text'] = f'{self.state.name} - Paused'
        else:
            self.timer_active = True
            # self.start_stop_button['text'] = 'Pause' # Original text update
            self.set_state_label()

        # Update the image for start/stop button regardless of state change
        # This requires add_control_widget to be designed to be callable for updates,
        # or a specific update method for the button image.
        # For now, the text on the button image is set at creation time.
        # A better approach would be to have start/pause images pre-created or a function to update it.

        # Quick fix: Re-create the button image with new text
        btn_width_px = 207 # Increased by another 50% from 138
        btn_height_px = 69 # Increased by another 50% from 46
        corner_radius_px = 5
        font_name_str, font_size_int, font_weight_str = button_font # Font size might need adjustment
        text_color_str = '#000000'
        current_text = 'Start' if not self.timer_active else 'Pause'

        self.start_stop_button_img = create_rounded_button_image(
            text=current_text, width=btn_width_px, height=btn_height_px, corner_radius=corner_radius_px,
            bg_color=button_bg, text_color=text_color_str, font_name=font_name_str,
            font_size=font_size_int, font_weight=font_weight_str
        )
        self.start_stop_button.configure(image=self.start_stop_button_img)
        self.start_stop_button.image = self.start_stop_button_img


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

    def on_close(self):
        """Handles actions to be performed when the window is closed."""
        logger.info("Window closing, saving options...")
        try:
            # Update window_geometry with the current size and position
            self.window_geometry["width"] = self.root.winfo_width()
            self.window_geometry["height"] = self.root.winfo_height()
            self.window_geometry["x"] = self.root.winfo_x()
            self.window_geometry["y"] = self.root.winfo_y()
            self.save_options()
        except tk.TclError as e:
            # This might happen if the window is already destroyed
            logger.error(f"Error getting window geometry on close: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during on_close: {e}")
        finally:
            self.root.destroy()


if __name__ == '__main__':
    pymo = Pymodoro()
