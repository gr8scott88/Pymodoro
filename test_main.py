import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os

# os.environ['DISPLAY'] = ':0' # Removed: pyautogui will be mocked directly

# Mock tkinter before main.py is imported
mock_tkinter = MagicMock()
type(mock_tkinter).TkVersion = PropertyMock(return_value=8.6) # For pymsgbox
sys.modules['tkinter'] = mock_tkinter
# Ensure tkinter.messagebox is also the mock's messagebox attribute
# main.py does: from tkinter import messagebox
# So, when main.py is imported, its 'messagebox' will be mock_tkinter.messagebox
# The patch target for askyesno should then be 'main.messagebox.askyesno'
# sys.modules['tkinter.messagebox'] = mock_tkinter.messagebox # This line might be redundant if main imports messagebox directly

# Mock pyautogui before main.py is imported to prevent X11 connection errors
sys.modules['pyautogui'] = MagicMock()

from main import Pymodoro, State, timer_dict # main.py imports pyautogui, which needs DISPLAY
from datetime import datetime
import time
# tkinter.messagebox will be patched, so direct import is not strictly necessary at the top level for tests,
# but it's good to know what we're patching.

class TestCheckInactivity(unittest.TestCase):

    @patch('main.tk.Tk') # Mock Tkinter root window as Pymodoro instantiates tk.Tk()
    @patch('main.Pymodoro.build_window') # Prevent GUI building
    @patch('main.Pymodoro.start') # Prevent mainloop
    def setUp(self, mock_start_pymodoro, mock_build_window_pymodoro, mock_tk_pymodoro):
        """Set up a Pymodoro instance for testing."""
        # Configure the mock_tk (which is main.tk.Tk due to the patch)
        # to behave like a Tkinter root window without actually creating one.
        # mock_tk_pymodoro is the MagicMock for tk.Tk
        mock_tk_instance = MagicMock()
        mock_tk_pymodoro.return_value = mock_tk_instance

        self.pymodoro = Pymodoro()
        # Reset interactions and timer for clean state in each test
        self.pymodoro.last_interaction = time.time() 
        self.pymodoro.timer_active = False
        self.pymodoro.state = State.Ready
        # Ensure sec_remaining is initialized; Pymodoro __init__ does this
        # but we are overriding parts of its setup.
        # self.pymodoro.sec_remaining = timer_dict[self.pymodoro.state.name] 
        # Actually, Pymodoro.__init__ sets self.sec_remaining, so it should be fine.
        # Let's ensure time_remaining is also set as per Pymodoro's logic for a Ready state.
        self.pymodoro.time_remaining = timer_dict[self.pymodoro.state.name]


        # Mock methods that might be problematic if not GUI related to check_inactivity
        self.pymodoro.update_timer_label = MagicMock()
        self.pymodoro.set_state_label = MagicMock()
        self.pymodoro.update_state_graphic = MagicMock()
        self.pymodoro.play_pause_media = MagicMock()
        # Wrap reset to spy on it while still executing its (potentially non-GUI) logic
        # Pymodoro.reset calls self.rebuild_window and self.set_time_remaining, self.set_state_label
        # rebuild_window is complex, so it's good it's mocked by Pymodoro.build_window in the class setup
        # For reset, we mainly care it's called and that play_pause_media is also called.
        # Let's make reset a simple MagicMock for these tests to avoid its internal complexities with rebuild_window.
        self.pymodoro.reset = MagicMock()


    @patch('main.messagebox.askyesno') # Corrected patch target
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_not_triggered_within_window(self, mock_datetime, mock_time, mock_askyesno):
        # Scenario: Current time is 10 AM (within 7 AM - 4 PM window)
        mock_dt_instance = MagicMock()
        mock_dt_instance.hour = 10
        mock_datetime.now.return_value = mock_dt_instance

        self.pymodoro.state = State.Working
        self.pymodoro.timer_active = True
        # Simulate being inactive for more than an hour
        self.pymodoro.last_interaction = 0 # way in the past
        mock_time.return_value = 3601 # current time

        self.pymodoro.check_inactivity()

        mock_askyesno.assert_not_called()

    @patch('main.messagebox.askyesno') # Corrected patch target
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_triggered_outside_window_user_yes(self, mock_datetime, mock_time, mock_askyesno):
        # Scenario: Current time is 6 AM (outside 7 AM - 4 PM window)
        mock_dt_instance = MagicMock()
        mock_dt_instance.hour = 6
        mock_datetime.now.return_value = mock_dt_instance

        self.pymodoro.state = State.Working
        self.pymodoro.timer_active = True
        initial_last_interaction = 0 
        self.pymodoro.last_interaction = initial_last_interaction
        current_simulated_time = 3601
        mock_time.return_value = current_simulated_time
        
        mock_askyesno.return_value = True # User responds "yes"

        # Mock update_interaction to check if it's called and its effect
        # Original Pymodoro.update_interaction just updates self.last_interaction
        # We can spy on it or just check the effect.
        # self.pymodoro.update_interaction = MagicMock(wraps=self.pymodoro.update_interaction)
        # Let's check the effect directly.

        self.pymodoro.check_inactivity()

        mock_askyesno.assert_called_once_with("Still there?", "Are you still listening?")
        # self.pymodoro.update_interaction.assert_called_once() # Not needed if checking effect
        self.assertEqual(self.pymodoro.last_interaction, current_simulated_time) # Check if last_interaction was updated
        self.pymodoro.reset.assert_not_called()
        # self.pymodoro.play_pause_media.assert_not_called() # play_pause_media IS NOT CALLED if user says yes.

    @patch('main.messagebox.askyesno') # Corrected patch target
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_triggered_outside_window_user_no(self, mock_datetime, mock_time, mock_askyesno):
        # Scenario: Current time is 5 PM (outside 7 AM - 4 PM window)
        mock_dt_instance = MagicMock()
        mock_dt_instance.hour = 17
        mock_datetime.now.return_value = mock_dt_instance

        self.pymodoro.state = State.Working
        self.pymodoro.timer_active = True
        self.pymodoro.last_interaction = 0 
        mock_time.return_value = 3601
        
        mock_askyesno.return_value = False # User responds "no"

        self.pymodoro.check_inactivity()

        mock_askyesno.assert_called_once_with("Still there?", "Are you still listening?")
        self.pymodoro.reset.assert_called_once()
        self.pymodoro.play_pause_media.assert_called_once() # play_pause_media IS CALLED if user says no
        
    @patch('main.messagebox.askyesno') # Corrected patch target
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_not_triggered_if_not_working_state(self, mock_datetime, mock_time, mock_askyesno):
        mock_dt_instance = MagicMock()
        mock_dt_instance.hour = 6 # Outside window
        mock_datetime.now.return_value = mock_dt_instance

        self.pymodoro.state = State.Rest # Not Working
        self.pymodoro.timer_active = True
        self.pymodoro.last_interaction = 0
        mock_time.return_value = 3601

        self.pymodoro.check_inactivity()
        mock_askyesno.assert_not_called()

    @patch('main.messagebox.askyesno') # Corrected patch target
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_not_triggered_if_timer_not_active(self, mock_datetime, mock_time, mock_askyesno):
        mock_dt_instance = MagicMock()
        mock_dt_instance.hour = 6 # Outside window
        mock_datetime.now.return_value = mock_dt_instance

        self.pymodoro.state = State.Working
        self.pymodoro.timer_active = False # Timer not active
        self.pymodoro.last_interaction = 0
        mock_time.return_value = 3601

        self.pymodoro.check_inactivity()
        mock_askyesno.assert_not_called()

    @patch('main.messagebox.askyesno') # Corrected patch target
    @patch('main.time.time')
    @patch('main.datetime')
    def test_inactivity_check_not_triggered_if_not_inactive_long_enough(self, mock_datetime, mock_time, mock_askyesno):
        mock_dt_instance = MagicMock()
        mock_dt_instance.hour = 6 # Outside window
        mock_datetime.now.return_value = mock_dt_instance

        self.pymodoro.state = State.Working
        self.pymodoro.timer_active = True
        
        # Interaction was less than an hour ago
        # current time mock_time.return_value = 3601
        # last_interaction should be > (3601 - 3600) = 1
        self.pymodoro.last_interaction = 100 # e.g. current time is 3601, last interaction was at 100
        mock_time.return_value = 3601 # current time is 3601

        self.pymodoro.check_inactivity()
        mock_askyesno.assert_not_called()

if __name__ == '__main__':
    unittest.main()
