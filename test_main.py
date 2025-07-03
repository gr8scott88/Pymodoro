import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os
import json # Added for options testing

# Mock tkinter before main.py is imported
# We need to ensure BooleanVar is a class that can be instantiated,
# and its instances have get/set methods that can be further mocked.
mock_tkinter_module = MagicMock()
type(mock_tkinter_module).TkVersion = PropertyMock(return_value=8.6) # For pymsgbox

# Create a mock BooleanVar class that can be instantiated
mock_boolean_var_class = MagicMock(name="MockBooleanVarClass")
def boolean_var_constructor(*args, **kwargs):
    # This instance will have .get() and .set() as MagicMock methods by default
    instance = MagicMock(name=f"MockBooleanVarInstance_{kwargs.get('name', 'unnamed')}")
    # Store the initial value if provided, defaulting to False (tk.BooleanVar default)
    initial_value = kwargs.get('value', False)

    # Internal state for this instance
    _current_val_for_instance = [initial_value] # Use a list to allow modification in closures

    def mock_get():
        return _current_val_for_instance[0]

    def mock_set(val):
        _current_val_for_instance[0] = bool(val)
        return None # .set() usually returns None

    instance.get.side_effect = mock_get
    instance.set.side_effect = mock_set

    # Initialize its state
    instance.set(initial_value)
    return instance

mock_boolean_var_class.side_effect = boolean_var_constructor
mock_tkinter_module.BooleanVar = mock_boolean_var_class
sys.modules['tkinter'] = mock_tkinter_module

# Make the original mock_tkinter available if some tests rely on its specific MagicMock nature directly
mock_tkinter = mock_tkinter_module

# Mock pyautogui before main.py is imported
sys.modules['pyautogui'] = MagicMock()

# Mock pygame and its submodules/methods used in main.py before main.py is imported
mock_pygame_global = MagicMock(name='pygame_mock_global') # Renamed to avoid confusion
mock_pygame_global.mixer = MagicMock(name='pygame_mixer_mock_global')
mock_pygame_global.mixer.init = MagicMock(name='pygame_mixer_init_mock_global')
# pygame.mixer.music will be freshly mocked in setUp for each test class instance
mock_pygame_global.mixer.music = MagicMock(name='pygame_mixer_music_placeholder_global')
mock_pygame_global.error = type('PygameErrorMockGlobal', (Exception,), {})
sys.modules['pygame'] = mock_pygame_global

# Import main AFTER all crucial sys.modules mocks are in place
import main # Needed to access main.script_dir
from main import Pymodoro, State, timer_dict, OPTIONS_FILE # Added OPTIONS_FILE
from datetime import datetime
import time

