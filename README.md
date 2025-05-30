# Pymodoro
Python pomodoro app for Windows

Quick GUI for managing work via pomoro method with the following timing sequeng: 
<ul>
  <li>Work: 25 min</li>
  <li>Rest: 5 min </li>
  <li>Work: 25 min</li>
  <li>Rest: 5 min </li>
  <li>Work: 25 min</li>
  <li>Rest: 5 min </li>
  <li>Work: 25 min</li>
  <li>Rest: 15 min </li>
</ul>

Utilizes "play/pause" keyboard command, so will work with any windows media client (Spotify, YouTube, etc.)

## Voice Prompts

Pymodoro includes a feature for voice prompts to audibly signal certain events. Users can customize these by placing their own audio files in the `res` directory. The application expects these files to be in `.mp3` format.

The specific sound events and their corresponding audio file names are:

-   **Transition from Work to a short rest**: `lets_take_a_quick_break.mp3`
-   **Transition from Rest (short or long) to Work**: `lets_get_back_to_work.mp3`
-   **Transition from Work to a long rest**: `lets_take_a_longer_break.mp3`
-   **"Are you still listening?" inactivity popup**: `are_you_still_listening.mp3`

Ensure your custom audio files are named exactly as listed above and placed in the `res` folder for the voice prompts to work correctly.

*(Note: Audio playback is handled by the `pygame.mixer` library, which replaced the previous `playsound` library for improved compatibility and control.)*
