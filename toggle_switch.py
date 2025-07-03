import tkinter as tk

class ToggleSwitch(tk.Canvas):
    def __init__(self, parent, variable, command=None, width=44, height=22, **kwargs):
        super().__init__(parent, width=width, height=height, borderwidth=0, highlightthickness=0, **kwargs)

        self.variable = variable
        self.command = command
        self.width = width
        self.height = height
        self.knob_diameter = height - 4  # Knob slightly smaller than canvas height, with 2px padding top/bottom
        self.track_color_on = '#abdbe3'  # Light Blue (button_bg, for better contrast with window bg)
        self.track_color_off = '#cccccc'  # Light Gray
        self.knob_color_on = '#ffffff'    # White
        self.knob_color_off = '#a0a0a0'   # Medium Gray

        self.configure(bg=self.master.cget('bg')) # Match parent background

        self.bind("<Button-1>", self._on_click)
        self.variable.trace_add("write", self._on_variable_change) # Update visuals if var changes externally

        self._draw_switch()

    def _draw_switch(self):
        self.delete("all")
        current_state = self.variable.get()

        # Track
        track_x1 = 0
        track_y1 = 0
        track_x2 = self.width
        track_y2 = self.height
        radius = self.height / 2

        track_color = self.track_color_on if current_state else self.track_color_off

        # Simplified rounded rectangle for track (pill shape)
        # Left semi-circle
        self.create_oval(track_x1, track_y1, track_x1 + 2 * radius, track_y2, fill=track_color, outline=track_color)
        # Right semi-circle
        self.create_oval(track_x2 - 2 * radius, track_y1, track_x2, track_y2, fill=track_color, outline=track_color)
        # Center rectangle
        self.create_rectangle(track_x1 + radius, track_y1, track_x2 - radius, track_y2, fill=track_color, outline=track_color)

        # Knob
        knob_x_padding = 2  # Padding from the edge of the track
        knob_y = (self.height - self.knob_diameter) / 2 # Centered vertically

        if current_state:  # ON state - knob on the right
            knob_x1 = self.width - self.knob_diameter - knob_x_padding
            knob_color = self.knob_color_on
        else:  # OFF state - knob on the left
            knob_x1 = knob_x_padding
            knob_color = self.knob_color_off

        knob_x2 = knob_x1 + self.knob_diameter
        knob_y1 = knob_y
        knob_y2 = knob_y + self.knob_diameter

        self.create_oval(knob_x1, knob_y1, knob_x2, knob_y2, fill=knob_color, outline=knob_color)

    def _on_click(self, event):
        current_state = self.variable.get()
        self.variable.set(not current_state)
        # The trace on self.variable will call _draw_switch and the command

    def _on_variable_change(self, *args):
        self._draw_switch()
        if self.command:
            self.command()

if __name__ == '__main__':
    # Example Usage
    root = tk.Tk()
    root.title("Toggle Switch Test")
    root.geometry("200x100")
    root.configure(bg='#f0f0f0') # Example background

    var = tk.BooleanVar(value=False)

    def on_toggle():
        print(f"Toggle state: {var.get()}")

    label = tk.Label(root, text="Test Switch:", bg=root.cget('bg'))
    label.pack(side=tk.LEFT, padx=5, pady=30)

    # Note: For the ToggleSwitch to correctly pick up its master's background for its own canvas bg,
    # it should be created *after* its direct parent (if that parent has a specific bg).
    # Here, its parent is root.
    toggle = ToggleSwitch(root, var, command=on_toggle, width=50, height=25)
    toggle.pack(side=tk.LEFT, padx=5, pady=30)

    # Button to test external variable change
    def flip_var():
        var.set(not var.get())

    test_button = tk.Button(root, text="Flip Var Externally", command=flip_var)
    test_button.pack(pady=5)

    root.mainloop()