class TestCheckInactivity(unittest.TestCase):

    @patch('main.tk.Tk')
    @patch('main.Pymodoro.build_window')
    @patch('main.Pymodoro.start')
    def setUp(self, mock_start_pymodoro, mock_build_window_pymodoro, mock_tk_pymodoro):
        mock_tk_instance = MagicMock()
        mock_tk_pymodoro.return_value = mock_tk_instance

        # Reset init mock which is on the global mock_pygame_global.mixer
        mock_pygame_global.mixer.init.reset_mock()

        # Create fresh mocks for mixer.music and its methods for each test
        self.mock_pygame_mixer_music = MagicMock(name='fresh_mixer_music_for_test_check_inactivity')
        self.mock_pygame_mixer_music.load = MagicMock(name='fresh_mixer_music_load_mock')
        self.mock_pygame_mixer_music.play = MagicMock(name='fresh_mixer_music_play_mock')

        # Replace the 'music' attribute on the globally mocked pygame.mixer for this test's scope
        mock_pygame_global.mixer.music = self.mock_pygame_mixer_music

        self.pymodoro = Pymodoro() # This will call mock_pygame_global.mixer.init()

        mock_pygame_global.mixer.init.assert_called_once()

        self.pymodoro.last_interaction = time.time()
        self.pymodoro.timer_active = False
        self.pymodoro.state = State.Ready
        self.pymodoro.time_remaining = timer_dict[self.pymodoro.state.name]

        self.pymodoro.update_timer_label = MagicMock()
        self.pymodoro.set_state_label = MagicMock()
        self.pymodoro.update_state_graphic = MagicMock()
        self.pymodoro.play_pause_media = MagicMock()
        self.pymodoro.reset = MagicMock()

        # Pymodoro.__init__ already creates self.voice_active_var using the mocked tkinter.BooleanVar
        # The mock_boolean_var_class ensures it has a working get/set via side_effect.
        # load_options in Pymodoro.__init__ will use this mocked BooleanVar.
        # We need to ensure its state is what load_options would have set.
        # Since OPTIONS_FILE doesn't exist by default at this stage of setUp,
        # load_options would set it to True and save the file.
        self.pymodoro.voice_active_var.set(True)


    @patch('main.messagebox.askyesno')
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_not_triggered_within_window(self, mock_datetime, mock_time, mock_askyesno):
        mock_dt_instance = MagicMock()
        mock_dt_instance.hour = 10
        mock_datetime.now.return_value = mock_dt_instance
        self.pymodoro.state = State.Working
        self.pymodoro.timer_active = True
        self.pymodoro.last_interaction = 0
        mock_time.return_value = 3601

        self.pymodoro.check_inactivity()

        mock_askyesno.assert_not_called()
        self.mock_pygame_mixer_music.load.assert_not_called()
        self.mock_pygame_mixer_music.play.assert_not_called()

    @patch('main.messagebox.askyesno')
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_triggered_outside_window_user_yes(self, mock_datetime, mock_time, mock_askyesno):
        sound_name = "are_you_still_listening"
        expected_path = os.path.join(main.script_dir, 'res', f"{sound_name}.mp3")

        mock_dt_instance = MagicMock()
        mock_dt_instance.hour = 6
        mock_datetime.now.return_value = mock_dt_instance
        self.pymodoro.state = State.Working
        self.pymodoro.timer_active = True
        self.pymodoro.last_interaction = 0
        current_simulated_time = 3601
        mock_time.return_value = current_simulated_time
        mock_askyesno.return_value = True

        with patch('main.os.path.exists', return_value=True) as mock_exists:
            self.pymodoro.check_inactivity()
            mock_exists.assert_called_once_with(expected_path)

        self.mock_pygame_mixer_music.load.assert_called_once_with(expected_path)
        self.mock_pygame_mixer_music.play.assert_called_once()
        mock_askyesno.assert_called_once_with("Still there?", "Are you still listening?")
        self.assertEqual(self.pymodoro.last_interaction, current_simulated_time)
        self.pymodoro.reset.assert_not_called()
        self.pymodoro.play_pause_media.assert_not_called()

    @patch('main.messagebox.askyesno')
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_triggered_outside_window_user_no(self, mock_datetime, mock_time, mock_askyesno):
        sound_name = "are_you_still_listening"
        expected_path = os.path.join(main.script_dir, 'res', f"{sound_name}.mp3")

        mock_dt_instance = MagicMock()
        mock_dt_instance.hour = 17
        mock_datetime.now.return_value = mock_dt_instance
        self.pymodoro.state = State.Working
        self.pymodoro.timer_active = True
        self.pymodoro.last_interaction = 0
        mock_time.return_value = 3601
        mock_askyesno.return_value = False

        with patch('main.os.path.exists', return_value=True) as mock_exists:
            self.pymodoro.check_inactivity()
            mock_exists.assert_called_once_with(expected_path)

        self.mock_pygame_mixer_music.load.assert_called_once_with(expected_path)
        self.mock_pygame_mixer_music.play.assert_called_once()
        mock_askyesno.assert_called_once_with("Still there?", "Are you still listening?")
        self.pymodoro.reset.assert_called_once()
        self.pymodoro.play_pause_media.assert_called_once()

    @patch('main.messagebox.askyesno')
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_not_triggered_if_not_working_state(self, mock_datetime, mock_time, mock_askyesno):
        mock_dt_instance = MagicMock() # Added full setup for clarity
        mock_dt_instance.hour = 6
        mock_datetime.now.return_value = mock_dt_instance
        self.pymodoro.state = State.Rest
        self.pymodoro.timer_active = True
        self.pymodoro.last_interaction = 0
        mock_time.return_value = 3601
        self.pymodoro.check_inactivity()
        mock_askyesno.assert_not_called()
        self.mock_pygame_mixer_music.load.assert_not_called()

    @patch('main.messagebox.askyesno')
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_not_triggered_if_timer_not_active(self, mock_datetime, mock_time, mock_askyesno):
        mock_dt_instance = MagicMock() # Added full setup for clarity
        mock_dt_instance.hour = 6
        mock_datetime.now.return_value = mock_dt_instance
        self.pymodoro.state = State.Working
        self.pymodoro.timer_active = False
        self.pymodoro.last_interaction = 0
        mock_time.return_value = 3601
        self.pymodoro.check_inactivity()
        mock_askyesno.assert_not_called()
        self.mock_pygame_mixer_music.load.assert_not_called()

    @patch('main.messagebox.askyesno')
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_not_triggered_if_not_inactive_long_enough(self, mock_datetime, mock_time, mock_askyesno):
        mock_dt_instance = MagicMock() # Added full setup for clarity
        mock_dt_instance.hour = 6
        mock_datetime.now.return_value = mock_dt_instance
        self.pymodoro.state = State.Working
        self.pymodoro.timer_active = True
        self.pymodoro.last_interaction = 100
        mock_time.return_value = 3601
        self.pymodoro.check_inactivity()
        mock_askyesno.assert_not_called()
        self.mock_pygame_mixer_music.load.assert_not_called()


