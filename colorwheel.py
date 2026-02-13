import tkinter as tk
from tkinter import ttk
import math
import colorsys
from PIL import Image, ImageDraw, ImageTk

class ColorWheel:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Color Plotter")
        self.root.geometry("500x600") # Adjusted geometry for the new layout
        
        # Rotation offset (in radians) - π/2 puts red at top
        self.hue_rotation = math.pi / 2
        
        # --- Color wheel properties (unchanged) ---
        self.wheel_size = 300
        self.canvas_size = 340
        self.wheel_radius = self.wheel_size // 2
        self.padding = (self.canvas_size - self.wheel_size) // 2
        self.center_x = self.canvas_size // 2
        self.center_y = self.canvas_size // 2
        
        # --- NEW: Data structure for 5 colors ---
        # We'll store the HSV data for each of the 5 possible colors
        # A value of None means the slot is empty.
        self.colors = [None] * 5
        
        # --- NEW: UI element lists ---
        self.hex_vars = []
        self.color_previews = []
        
        self.setup_ui()
        self.create_color_wheel()
        self.initialize_entries() # Initialize with some default colors
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Canvas for color wheel (binding removed as clicking is no longer the primary input)
        self.canvas = tk.Canvas(main_frame, width=self.canvas_size, height=self.canvas_size, bg='white')
        self.canvas.grid(row=0, column=0, pady=(0, 20))
        
        # --- NEW: Frame for all color inputs ---
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Create 5 rows of inputs
        for i in range(5):
            # Color Preview Box
            preview = tk.Frame(input_frame, width=30, height=30, relief=tk.RAISED, borderwidth=2, bg="#f0f0f0")
            preview.grid(row=i, column=0, padx=(0, 10), pady=4)
            self.color_previews.append(preview)
            
            # Label
            ttk.Label(input_frame, text=f"Color {i+1}:").grid(row=i, column=1, padx=(0, 5))
            
            # Hex Entry
            hex_var = tk.StringVar()
            entry = ttk.Entry(input_frame, textvariable=hex_var, width=12, font=("Courier", 10))
            entry.grid(row=i, column=2)
            
            # Bind the event to a function that knows WHICH entry was changed
            entry.bind('<Return>', lambda event, index=i: self.on_hex_change(index))
            entry.bind('<FocusOut>', lambda event, index=i: self.on_hex_change(index))
            
            self.hex_vars.append(hex_var)

    def create_color_wheel(self):
        # This function creates the background wheel image.
        # It now only needs to run once at the start.
        image = Image.new('RGB', (self.wheel_size, self.wheel_size), 'white')
        draw = ImageDraw.Draw(image)
        wheel_center = self.wheel_size // 2
        
        for y in range(self.wheel_size):
            for x in range(self.wheel_size):
                dx, dy = x - wheel_center, y - wheel_center
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance <= self.wheel_radius:
                    angle = math.atan2(dy, dx)
                    hue = (angle + math.pi + self.hue_rotation) / (2 * math.pi)
                    saturation = min(distance / self.wheel_radius, 1.0)
                    r, g, b = colorsys.hsv_to_rgb(hue, saturation, 1.0) # Always full value
                    color = (int(r * 255), int(g * 255), int(b * 255))
                    draw.point((x, y), color)
        
        self.wheel_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(self.padding, self.padding, anchor=tk.NW, image=self.wheel_image, tags="wheel")

    def draw_all_cursors(self):
        """NEW: Clears and draws all cursors based on the self.colors list."""
        self.canvas.delete("cursor")
        
        cursor_styles = [
            {'fill': '#FFFFFF', 'outline': '#000000'},
            {'fill': '#FFD700', 'outline': '#A0522D'},
            {'fill': '#ADFF2F', 'outline': '#006400'},
            {'fill': '#87CEEB', 'outline': '#00008B'},
            {'fill': '#EE82EE', 'outline': '#8B008B'}
        ]
        
        for i, color_data in enumerate(self.colors):
            if color_data: # Only draw if the color data exists
                h, s, v = color_data['h'], color_data['s'], color_data['v']
                
                # Calculate cursor position from HSV
                angle = h * 2 * math.pi - math.pi - self.hue_rotation
                distance = s * self.wheel_radius
                x = self.center_x + distance * math.cos(angle)
                y = self.center_y + distance * math.sin(angle)
                
                # Draw cursor with unique style
                style = cursor_styles[i]
                radius = 6
                self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                                    fill=style['fill'], outline=style['outline'], width=2, tags="cursor")
                # Draw number inside cursor
                self.canvas.create_text(x, y, text=str(i+1), font=("Arial", 8, "bold"), tags="cursor")

    def on_hex_change(self, index):
        """NEW: Triggered when a hex entry is updated."""
        hex_color = self.hex_vars[index].get().strip()
        
        if not hex_color.startswith('#'):
            hex_color = '#' + hex_color
        
        try:
            if len(hex_color) == 7:
                r = int(hex_color[1:3], 16) / 255.0
                g = int(hex_color[3:5], 16) / 255.0
                b = int(hex_color[5:7], 16) / 255.0
                h, s, v = colorsys.rgb_to_hsv(r, g, b)
                
                # Store the valid color data
                self.colors[index] = {'h': h, 's': s, 'v': v}
                self.color_previews[index].config(bg=hex_color)
            else:
                # If hex is invalid or cleared, remove the data
                self.colors[index] = None
                self.color_previews[index].config(bg="#f0f0f0")

        except ValueError:
            # Handle invalid characters in hex code
            self.colors[index] = None
            self.color_previews[index].config(bg="#f0f0f0")
            
        # Redraw all cursors with the updated information
        self.draw_all_cursors()

    def initialize_entries(self):
        """Helper to pre-fill some entries for demonstration."""
        initial_colors = ["#ff0000", "#00ff00", "#0000ff"]
        for i, color in enumerate(initial_colors):
            self.hex_vars[i].set(color)
            self.on_hex_change(i) # Trigger the update to plot them

if __name__ == "__main__":
    root = tk.Tk()
    app = ColorWheel(root)
    root.mainloop()