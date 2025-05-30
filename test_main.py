import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os

# Mock tkinter before main.py is imported
mock_tkinter = MagicMock()
type(mock_tkinter).TkVersion = PropertyMock(return_value=8.6) # For pymsgbox
sys.modules['tkinter'] = mock_tkinter

# Mock pyautogui before main.py is imported to prevent X11 connection errors
sys.modules['pyautogui'] = MagicMock()

from main import Pymodoro, State, timer_dict 
from datetime import datetime
import time

class TestCheckInactivity(unittest.TestCase):

    @patch('main.tk.Tk') 
    @patch('main.Pymodoro.build_window') 
    @patch('main.Pymodoro.start') 
    def setUp(self, mock_start_pymodoro, mock_build_window_pymodoro, mock_tk_pymodoro): # mock_play_sound_method removed
        mock_tk_instance = MagicMock()
        mock_tk_pymodoro.return_value = mock_tk_instance

        self.pymodoro = Pymodoro()
        # Manually patch the play_sound method on the instance
        self.pymodoro.play_sound = MagicMock(name='play_sound_mock_check_inactivity') 

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
        self.pymodoro.play_sound.assert_not_called() 

    @patch('main.messagebox.askyesno') 
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_triggered_outside_window_user_yes(self, mock_datetime, mock_time, mock_askyesno):
        mock_dt_instance = MagicMock()
        mock_dt_instance.hour = 6
        mock_datetime.now.return_value = mock_dt_instance
        self.pymodoro.state = State.Working
        self.pymodoro.timer_active = True
        initial_last_interaction = 0 
        self.pymodoro.last_interaction = initial_last_interaction
        current_simulated_time = 3601
        mock_time.return_value = current_simulated_time
        mock_askyesno.return_value = True

        self.pymodoro.check_inactivity()

        self.pymodoro.play_sound.assert_called_once_with("are_you_still_listening")
        mock_askyesno.assert_called_once_with("Still there?", "Are you still listening?")
        self.assertEqual(self.pymodoro.last_interaction, current_simulated_time) 
        self.pymodoro.reset.assert_not_called()
        self.pymodoro.play_pause_media.assert_not_called()

    @patch('main.messagebox.askyesno') 
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_triggered_outside_window_user_no(self, mock_datetime, mock_time, mock_askyesno):
        mock_dt_instance = MagicMock()
        mock_dt_instance.hour = 17
        mock_datetime.now.return_value = mock_dt_instance
        self.pymodoro.state = State.Working
        self.pymodoro.timer_active = True
        self.pymodoro.last_interaction = 0 
        mock_time.return_value = 3601
        mock_askyesno.return_value = False

        self.pymodoro.check_inactivity()
        
        self.pymodoro.play_sound.assert_called_once_with("are_you_still_listening")
        mock_askyesno.assert_called_once_with("Still there?", "Are you still listening?")
        self.pymodoro.reset.assert_called_once()
        self.pymodoro.play_pause_media.assert_called_once() 
        
    @patch('main.messagebox.askyesno') 
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_not_triggered_if_not_working_state(self, mock_datetime, mock_time, mock_askyesno):
        mock_dt_instance = MagicMock()
        mock_dt_instance.hour = 6 
        mock_datetime.now.return_value = mock_dt_instance
        self.pymodoro.state = State.Rest 
        self.pymodoro.timer_active = True
        self.pymodoro.last_interaction = 0
        mock_time.return_value = 3601

        self.pymodoro.check_inactivity()
        mock_askyesno.assert_not_called()
        self.pymodoro.play_sound.assert_not_called()

    @patch('main.messagebox.askyesno') 
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_not_triggered_if_timer_not_active(self, mock_datetime, mock_time, mock_askyesno):
        mock_dt_instance = MagicMock()
        mock_dt_instance.hour = 6 
        mock_datetime.now.return_value = mock_dt_instance
        self.pymodoro.state = State.Working
        self.pymodoro.timer_active = False 
        self.pymodoro.last_interaction = 0
        mock_time.return_value = 3601

        self.pymodoro.check_inactivity()
        mock_askyesno.assert_not_called()
        self.pymodoro.play_sound.assert_not_called()

    @patch('main.messagebox.askyesno') 
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_not_triggered_if_not_inactive_long_enough(self, mock_datetime, mock_time, mock_askyesno):
        mock_dt_instance = MagicMock()
        mock_dt_instance.hour = 6 
        mock_datetime.now.return_value = mock_dt_instance
        self.pymodoro.state = State.Working
        self.pymodoro.timer_active = True
        self.pymodoro.last_interaction = 100 
        mock_time.return_value = 3601 

        self.pymodoro.check_inactivity()
        mock_askyesno.assert_not_called()
        self.pymodoro.play_sound.assert_not_called()


class TestStateTransitions(unittest.TestCase):

    @patch('main.tk.Tk')
    @patch('main.Pymodoro.build_window')
    @patch('main.Pymodoro.start')
    def setUp(self, mock_start_pymodoro, mock_build_window_pymodoro, mock_tk_pymodoro): # mock_play_sound_method removed
        mock_tk_instance = MagicMock()
        mock_tk_pymodoro.return_value = mock_tk_instance

        self.pymodoro = Pymodoro()
        # Manually patch the play_sound method on the instance
        self.pymodoro.play_sound = MagicMock(name='play_sound_mock_transitions')

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
        self.pymodoro.play_sound.assert_not_called()
        self.pymodoro.play_pause_media.assert_called_once()
        self.assertEqual(self.pymodoro.state, State.Working)
        self.assertTrue(self.pymodoro.timer_active)

    def test_transition_working_to_short_rest(self):
        self.pymodoro.state = State.Working
        self.pymodoro.rests = 0 
        self.pymodoro.transition_state()
        self.pymodoro.play_sound.assert_called_once_with("work_to_short_rest")
        self.pymodoro.play_pause_media.assert_called_once()
        self.assertEqual(self.pymodoro.state, State.Rest)
        self.assertEqual(self.pymodoro.rests, 1)

    def test_transition_working_to_long_rest(self):
        self.pymodoro.state = State.Working
        self.pymodoro.rests = 3
        self.pymodoro.transition_state()
        self.pymodoro.play_sound.assert_called_once_with("work_to_long_rest")
        self.pymodoro.play_pause_media.assert_called_once()
        self.assertEqual(self.pymodoro.state, State.LongRest)
        self.assertEqual(self.pymodoro.rests, 0) 

    def test_transition_rest_to_working(self):
        self.pymodoro.state = State.Rest
        self.pymodoro.transition_state()
        self.pymodoro.play_sound.assert_called_once_with("rest_to_work")
        self.pymodoro.play_pause_media.assert_called_once()
        self.assertEqual(self.pymodoro.state, State.Working)

    def test_transition_long_rest_to_working(self):
        self.pymodoro.state = State.LongRest
        self.pymodoro.transition_state()
        self.pymodoro.play_sound.assert_called_once_with("rest_to_work")
        self.pymodoro.play_pause_media.assert_called_once()
        self.assertEqual(self.pymodoro.state, State.Working)

if __name__ == '__main__':
    unittest.main()