class TestStateTransitions(unittest.TestCase):

    @patch('main.tk.Tk')
    @patch('main.Pymodoro.build_window')
    @patch('main.Pymodoro.start')
    def setUp(self, mock_start_pymodoro, mock_build_window_pymodoro, mock_tk_pymodoro):
        mock_tk_instance = MagicMock()
        mock_tk_pymodoro.return_value = mock_tk_instance

        mock_pygame_global.mixer.init.reset_mock()

        self.mock_pygame_mixer_music = MagicMock(name='fresh_mixer_music_for_test_transitions')
        self.mock_pygame_mixer_music.load = MagicMock(name='fresh_mixer_music_load_mock')
        self.mock_pygame_mixer_music.play = MagicMock(name='fresh_mixer_music_play_mock')
        mock_pygame_global.mixer.music = self.mock_pygame_mixer_music

        self.pymodoro = Pymodoro()
        mock_pygame_global.mixer.init.assert_called_once()

        self.pymodoro.state = State.Ready
        self.pymodoro.rests = 0
        self.pymodoro.time_remaining = timer_dict[self.pymodoro.state.name]
        self.pymodoro.timer_active = False

        self.pymodoro.set_time_remaining = MagicMock()
        self.pymodoro.set_state_label = MagicMock()
        self.pymodoro.update_state_graphic = MagicMock()
        self.pymodoro.play_pause_media = MagicMock()

    def test_transition_ready_to_working(self):
        self.pymodoro.state = State.Ready
        self.pymodoro.transition_state()
        self.mock_pygame_mixer_music.load.assert_not_called()
        self.mock_pygame_mixer_music.play.assert_not_called()
        self.pymodoro.play_pause_media.assert_called_once()
        self.assertEqual(self.pymodoro.state, State.Working)

    def helper_test_sound_on_transition(self, initial_state, initial_rests, sound_name, expected_final_state, voice_active_setting, expected_final_rests=None):
        self.pymodoro.state = initial_state
        if initial_rests is not None:
            self.pymodoro.rests = initial_rests

        # Set the desired voice_active state for the test using the mocked set
        self.pymodoro.voice_active_var.set(voice_active_setting)

        # Reset mocks for play/load before the action
        self.mock_pygame_mixer_music.load.reset_mock()
        self.mock_pygame_mixer_music.play.reset_mock()


        expected_path = os.path.join(main.script_dir, 'res', f"{sound_name}.mp3")

        with patch('main.os.path.exists', return_value=True) as mock_exists:
            self.pymodoro.transition_state()
            if sound_name and voice_active_setting: # Only expect path check if a sound is supposed to play and voice is on
                mock_exists.assert_called_once_with(expected_path)
            else:
                mock_exists.assert_not_called()


        if sound_name and voice_active_setting:
            self.mock_pygame_mixer_music.load.assert_called_once_with(expected_path)
            self.mock_pygame_mixer_music.play.assert_called_once()
        else:
            self.mock_pygame_mixer_music.load.assert_not_called()
            self.mock_pygame_mixer_music.play.assert_not_called()

        self.pymodoro.play_pause_media.assert_called_once() # This is called regardless of sound
        self.assertEqual(self.pymodoro.state, expected_final_state)
        if expected_final_rests is not None:
            self.assertEqual(self.pymodoro.rests, expected_final_rests)

    # --- Tests for voice ON ---
    def test_transition_working_to_short_rest_voice_on(self):
        self.helper_test_sound_on_transition(State.Working, 0, "lets_take_a_quick_break", State.Rest, True, 1)

    def test_transition_working_to_long_rest_voice_on(self):
        self.helper_test_sound_on_transition(State.Working, 3, "lets_take_a_longer_break", State.LongRest, True, 0)

    def test_transition_rest_to_working_voice_on(self):
        self.helper_test_sound_on_transition(State.Rest, None, "lets_get_back_to_work", State.Working, True)

    def test_transition_long_rest_to_working_voice_on(self):
        self.helper_test_sound_on_transition(State.LongRest, None, "lets_get_back_to_work", State.Working, True)

    # --- Tests for voice OFF ---
    def test_transition_working_to_short_rest_voice_off(self):
        self.helper_test_sound_on_transition(State.Working, 0, "lets_take_a_quick_break", State.Rest, False, 1)

    def test_transition_working_to_long_rest_voice_off(self):
        self.helper_test_sound_on_transition(State.Working, 3, "lets_take_a_longer_break", State.LongRest, False, 0)

    def test_transition_rest_to_working_voice_off(self):
        self.helper_test_sound_on_transition(State.Rest, None, "lets_get_back_to_work", State.Working, False)

    def test_transition_long_rest_to_working_voice_off(self):
        self.helper_test_sound_on_transition(State.LongRest, None, "lets_get_back_to_work", State.Working, False)


