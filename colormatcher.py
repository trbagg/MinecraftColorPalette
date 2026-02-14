import re
import json
import colorsys
import math
import tkinter as tk
import tkinter.font as tkfont
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
    BASE_HEIGHT = 940
    ASPECT_RATIO = BASE_WIDTH / BASE_HEIGHT

    BASE_WHEEL_SIZE = 300
    BASE_WHEEL_PADDING = 10
    BASE_BOX_WIDTH = 180
    BASE_BOX_HEIGHT = 100
    BASE_LEGEND_ICON = 16
    BASE_LEGEND_SHAPE = 6

    BASE_FONT_LARGE = 10
    BASE_FONT_SMALL = 8

    BASE_MARKER_SIZE = 7
    BASE_PRIMARY_SIZE = 11
    BASE_MARKER_OUTLINE = 2
    BASE_PRIMARY_OUTLINE = 3
    BASE_LABEL_HALF_W = 30
    BASE_LABEL_HALF_H = 9
    BASE_LABEL_OFFSET = 22

    PALETTE_META = [
        {"name": "Complementary", "shape": "circle"},
        {"name": "Monochromatic", "shape": "square"},
        {"name": "Analogous", "shape": "triangle_up"},
        {"name": "Triadic", "shape": "triangle_down"},
        {"name": "Split Comp.", "shape": "diamond"},
        {"name": "Square", "shape": "pentagon"},
        {"name": "Rectangle", "shape": "hexagon"},
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("Color Box Display")
        self.root.geometry(f"{self.BASE_WIDTH}x{self.BASE_HEIGHT}")
        self.root.minsize(400, int(400 / self.ASPECT_RATIO))
        self.root.wm_aspect(self.BASE_WIDTH, self.BASE_HEIGHT,
                            self.BASE_WIDTH, self.BASE_HEIGHT)

        self._current_scale = 1.0
        self._resize_after_id = None
        self._last_palettes = None

        # Wheel state (mutable, updated on scale)
        self.wheel_radius = (self.BASE_WHEEL_SIZE - 2 * self.BASE_WHEEL_PADDING) // 2
        self.wheel_center = self.BASE_WHEEL_SIZE // 2

        # Named fonts (auto-propagate on .configure)
        self._font_large = tkfont.Font(family="Arial", size=self.BASE_FONT_LARGE, weight="bold")
        self._font_small = tkfont.Font(family="Arial", size=self.BASE_FONT_SMALL)
        self._font_small_bold = tkfont.Font(family="Arial", size=self.BASE_FONT_SMALL, weight="bold")

        # --- Input Section ---
        self._input_label = tk.Label(root, text="Enter Hex Color:", font=self._font_large)
        self._input_label.pack(pady=10)
        self.entry_var = tk.StringVar()

        self._top_frame = tk.Frame(root)
        self._top_frame.pack(pady=10)

        self.input_entry = tk.Entry(self._top_frame, width=20, textvariable=self.entry_var,
                                    font=self._font_large)
        self.input_entry.pack(pady=5)
        self.input_entry.insert(0, "#CCCCCC")
        self.checkbox_var = tk.BooleanVar(value=False)
        self.checkbox = tk.Checkbutton(
            self._top_frame,
            text="Restrict to block palette",
            variable=self.checkbox_var,
            command=self.get_colors,
            font=self._font_small
        )
        self.checkbox.pack(side=tk.LEFT, padx=5)

        # --- Main Content (wheel left, boxes right) ---
        self._content_frame = tk.Frame(root)
        self._content_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        self._content_frame.grid_rowconfigure(0, weight=1)
        self._content_frame.grid_columnconfigure(0, weight=0)
        self._content_frame.grid_columnconfigure(1, weight=1)

        # Left frame: wheel + legend, vertically centered
        self._left_frame = tk.Frame(self._content_frame)
        self._left_frame.grid(row=0, column=0, padx=10)

        self._init_wheel(self._left_frame)
        self._init_legend(self._left_frame)

        # Right frame: color boxes, centered and evenly spaced
        self.color_frame = tk.Frame(self._content_frame)
        self.color_frame.grid(row=0, column=1, padx=10)
        self.colors = [
            "#CCCCCC",
            "#CCCCCC",
            "#CCCCCC",
            "#CCCCCC",
            "#CCCCCC"
        ]

        # Create 21 color boxes
        self.color_boxes = []
        self.color_labels = []
        self.block_labels = []
        self._box_containers = []
        self._row_frames = []
        box_sorting = [2,2,3,3,3,4,4]

        for j in box_sorting:
            row_frame = tk.Frame(self.color_frame)
            row_frame.pack(pady=6)
            self._row_frames.append(row_frame)

            for i in range(j):
                container = tk.Frame(row_frame, width=self.BASE_BOX_WIDTH,
                                     height=self.BASE_BOX_HEIGHT)
                container.pack_propagate(False)
                container.grid(row=0,column=i, padx=10)
                self._box_containers.append(container)

                color_box = tk.Label(
                    container,
                    width=6,
                    height=3,
                    bg=self.colors[i],
                    relief=tk.RAISED,
                    borderwidth=2,
                    font=self._font_large
                )

                color_box.pack()
                self.color_boxes.append(color_box)

                # Hex label
                hex_label = tk.Label(
                    container,
                    text=self.colors[i],
                    font=self._font_large
                )
                hex_label.pack(pady=1)
                self.color_labels.append(hex_label)

                # Block name label
                block_label = tk.Label(
                    container,
                    text='N/A',
                    font=self._font_large,
                    anchor='w'
                )
                block_label.pack(pady=1)
                self.block_labels.append(block_label)

        self.entry_var.trace_add('write', self.get_colors)
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
        box_padx = max(1, int(10 * scale))
        for container in self._box_containers:
            container.configure(width=box_w, height=box_h)
            container.grid_configure(padx=box_padx)

        # 3. Row padding
        row_pady = max(1, int(6 * scale))
        for row_frame in self._row_frames:
            row_frame.pack_configure(pady=row_pady)

        # 4. Wheel canvas
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

        # 5. Legend icons
        icon_size = max(6, int(self.BASE_LEGEND_ICON * scale))
        shape_size = max(2, int(self.BASE_LEGEND_SHAPE * scale))
        cx = icon_size / 2
        for i, (item_frame, mini_canvas) in enumerate(self._legend_items):
            mini_canvas.configure(width=icon_size, height=icon_size)
            mini_canvas.delete("all")
            self._draw_shape(
                mini_canvas, cx, cx,
                self.PALETTE_META[i]["shape"], "#888888",
                size=shape_size, outline="black",
                width=max(1, int(scale)), tag="legend"
            )

        # 6. Paddings
        p5 = max(1, int(5 * scale))
        p10 = max(1, int(10 * scale))
        self._input_label.pack_configure(pady=p10)
        self._top_frame.pack_configure(pady=p10)
        self.input_entry.pack_configure(pady=p5)
        self.checkbox.pack_configure(padx=p5)
        self._content_frame.pack_configure(padx=p10)
        self._left_frame.grid_configure(padx=p10)
        self.color_frame.grid_configure(padx=p10)
        self._wheel_frame.pack_configure(pady=p5)
        self._legend_outer.pack_configure(pady=p5)
        for item_frame, mini_canvas in self._legend_items:
            item_frame.pack_configure(pady=max(1, int(1 * scale)))
            mini_canvas.pack_configure(padx=max(1, int(2 * scale)))
        for label in self.color_labels:
            label.pack_configure(pady=max(1, int(1 * scale)))
        for label in self.block_labels:
            label.pack_configure(pady=max(1, int(1 * scale)))

        # 7. Redraw wheel markers
        if self._last_palettes is not None:
            self._update_wheel_markers(self._last_palettes)

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

    def _draw_shape(self, canvas, x, y, shape, fill_color, size=7,
                    outline="white", width=2, tag="marker"):
        s = size
        if shape == "circle":
            canvas.create_oval(
                x - s, y - s, x + s, y + s,
                fill=fill_color, outline=outline, width=width, tags=tag
            )
        elif shape == "square":
            canvas.create_rectangle(
                x - s, y - s, x + s, y + s,
                fill=fill_color, outline=outline, width=width, tags=tag
            )
        elif shape == "triangle_up":
            pts = [x, y - s, x - s, y + s, x + s, y + s]
            canvas.create_polygon(
                pts, fill=fill_color, outline=outline, width=width, tags=tag
            )
        elif shape == "triangle_down":
            pts = [x, y + s, x - s, y - s, x + s, y - s]
            canvas.create_polygon(
                pts, fill=fill_color, outline=outline, width=width, tags=tag
            )
        elif shape == "diamond":
            pts = [x, y - s, x + s, y, x, y + s, x - s, y]
            canvas.create_polygon(
                pts, fill=fill_color, outline=outline, width=width, tags=tag
            )
        elif shape == "pentagon":
            pts = []
            for i in range(5):
                a = math.pi / 2 + i * 2 * math.pi / 5
                pts.extend([x + s * math.cos(a), y - s * math.sin(a)])
            canvas.create_polygon(
                pts, fill=fill_color, outline=outline, width=width, tags=tag
            )
        elif shape == "hexagon":
            pts = []
            for i in range(6):
                a = i * 2 * math.pi / 6
                pts.extend([x + s * math.cos(a), y - s * math.sin(a)])
            canvas.create_polygon(
                pts, fill=fill_color, outline=outline, width=width, tags=tag
            )

    def _update_wheel_markers(self, palettes):
        self._last_palettes = palettes

        self.wheel_canvas.delete("marker")
        self.wheel_canvas.delete("primary_marker")
        self.wheel_canvas.delete("primary_label")

        scale = self._current_scale
        marker_size = max(2, int(self.BASE_MARKER_SIZE * scale))
        marker_outline = max(1, int(self.BASE_MARKER_OUTLINE * scale))
        primary_size = max(3, int(self.BASE_PRIMARY_SIZE * scale))
        primary_outline = max(1, int(self.BASE_PRIMARY_OUTLINE * scale))
        label_half_w = max(10, int(self.BASE_LABEL_HALF_W * scale))
        label_half_h = max(4, int(self.BASE_LABEL_HALF_H * scale))
        label_offset = max(8, int(self.BASE_LABEL_OFFSET * scale))
        wheel_size = self.wheel_center * 2

        primary_hls = palettes[0][0]

        for i, palette in enumerate(palettes):
            shape = self.PALETTE_META[i]["shape"]
            for hls in palette:
                h, l, s = hls
                x, y = self._hls_to_wheel_xy(h, l, s)
                fill = self.hls_to_hex(hls)
                self._draw_shape(
                    self.wheel_canvas, x, y, shape, fill,
                    size=marker_size, outline="white",
                    width=marker_outline, tag="marker"
                )

        # Primary input color: larger marker drawn on top
        px, py = self._hls_to_wheel_xy(*primary_hls)
        primary_hex = self.hls_to_hex(primary_hls)
        self._draw_shape(
            self.wheel_canvas, px, py, "circle", primary_hex,
            size=primary_size, outline="white",
            width=primary_outline, tag="primary_marker"
        )

        # Hex label near the primary cursor
        label_y = py + label_offset if py < self.wheel_center else py - label_offset
        clamp_y = max(4, int(12 * scale))
        clamp_x = label_half_w + 2
        label_y = max(clamp_y, min(wheel_size - clamp_y, label_y))
        label_x = max(clamp_x, min(wheel_size - clamp_x, px))

        self.wheel_canvas.create_rectangle(
            label_x - label_half_w, label_y - label_half_h,
            label_x + label_half_w, label_y + label_half_h,
            fill="white", outline="#666666", width=1, tags="primary_label"
        )
        self.wheel_canvas.create_text(
            label_x, label_y, text=primary_hex,
            font=self._font_small_bold, fill="black", tags="primary_label"
        )

    # ---- Legend ----

    def _init_legend(self, parent):
        self._legend_outer = tk.Frame(parent)
        self._legend_outer.pack(pady=5)

        self._legend_items = []

        for i in range(len(self.PALETTE_META)):
            self._add_legend_item(self._legend_outer, i)

    def _add_legend_item(self, parent, index):
        meta = self.PALETTE_META[index]
        item = tk.Frame(parent)
        item.pack(anchor="w", pady=1)

        mini = tk.Canvas(item, width=self.BASE_LEGEND_ICON,
                         height=self.BASE_LEGEND_ICON, highlightthickness=0)
        mini.pack(side=tk.LEFT, padx=2)
        self._draw_shape(
            mini, self.BASE_LEGEND_ICON // 2, self.BASE_LEGEND_ICON // 2,
            meta["shape"], "#888888",
            size=self.BASE_LEGEND_SHAPE, outline="black", width=1, tag="legend"
        )

        tk.Label(item, text=meta["name"], font=self._font_small).pack(side=tk.LEFT)

        self._legend_items.append((item, mini))

    # ---- Palette Logic ----

    def get_colors(self, *args):
        prim = hex_to_hls(self.entry_var.get())
        if prim is None:
            return
        colors = self.generate_palette(prim)
        block_names, block_colors = self.match_colors(colors)
        use_blocks = self.checkbox_var.get()
        self.update_boxes(colors if not use_blocks else block_colors, block_names)
        self._update_wheel_markers(colors if not use_blocks else block_colors)

    def match_colors(self, palettes):
        global block_color_data

        block_color_palettes = []
        block_name_palettes = []

        for palette in palettes:
            block_colors = []
            block_names = []
            for target_color in palette:
                h1,l1,s1 = target_color
                min_dist = float('inf')
                for block_name in block_color_data:
                    h2,l2,s2 = block_color_data[block_name]
                    hue_diff = min(abs(h1 - h2), 1 - abs(h1 - h2))
                    light_weight = 0.25
                    distance = (hue_diff**2 + ((l1 - l2)**2 * light_weight) + (s1 - s2)**2) ** 0.5

                    if distance < min_dist:
                        min_dist = distance
                        nearest_block = block_name
                block_names.append(nearest_block)
                block_colors.append(block_color_data[nearest_block])
            block_color_palettes.append(block_colors)
            block_name_palettes.append(block_names)

        return block_name_palettes, block_color_palettes

    def generate_palette(self, hls):
        h, l, s = hls
        palettes = [
        [
            hls,
            ((h + 0.5) % 1, l, s),  # Complementary (2)
        ],
        [
            hls,
            (h, min(l+0.1,1.0), s),  # Monochromatic (2)
        ],
        [
            ((h - 0.0833) % 1, l, s),  # Analogous (3)
            hls,
            ((h + 0.0833) % 1, l, s)
        ],
        [
            ((h + 0.333) % 1, l, s),  # Triadic (3)
            hls,
            ((h + 0.666) % 1, l, s)
        ],
        [
            ((h + (1.0-0.0833)) % 1, l, s),  # Split Complementary (3)
            hls,
            ((h - (1.0-0.0833)) % 1, l, s)
        ],
        [
            hls,
            ((h + 0.25) % 1, l, s),  # Square (4)
            ((h + 0.50) % 1, l, s),
            ((h + 0.75) % 1, l, s)
        ],
        [
            hls,
            ((h + (0.0833 * 2)) % 1, l, s),  # Rectange (4)
            ((h + (0.0833 * 6)) % 1, l, s),
            ((h + (0.0833 * 8)) % 1, l, s)
        ]]
        return palettes

    def update_boxes(self, palettes, block_names):
        merged_list = sum([sublist for sublist in palettes], [])
        block_list = sum([sublist for sublist in block_names], [])
        for i, hls in enumerate(merged_list):
            hex_color = self.hls_to_hex(hls)
            block_name = block_list[i]
            self.color_boxes[i].config(bg=hex_color)
            self.color_labels[i].config(text=hex_color)
            self.block_labels[i].config(text=block_name)

    def hls_to_hex(self, hls):
        r, g, b = colorsys.hls_to_rgb(hls[0],hls[1],hls[2])
        r = round(r*255)
        g = round(g*255)
        b = round(b*255)

        return '#%02x%02x%02x' % (r, g, b)


if __name__ == '__main__':
    root = tk.Tk()
    app = ColorBoxApp(root)
    root.mainloop()
