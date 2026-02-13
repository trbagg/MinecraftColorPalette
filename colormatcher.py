import re
import json
import colorsys
import tkinter as tk

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
    def __init__(self, root):
        self.root = root
        self.root.title("Color Box Display")
        self.root.geometry("800x940")
        tk.Label(root, text="Enter Hex Color:").pack(pady=10)
        self.input_entry = tk.Entry(root, width=20)

        self.entry_var = tk.StringVar()

        top_frame = tk.Frame(root)
        top_frame.pack(pady=10)

        self.input_entry = tk.Entry(top_frame, width=20, textvariable=self.entry_var)
        self.input_entry.pack(pady=5)
        self.input_entry.insert(0, "#CCCCCC")
        self.checkbox_var = tk.BooleanVar(value=False)
        self.checkbox = tk.Checkbutton(
            top_frame,
            text="Restrict to block palette",
            variable=self.checkbox_var,
            command=self.get_colors
        )
        self.checkbox.pack(side=tk.LEFT, padx=5)
        self.color_frame = tk.Frame(root)
        self.color_frame.pack(pady=20)
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
        box_sorting = [2,2,3,3,3,4,4]
        
        for j in box_sorting:
            row_frame = tk.Frame(self.color_frame)
            row_frame.pack(pady=6)

            for i in range(j):
                container = tk.Frame(row_frame, width=180, height=100)
                container.pack_propagate(False) 
                container.grid(row=0,column=i, padx=10)
                
                color_box = tk.Label(
                    container,
                    width=6,
                    height=3,
                    bg=self.colors[i],
                    relief=tk.RAISED,
                    borderwidth=2
                )

                color_box.pack()
                self.color_boxes.append(color_box)
                
                # Hex label
                hex_label = tk.Label(
                    container,
                    text=self.colors[i],
                    font=("Arial", 10, "bold")
                )
                hex_label.pack(pady=1)
                self.color_labels.append(hex_label)

                # Block name label
                block_label = tk.Label(
                    container,
                    text='N/A',
                    font=("Arial", 10, "bold"),
                    anchor='w'
                )
                block_label.pack(pady=1)
                self.block_labels.append(block_label)
                
        self.entry_var.trace_add('write', self.get_colors)

    def get_colors(self, *args):
        prim = hex_to_hls(self.entry_var.get())
        if prim is None:
            return
        colors = self.generate_palette(prim)
        block_names, block_colors = self.match_colors(colors)
        self.update_boxes(colors if self.checkbox_var.get() == False else block_colors,block_names)
    
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