class TestOptionsPersistence(unittest.TestCase):

    @patch('main.tk.Tk')
    @patch('main.Pymodoro.build_window')
    @patch('main.Pymodoro.start')
    def setUp(self, mock_start_pymodoro, mock_build_window_pymodoro, mock_tk_pymodoro):
        mock_tk_instance = MagicMock()
        mock_tk_pymodoro.return_value = mock_tk_instance

        # Mock pygame mixer specifically for Pymodoro instantiation if needed,
        # though Pymodoro's load_options doesn't directly use pygame.
        # However, Pymodoro.__init__ calls pygame.mixer.init().
        mock_pygame_global.mixer.init.reset_mock()
        self.mock_pygame_mixer_music = MagicMock(name='fresh_mixer_music_for_options_test')
        mock_pygame_global.mixer.music = self.mock_pygame_mixer_music

        # Clean up options file before each test
        try:
            os.remove(OPTIONS_FILE)
        except OSError:
            pass # File might not exist, which is fine

        # Pymodoro instance is created after potential OPTIONS_FILE cleanup or creation
        # Pymodoro instance will be created in each test method for TestOptionsPersistence
        # as the state of OPTIONS_FILE before Pymodoro init is crucial.
        # For this class, self.pymodoro is not created in setUp.

    def tearDown(self):
        # Clean up options file after each test
        try:
            os.remove(OPTIONS_FILE)
        except OSError:
            pass

    @patch('main.tk.Tk')
    @patch('main.Pymodoro.build_window')
    @patch('main.Pymodoro.start')
    def test_load_default_options_file_creation(self, mock_start, mock_build, mock_tk_root_constructor):
        # This test relies on Pymodoro.__init__ calling load_options,
        # which should create and save default options if file doesn't exist.
        # The mocked BooleanVar should correctly .set(True) and then .get() returning True.
        # And save_options should .get() True and write to file.

        # Ensure file does not exist
        if os.path.exists(OPTIONS_FILE): os.remove(OPTIONS_FILE)

        # main.tk.Tk() is already globally mocked to return a MagicMock instance by default from @patch
        # The BooleanVar is also globally mocked to be functional.
        pymodoro_instance = Pymodoro()

        # Assertions
        self.assertTrue(pymodoro_instance.voice_active_var.get()) # Check mock's state
        self.assertTrue(os.path.exists(OPTIONS_FILE))
        with open(OPTIONS_FILE, 'r') as f:
            options = json.load(f)
        self.assertEqual(options, {"voice_active": True}) # Check file content

    # Patches for Pymodoro's dependencies during instantiation
    @patch('main.tk.Tk')
    @patch('main.Pymodoro.build_window')
    @patch('main.Pymodoro.start')
    def test_load_options_voice_active_false(self, mock_start, mock_build, mock_tk_root_constructor):
        with open(OPTIONS_FILE, 'w') as f:
            json.dump({"voice_active": False}, f)

        pymodoro_instance = Pymodoro()
        # load_options should have called self.voice_active_var.set(False)
        self.assertFalse(pymodoro_instance.voice_active_var.get())

    @patch('main.tk.Tk')
    @patch('main.Pymodoro.build_window')
    @patch('main.Pymodoro.start')
    def test_load_options_voice_active_true(self, mock_start, mock_build, mock_tk_root_constructor):
        with open(OPTIONS_FILE, 'w') as f:
            json.dump({"voice_active": True}, f)

        pymodoro_instance = Pymodoro()
        self.assertTrue(pymodoro_instance.voice_active_var.get())

    @patch('main.tk.Tk')
    @patch('main.Pymodoro.build_window')
    @patch('main.Pymodoro.start')
    def test_save_options(self, mock_start, mock_build, mock_tk_root_constructor):
        pymodoro_instance = Pymodoro() # Creates default options file (voice_active: True via load_options)
        self.assertTrue(pymodoro_instance.voice_active_var.get()) # Initial state check

        # Test saving False
        pymodoro_instance.voice_active_var.set(False) # Uses the mocked BooleanVar's set
        pymodoro_instance.save_options() # Uses the mocked BooleanVar's get
        with open(OPTIONS_FILE, 'r') as f:
            options = json.load(f)
        self.assertEqual(options, {"voice_active": False})

        # Test saving True
        pymodoro_instance.voice_active_var.set(True)
        pymodoro_instance.save_options()
        with open(OPTIONS_FILE, 'r') as f:
            options = json.load(f)
        self.assertEqual(options, {"voice_active": True})

    @patch('main.tk.Tk')
    @patch('main.Pymodoro.build_window')
    @patch('main.Pymodoro.start')
    def test_load_corrupted_options_file(self, mock_start, mock_build, mock_tk_root_constructor):
        with open(OPTIONS_FILE, 'w') as f:
            f.write("this is not valid json")

        pymodoro_instance = Pymodoro()
        # load_options should call .set(True) and save_options
        self.assertTrue(pymodoro_instance.voice_active_var.get())
        self.assertTrue(os.path.exists(OPTIONS_FILE))
        with open(OPTIONS_FILE, 'r') as f:
            options = json.load(f)
        self.assertEqual(options, {"voice_active": True})

    @patch('main.tk.Tk')
    @patch('main.Pymodoro.build_window')
    @patch('main.Pymodoro.start')
    def test_load_options_missing_key(self, mock_start, mock_build, mock_tk_root_constructor):
        with open(OPTIONS_FILE, 'w') as f:
            json.dump({"another_option": "some_value"}, f)

        pymodoro_instance = Pymodoro()
        # load_options should default to True and call save_options
        self.assertTrue(pymodoro_instance.voice_active_var.get())
        with open(OPTIONS_FILE, 'r') as f:
            options = json.load(f)
        self.assertEqual(options.get("voice_active"), True)


if __name__ == '__main__':
    unittest.main()
