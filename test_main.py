import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os

# Mock tkinter before main.py is imported
mock_tkinter = MagicMock()
type(mock_tkinter).TkVersion = PropertyMock(return_value=8.6) # For pymsgbox
sys.modules['tkinter'] = mock_tkinter

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
from main import Pymodoro, State, timer_dict
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

    def helper_test_sound_on_transition(self, initial_state, initial_rests, sound_name, expected_final_state, expected_final_rests=None):
        self.pymodoro.state = initial_state
        if initial_rests is not None:
            self.pymodoro.rests = initial_rests

        expected_path = os.path.join(main.script_dir, 'res', f"{sound_name}.mp3")

        with patch('main.os.path.exists', return_value=True) as mock_exists:
            self.pymodoro.transition_state()
            if sound_name: # Only expect path check if a sound is supposed to play
                mock_exists.assert_called_once_with(expected_path)
            else:
                mock_exists.assert_not_called()


        if sound_name:
            self.mock_pygame_mixer_music.load.assert_called_once_with(expected_path)
            self.mock_pygame_mixer_music.play.assert_called_once()
        else:
            self.mock_pygame_mixer_music.load.assert_not_called()
            self.mock_pygame_mixer_music.play.assert_not_called()

        self.pymodoro.play_pause_media.assert_called_once()
        self.assertEqual(self.pymodoro.state, expected_final_state)
        if expected_final_rests is not None:
            self.assertEqual(self.pymodoro.rests, expected_final_rests)

    def test_transition_working_to_short_rest(self):
        self.helper_test_sound_on_transition(State.Working, 0, "work_to_short_rest", State.Rest, 1)

    def test_transition_working_to_long_rest(self):
        self.helper_test_sound_on_transition(State.Working, 3, "work_to_long_rest", State.LongRest, 0)

    def test_transition_rest_to_working(self):
        self.helper_test_sound_on_transition(State.Rest, None, "rest_to_work", State.Working)

    def test_transition_long_rest_to_working(self):
        self.helper_test_sound_on_transition(State.LongRest, None, "rest_to_work", State.Working)

if __name__ == '__main__':
    unittest.main()
