import tkinter as tk
from PIL import Image, ImageDraw, ImageTk, ImageFont
import os # For font path if needed

# Define a global default font path or a way to find fonts if needed.
# This might need adjustment based on where fonts are located on the system
# or if a specific font file is bundled with the application.
try:
    # Common path for Arial on Windows
    DEFAULT_FONT_PATH = "arial.ttf"
    ImageFont.truetype(DEFAULT_FONT_PATH, 10) # Test load
except IOError:
    # Fallback for other systems or if Arial is not in the default path
    # On Linux, fc-match Arial might give a path, or use a common sans-serif
    # For simplicity, if Arial isn't found directly, Pillow might find it
    # or use a default. For more robustness, one might bundle a .ttf file.
    try:
        DEFAULT_FONT_PATH = "DejaVuSans.ttf" # Common on Linux
        ImageFont.truetype(DEFAULT_FONT_PATH, 10)
    except IOError:
        DEFAULT_FONT_PATH = None # Pillow will use a default font
        print("Warning: Arial or DejaVuSans font not found. Using Pillow's default font.")


def create_rounded_rectangle_image(width, height, corner_radius, color):
    """
    Creates an image of a rounded rectangle with a transparent background.
    """
    # Create an RGBA image (with alpha channel for transparency)
    image = Image.new("RGBA", (width, height), (255, 255, 255, 0)) # Transparent background
    draw = ImageDraw.Draw(image)

    # Coordinates for the rounded rectangle
    # x0, y0, x1, y1
    rect_coords = [0, 0, width, height]

    # Draw the rounded rectangle
    # For Pillow < 9.3.0, radius is a single value.
    # For Pillow >= 9.3.0, rounded_rectangle can take different radii for each corner.
    # We'll use a single radius for all corners.
    draw.rounded_rectangle(rect_coords, radius=corner_radius, fill=color)

    return image

def create_rounded_button_image(text, width, height, corner_radius,
                                bg_color, text_color, font_name=None, font_size=12, font_weight="normal"):
    """
    Creates a button-like image with rounded corners and text.

    Args:
        text (str): The text to display on the button.
        width (int): The width of the button image in pixels.
        height (int): The height of the button image in pixels.
        corner_radius (int): The radius for the rounded corners.
        bg_color (str): Background color of the button (e.g., '#RRGGBB').
        text_color (str): Color of the text (e.g., '#RRGGBB').
        font_name (str, optional): Name of the font. Defaults to system default or a predefined one.
        font_size (int, optional): Size of the font. Defaults to 12.
        font_weight (str, optional): "normal" or "bold".

    Returns:
        ImageTk.PhotoImage: The generated button image.
    """
    # 1. Create the rounded rectangle shape
    button_shape = create_rounded_rectangle_image(width, height, corner_radius, bg_color)

    # 2. Prepare to draw text
    draw = ImageDraw.Draw(button_shape)

    # 3. Load font
    actual_font_name = font_name if font_name else DEFAULT_FONT_PATH
    try:
        if font_weight == "bold":
            # For bold, some fonts have a specific bold variant (e.g., "arialbd.ttf")
            # Or Pillow can try to emulate bold if the font supports it.
            # Trying a common convention for bold fonts.
            try:
                bold_font_name = actual_font_name.replace(".ttf", "bd.ttf") if actual_font_name else None
                if bold_font_name and os.path.exists(bold_font_name):
                     font = ImageFont.truetype(bold_font_name, font_size)
                elif actual_font_name: # Try with "Bold" appended for some font naming schemes
                    font = ImageFont.truetype(actual_font_name.replace(".ttf"," BOLD.ttf"), font_size) # common way to specify bold font
                else: # fallback to pillow's default bold if possible
                     font = ImageFont.truetype(actual_font_name, font_size, encoding='unic', layout_engine=ImageFont.LAYOUT_RAQM)
            except IOError: # Fallback to regular with simulated bold if possible or just regular
                font = ImageFont.truetype(actual_font_name, font_size)
        else:
            font = ImageFont.truetype(actual_font_name, font_size)
    except IOError:
        print(f"Warning: Font '{actual_font_name}' not found. Using Pillow's default font.")
        font = ImageFont.load_default()
    except Exception as e:
        print(f"Error loading font: {e}. Using Pillow's default font.")
        font = ImageFont.load_default()


    # 4. Calculate text position for centering
    # Use textbbox for more accurate positioning with Pillow 9.2.0+
    if hasattr(draw, 'textbbox'):
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (width - text_width) / 2
        text_y = (height - text_height) / 2 - text_bbox[1] # Adjust for the bbox's y offset
    else: # Fallback for older Pillow versions
        text_size = draw.textsize(text, font=font)
        text_width = text_size[0]
        text_height = text_size[1]
        text_x = (width - text_width) / 2
        text_y = (height - text_height) / 2


    # 5. Draw text onto the button shape
    draw.text((text_x, text_y), text, font=font, fill=text_color)

    # 6. Convert PIL Image to PhotoImage for Tkinter
    photo_image = ImageTk.PhotoImage(button_shape)

    return photo_image

if __name__ == '__main__':
    # Example usage for testing ui_utils.py directly
    root = tk.Tk()
    root.title("Rounded Button Test")
    root.geometry("400x300")

    # Test Data
    button_text = "Click Me"
    # Dimensions might need to be estimated or passed based on main app's button sizes
    # Tkinter button width is in text units, height in text lines.
    # For image buttons, pixel dimensions are better.
    # Let's assume a typical button size for now.
    # From main.py: width='15', pady='5', font=("Arial", 15, 'bold')
    # A width of 15 for Arial 15 bold is roughly 15 * (15 * 0.6) = 135px? pady adds to height.
    # Let's try a fixed pixel size first.
    btn_width_px = 150
    btn_height_px = 40
    radius_px = 10 # Slightly larger for testing visibility
    bg_c = '#abdbe3' # From main.py button_bg
    text_c = '#000000' # Black text
    font_n = "Arial"
    font_s = 15
    font_w = "bold"

    # Create the image
    try:
        img = create_rounded_button_image(
            button_text, btn_width_px, btn_height_px, radius_px,
            bg_c, text_c, font_name=font_n, font_size=font_s, font_weight=font_w
        )

        img_label = tk.Label(root, image=img, borderwidth=0)
        img_label.image = img # Keep a reference
        img_label.pack(pady=20)

        # Test with the gear icon '⚙'
        gear_img = create_rounded_button_image(
            '⚙', 50, 40, radius_px,
            bg_c, text_c, font_name=font_n, font_size=20, font_weight=font_w
        )
        gear_label = tk.Label(root, image=gear_img, borderwidth=0)
        gear_label.image = gear_img
        gear_label.pack(pady=10)

        # Test with a different color and radius
        img2 = create_rounded_button_image(
            "Another Button", 180, 50, 20,
            '#eab676', '#FFFFFF', font_name=font_n, font_size=16, font_weight="normal"
        )
        img_label2 = tk.Label(root, image=img2, borderwidth=0)
        img_label2.image = img2 # Keep a reference
        img_label2.pack(pady=20)


    except Exception as e:
        print(f"Error in example usage: {e}")
        error_label = tk.Label(root, text=f"Error: {e}")
        error_label.pack(pady=20)

    root.mainloop()
