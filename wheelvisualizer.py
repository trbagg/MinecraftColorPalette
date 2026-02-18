import re
import json
import math
import colorsys
import tkinter as tk
import tkinter.font as tkfont
from functools import partial
from PIL import Image, ImageTk


def hex_to_hls(hex_color):
    if len(hex_color) == 0:
        return

    if hex_color[0] == '#':
        hex_color = hex_color[1:]

    if len(hex_color) != 6:
        return

    pattern = re.compile(r"^[0-9a-fA-F]{6}$")
    match = pattern.match(hex_color)
    if not match:
        return

    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0

    h, l, s = colorsys.rgb_to_hls(r, g, b)

    return h, l, s

with open('colormap.json', 'r') as f:
    data = json.load(f)
    block_color_data = {}
    for hex_val in data:
        block_color_data[hex_val] = hex_to_hls(data[hex_val])

class ColorBoxApp:
    # --- Base dimensions (reference at scale 1.0) ---
    BASE_WIDTH = 1200
    BASE_HEIGHT = 700
    ASPECT_RATIO = BASE_WIDTH / BASE_HEIGHT

    BASE_WHEEL_SIZE = 300
    BASE_WHEEL_PADDING = 10
    BASE_BOX_WIDTH = 180
    BASE_BOX_HEIGHT = 100

    BASE_FONT_LARGE = 10
    BASE_FONT_SMALL = 8

    BASE_MARKER_SIZE = 7
    BASE_MARKER_OUTLINE = 2
    BASE_LABEL_HALF_W = 30
    BASE_LABEL_HALF_H = 9
    BASE_LABEL_OFFSET = 22

    MAX_COLORS = 5

    def __init__(self, root):
        self.root = root
        self.root.title("Color Wheel Display")
        self.root.geometry(f"{self.BASE_WIDTH}x{self.BASE_HEIGHT}")
        self.root.minsize(400, int(400 / self.ASPECT_RATIO))
        self.root.wm_aspect(self.BASE_WIDTH, self.BASE_HEIGHT,
                            self.BASE_WIDTH, self.BASE_HEIGHT)

        self._current_scale = 1.0
        self._resize_after_id = None
        self._last_colors = None

        # Wheel state (mutable, updated on scale)
        self.wheel_radius = (self.BASE_WHEEL_SIZE - 2 * self.BASE_WHEEL_PADDING) // 2
        self.wheel_center = self.BASE_WHEEL_SIZE // 2

        # Named fonts (auto-propagate on .configure)
        self._font_large = tkfont.Font(family="Arial", size=self.BASE_FONT_LARGE, weight="bold")
        self._font_small = tkfont.Font(family="Arial", size=self.BASE_FONT_SMALL)
        self._font_small_bold = tkfont.Font(family="Arial", size=self.BASE_FONT_SMALL, weight="bold")

        # --- Input Section ---
        self._input_label = tk.Label(root, text="Enter Hex Colors (up to 5):", font=self._font_large)
        self._input_label.pack(pady=10)
        
        self._top_frame = tk.Frame(root)
        self._top_frame.pack(pady=10)

        # Create 5 entry fields
        self.entry_vars = []
        self.input_entries = []
        default_colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF"]
        
        for i in range(self.MAX_COLORS):
            entry_var = tk.StringVar()
            entry = tk.Entry(self._top_frame, width=12, textvariable=entry_var,
                           font=self._font_large)
            entry.grid(row=0, column=i, padx=5)
            entry.insert(0, default_colors[i])
            entry_var.trace_add('write', partial(self.get_colors_main,i))
            self.entry_vars.append(entry_var)
            self.input_entries.append(entry)

        # Control buttons
        self._control_frame = tk.Frame(root)
        self._control_frame.pack(pady=5)

        # --- Main Content (wheel left, boxes right) ---
        self._content_frame = tk.Frame(root)
        self._content_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        self._content_frame.grid_rowconfigure(0, weight=1)
        self._content_frame.grid_columnconfigure(0, weight=0)
        self._content_frame.grid_columnconfigure(1, weight=1)

        # Left frame: wheel
        self._left_frame = tk.Frame(self._content_frame)
        self._left_frame.grid(row=0, column=0, padx=10)

        self._init_wheel(self._left_frame)

        # Right frame: color boxes
        self.color_frame = tk.Frame(self._content_frame)
        self.color_frame.grid(row=0, column=1, padx=10)
        self.colors = []

        # Create color boxes
        self.color_boxes = []
        self.color_labels = []
        self.block_labels = []
        self._box_containers = []
        self.lightness_vars = []
        self.lightness_entries = []

        for i in range(self.MAX_COLORS):
            container = tk.Frame(self.color_frame, width=self.BASE_BOX_WIDTH,
                                 height=self.BASE_BOX_HEIGHT)
            container.pack_propagate(False)
            container.pack(pady=10)
            self._box_containers.append(container)

            container.grid_columnconfigure(0, weight=0)
            container.grid_columnconfigure(1, weight=0)
            container.grid_columnconfigure(2, weight=1)

            color_box = tk.Button(
                container,
                width=6,
                height=3,
                bg="#CCCCCC",
                relief=tk.RAISED,
                borderwidth=2,
                font=self._font_large
            )
            color_box.grid(row=0, column=0, padx=5)
            self.color_boxes.append(color_box)

            lightness_var = tk.DoubleVar()
            lightness_entry = tk.Scale(container, width=10, length=100, variable=lightness_var, font=self._font_large, orient="horizontal", command=self.get_colors)
            
            lightness_entry.grid(row=0, column=1, padx=5, sticky='e')

            #lightness_var.trace_add('write', self.get_colors)
            self.lightness_vars.append(lightness_var)
            self.lightness_entries.append(lightness_entry)

            # Block name label
            block_label = tk.Label(
                container,
                text='N/A',
                font=self._font_large,
                width=16
            )
            block_label.grid(row=1, column=0, padx=1)
            self.block_labels.append(block_label)

        self.get_colors()

        # Bind resize after all widgets exist
        self.root.after_idle(lambda: self.root.bind('<Configure>', self._on_resize))

    # ---- Resize Handling ----

    def _on_resize(self, event):
        if event.widget is not self.root:
            return

        w = event.width
        h = event.height

        # Enforce aspect ratio
        expected_h = round(w / self.ASPECT_RATIO)
        if abs(expected_h - h) > 2:
            self.root.geometry(f"{w}x{expected_h}")
            return

        # Compute scale
        scale = w / self.BASE_WIDTH
        if abs(scale - self._current_scale) < 0.005:
            return

        # Debounce
        if self._resize_after_id is not None:
            self.root.after_cancel(self._resize_after_id)
        self._resize_after_id = self.root.after(50, self._apply_scale, scale)

    def _apply_scale(self, scale):
        self._current_scale = scale
        self._resize_after_id = None

        # 1. Fonts (auto-propagates to all widgets)
        self._font_large.configure(size=max(1, int(self.BASE_FONT_LARGE * scale)))
        self._font_small.configure(size=max(1, int(self.BASE_FONT_SMALL * scale)))
        self._font_small_bold.configure(size=max(1, int(self.BASE_FONT_SMALL * scale)))

        # 2. Box containers
        box_w = max(40, int(self.BASE_BOX_WIDTH * scale))
        box_h = max(25, int(self.BASE_BOX_HEIGHT * scale))
        for container in self._box_containers:
            container.configure(width=box_w, height=box_h)
            container.pack_configure(pady=max(1, int(10 * scale)))

        # 3. Wheel canvas
        self.wheel_center = max(40, int(self.BASE_WHEEL_SIZE * scale)) // 2
        self.wheel_radius = max(20, (self.wheel_center * 2 -
                                     2 * max(1, int(self.BASE_WHEEL_PADDING * scale))) // 2)
        wheel_size = self.wheel_center * 2
        self.wheel_canvas.configure(width=wheel_size, height=wheel_size)
        self._generate_wheel_image()
        self.wheel_canvas.delete("all")
        self.wheel_canvas.create_image(
            self.wheel_center, self.wheel_center,
            image=self.wheel_photo, tags="wheel"
        )
        self.wheel_canvas.create_oval(
            self.wheel_center - self.wheel_radius - 1,
            self.wheel_center - self.wheel_radius - 1,
            self.wheel_center + self.wheel_radius + 1,
            self.wheel_center + self.wheel_radius + 1,
            outline="#888888", width=1, tags="wheel_border"
        )

        # 4. Paddings
        p5 = max(1, int(5 * scale))
        p10 = max(1, int(10 * scale))
        self._input_label.pack_configure(pady=p10)
        self._top_frame.pack_configure(pady=p10)
        self._control_frame.pack_configure(pady=p5)
        self.clear_button.pack_configure(padx=p5)
        self._content_frame.pack_configure(padx=p10)
        self._left_frame.grid_configure(padx=p10)
        self.color_frame.grid_configure(padx=p10)
        self._wheel_frame.pack_configure(pady=p5)
        
        for entry in self.input_entries:
            entry.grid_configure(padx=p5)
        
        for label in self.color_labels:
            label.pack_configure(pady=max(1, int(1 * scale)))
        for label in self.block_labels:
            label.pack_configure(pady=max(1, int(1 * scale)))

        # 5. Redraw wheel markers
        if self._last_colors is not None:
            self._update_wheel_markers(self._last_colors)

    # ---- Color Wheel ----

    def _init_wheel(self, parent):
        self._wheel_frame = tk.Frame(parent)
        self._wheel_frame.pack(pady=5)

        self.wheel_canvas = tk.Canvas(
            self._wheel_frame,
            width=self.BASE_WHEEL_SIZE, height=self.BASE_WHEEL_SIZE,
            highlightthickness=0
        )
        self.wheel_canvas.pack()

        self._generate_wheel_image()
        self.wheel_canvas.create_image(
            self.wheel_center, self.wheel_center,
            image=self.wheel_photo, tags="wheel"
        )
        self.wheel_canvas.create_oval(
            self.wheel_center - self.wheel_radius - 1,
            self.wheel_center - self.wheel_radius - 1,
            self.wheel_center + self.wheel_radius + 1,
            self.wheel_center + self.wheel_radius + 1,
            outline="#888888", width=1, tags="wheel_border"
        )

    def _generate_wheel_image(self):
        size = self.wheel_center * 2
        center = self.wheel_center
        radius = self.wheel_radius

        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        pixels = img.load()

        for x in range(size):
            for y in range(size):
                dx = x - center
                dy = y - center
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= radius:
                    hue = (math.atan2(-dy, dx) / (2 * math.pi)) % 1.0
                    sat = dist / radius
                    r, g, b = colorsys.hls_to_rgb(hue, 0.5, sat)
                    alpha = 255
                    if dist > radius - 1.5:
                        alpha = max(0, min(255, int(255 * (radius - dist + 1.5))))
                    pixels[x, y] = (int(r * 255), int(g * 255), int(b * 255), alpha)

        self.wheel_image = img
        self.wheel_photo = ImageTk.PhotoImage(img)

    def _hls_to_wheel_xy(self, h, l, s):
        angle = h * 2 * math.pi
        dist = s * self.wheel_radius
        x = self.wheel_center + dist * math.cos(angle)
        y = self.wheel_center - dist * math.sin(angle)
        return x, y

    def _update_wheel_markers(self, colors):
        self._last_colors = colors

        self.wheel_canvas.delete("marker")
        self.wheel_canvas.delete("marker_label")

        scale = self._current_scale
        marker_size = max(3, int(self.BASE_MARKER_SIZE * scale))
        marker_outline = max(1, int(self.BASE_MARKER_OUTLINE * scale))

        for i, hls in enumerate(colors):
            if hls is None:
                continue
                
            h, l, s = hls
            x, y = self._hls_to_wheel_xy(h, l, s)
            hex_color = self.hls_to_hex(hls)
            
            # Draw marker
            self.wheel_canvas.create_oval(
                x - marker_size, y - marker_size,
                x + marker_size, y + marker_size,
                fill=hex_color, outline="white",
                width=marker_outline, tags="marker"
            )

    # ---- Color Logic ----

    def init_colors(self, master = False):
        input_colors = []
        if master is False:
            for i, entry_var in enumerate(self.entry_vars):
                hls = hex_to_hls(entry_var.get())
                if hls is None:
                    continue
                h,l,s = hls
                lightness = self.lightness_vars[i].get()
                input_colors.append((h, min(1,lightness/100.0), s))
        else:
            for i, entry_var in enumerate(self.entry_vars):
                hls = hex_to_hls(entry_var.get())
                if hls is None:
                    continue
                input_colors.append(hls)
        return input_colors

    def get_colors_main(self, *args):

        self.colors = self.init_colors(master=True)
        
        if len(self.colors) != 5:
            return

        i = args[0]

        self.lightness_vars[i].set(self.colors[i][1] * 100)
            
        self.get_colors()

    def get_colors(self, *args):
        
        self.colors = self.init_colors()
        
        # Match to blocks
        block_names = []
        
        for hls in self.colors:
            if hls is None:
                block_names.append("N/A")
            else:
                name = self.match_color(hls)
                block_names.append(name)
        
        # Use block colors if checkbox is selected
        display_colors = self.colors
        
        self.update_boxes(display_colors, block_names)
        self._update_wheel_markers(display_colors)

    def match_color(self, target_hls):
        if target_hls is None:
            return "N/A", None
            
        h1, l1, s1 = target_hls
        min_dist = float('inf')
        nearest_block = "N/A"
        
        for block_name in block_color_data:
            h2, l2, s2 = block_color_data[block_name]
            hue_diff = min(abs(h1 - h2), 1 - abs(h1 - h2))
            light_weight = 0.25
            distance = (hue_diff**2 + ((l1 - l2)**2 * light_weight) + (s1 - s2)**2) ** 0.5

            if distance < min_dist:
                min_dist = distance
                nearest_block = block_name
        
        return nearest_block

    def update_boxes(self, colors, block_names):
        for i in range(self.MAX_COLORS):
            if i < len(colors) and colors[i] is not None:
                hex_color = self.hls_to_hex(colors[i])
                block_name = block_names[i]
                self.color_boxes[i].config(bg=hex_color)
                #self.lightness_entries[i].delete(0, tk.END)
                #h,l,s = hex_to_hls(hex_color)
                #self.lightness_entries[i].insert(tk.END, l)
                self.block_labels[i].config(text=block_name)
            else:
                self.color_boxes[i].config(bg="#CCCCCC")
                self.block_labels[i].config(text="N/A")

    def hls_to_hex(self, hls):
        r, g, b = colorsys.hls_to_rgb(hls[0], hls[1], hls[2])
        r = round(r * 255)
        g = round(g * 255)
        b = round(b * 255)
        return '#%02x%02x%02x' % (r, g, b)


if __name__ == '__main__':
    root = tk.Tk()
    app = ColorBoxApp(root)
    root.mainloop()