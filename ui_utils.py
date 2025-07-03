import tkinter as tk
from PIL import Image, ImageDraw, ImageTk, ImageFont
import os # For font path if needed

# Define a global default font path or a way to find fonts if needed.

def get_font_path(font_name, font_weight="normal"):
    """
    Tries to find a font file path.
    This is a basic implementation. For robust cross-platform font finding,
    a library like `matplotlib.font_manager` could be used, or bundle fonts.
    """
    font_name_lower = font_name.lower()
    system_fonts = {
        "windows": {
            "arial": {
                "normal": "arial.ttf",
                "bold": "arialbd.ttf"
            },
            "tahoma": { # Tahoma is good for UI and Unicode
                "normal": "tahoma.ttf",
                "bold": "tahomabd.ttf"
            }
        },
        "linux": { # Common on Linux systems with fontconfig
            "dejavusans": {
                "normal": "DejaVuSans.ttf",
                "bold": "DejaVuSans-Bold.ttf"
            },
            "arial" : { # Often symlinked or available
                 "normal": "arial.ttf",
                 "bold": "arialbd.ttf"
            }
        },
        "darwin": { # macOS
            "arial": {
                "normal": "Arial.ttf", # Case sensitive on macOS sometimes
                "bold": "Arial Bold.ttf"
            },
            "helveticaneue": {
                "normal": "HelveticaNeue.ttc", # .ttc can contain multiple fonts
                "bold": "HelveticaNeue-Bold.ttc" # Or specific variant
            }
        }
    }

    import sys
    platform = sys.platform
    if platform.startswith("win"):
        os_fonts = system_fonts["windows"]
    elif platform.startswith("linux"):
        os_fonts = system_fonts["linux"]
    elif platform.startswith("darwin"):
        os_fonts = system_fonts["darwin"]
    else:
        os_fonts = {} # Unknown OS

    font_family = os_fonts.get(font_name_lower)
    if font_family:
        return font_family.get(font_weight, font_family.get("normal"))

    # Fallback to just the name if not in our simple map
    if font_weight == "bold":
        if font_name_lower.endswith(".ttf"):
            return font_name.replace(".ttf", "bd.ttf") # Simple guess
        return font_name # Or let Pillow try to find "FontName Bold"
    return font_name


DEFAULT_FONT_NAME = "Arial" # Preferred
FALLBACK_FONT_NAME = "DejaVuSans" # Good Unicode coverage, common on Linux
GENERIC_FALLBACK_FONT_NAME = "Tahoma" # Good Unicode coverage, common on Windows

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
    # 3. Load font
    font_loaded = False
    if text == '⚙': # Prioritize symbol fonts for the gear character
        symbol_fonts_to_try = ["Segoe UI Symbol", "Symbola", "Noto Sans Symbols", "DejaVu Sans"]
        for symbol_font_name in symbol_fonts_to_try:
            try:
                # We don't typically specify weight for symbol fonts, assume 'normal'
                symbol_font_path = get_font_path(symbol_font_name, "normal")
                font = ImageFont.truetype(symbol_font_path, font_size, layout_engine=ImageFont.LAYOUT_RAQM)
                if font.getmask(text).getbbox(): # Check if '⚙' is actually in this font
                    font_loaded = True
                    # print(f"Successfully loaded symbol font '{symbol_font_name}' for '⚙'")
                    break
                # else:
                    # print(f"Symbol font '{symbol_font_name}' found but does not contain '⚙'.")
            except IOError:
                # print(f"Symbol font '{symbol_font_name}' not found. Trying next.")
                pass
        if not font_loaded:
            print(f"Warning: Could not find a dedicated symbol font for '⚙'. Will try standard fonts.")

    if not font_loaded:
        font_to_try = font_name if font_name else DEFAULT_FONT_NAME
        font_path = get_font_path(font_to_try, font_weight)
        try:
            font = ImageFont.truetype(font_path, font_size, layout_engine=ImageFont.LAYOUT_RAQM)
            if text == '⚙' and not font.getmask(text).getbbox():
                 raise IOError(f"Font '{font_path}' does not support '⚙' character.")
            font_loaded = True
        except IOError:
            # print(f"Warning: Font '{font_path}' not found or unsuitable. Trying fallbacks.")
            fallback_path = get_font_path(GENERIC_FALLBACK_FONT_NAME, font_weight)
            try:
                font = ImageFont.truetype(fallback_path, font_size, layout_engine=ImageFont.LAYOUT_RAQM)
                if text == '⚙' and not font.getmask(text).getbbox():
                    raise IOError(f"Fallback font {GENERIC_FALLBACK_FONT_NAME} also does not support '⚙'.")
                font_loaded = True
            except IOError:
                fallback_path_2 = get_font_path(FALLBACK_FONT_NAME, font_weight)
                try:
                    font = ImageFont.truetype(fallback_path_2, font_size, layout_engine=ImageFont.LAYOUT_RAQM)
                    if text == '⚙' and not font.getmask(text).getbbox():
                        raise IOError(f"Fallback font {FALLBACK_FONT_NAME} also does not support '⚙'.")
                    font_loaded = True
                except IOError:
                    print(f"Warning: All specified and fallback fonts not found or unsuitable for '{text}'. Using Pillow's default font.")
                    font = ImageFont.load_default() # This is the most likely cause of tofu for '⚙'
                    # No font_loaded = True here, as default font might not support '⚙'

    # 4. Calculate text position for centering
    # Use textbbox for more accurate positioning
    try:
        # Anchor 'ms' (middle baseline) for vertical, then adjust x for horizontal.
        # For draw.text, (x,y) is the top-left corner of the text bounding box by default.
        # Using textlength for width and textbbox for height and precise centering.

        text_left, text_top, text_right, text_bottom = font.getbbox(text)
        text_actual_width = text_right - text_left
        text_actual_height = text_bottom - text_top # Height of the drawing area for the glyph

        # For horizontal centering:
        text_x = (width - text_actual_width) / 2 - text_left

        # For vertical centering:
        # text_y = (height - text_actual_height) / 2 - text_top
        # A common heuristic for vertical centering that often looks better:
        text_y = (height - (font.getmetrics()[0] + font.getmetrics()[1])) / 2 + (font.getmetrics()[1] * 0.5) # Heuristic for better perceived vertical center
        # Or, more simply using the bbox:
        text_y = (height / 2) - ((text_top + text_bottom) / 2)


    except AttributeError: # Fallback if getbbox or other methods are not available (older Pillow?)
        # This path should ideally not be taken with modern Pillow.
        text_width, text_height = draw.textsize(text, font=font) # Deprecated
        text_x = (width - text_width) / 2
        text_y = (height - text_height) / 2

    # 5. Draw text onto the button shape
    # Ensure text color is in a format PIL understands (e.g. #RRGGBB)
    draw.text((text_x, text_y), text, font=font, fill=text_color) # Removed anchor, using calculated x,y

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
