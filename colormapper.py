import os
import json
from PIL import Image

image_paths = []
data = {}

folder_dir = "D:\\Python Projects\\MinecraftColorPalette\\block"
for image in os.listdir(folder_dir):
    if (image.endswith(".png")):
        image_paths.append(image)

for image_path in image_paths:
    img = Image.open(os.path.join(folder_dir, image_path)).convert('RGBA')
    if img.size != (16,16) or img.info.get("transparency", None) is not None or img.getextrema()[3][0] < 255:
        continue
    img = img.convert('RGB')
    img = img.resize((2,2), Image.Resampling.LANCZOS)

    pixels = list(img.getdata())
    
    avg_r = sum(p[0] for p in pixels) / len(pixels)
    avg_g = sum(p[1] for p in pixels) / len(pixels)
    avg_b = sum(p[2] for p in pixels) / len(pixels)

    data[image_path[:-4]] = '#%02x%02x%02x' % (round(avg_r), round(avg_g), round(avg_b))


with open('colormap.json', 'w') as f:
    json.dump(data, f, indent=4)