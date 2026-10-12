import json
from pathlib import Path
import numpy as np
from PIL import Image

root = Path(__file__).resolve().parents[1]
sample = next(iter(sorted((root / 'dataset/raw_static_v1').glob('*/*.jpg'))))
dest = root / 'fpga/hls/test_vectors'
dest.mkdir(parents=True, exist_ok=True)
rgb = np.asarray(Image.open(sample).convert('RGB').resize((360, 360)), dtype=np.uint8)
r, g, b = (rgb[..., i].astype(np.int32) for i in range(3))
y = np.clip((77*r + 150*g + 29*b) >> 8, 0, 255)
cr = np.clip(((131*r - 110*g - 21*b) >> 8) + 128, 0, 255)
cb = np.clip(((-43*r - 85*g + 128*b) >> 8) + 128, 0, 255)
mask = (y >= 45) & (y <= 225) & (cr >= 135) & (cr <= 190) & (cb >= 80) & (cb <= 145)
pad = np.pad(mask.astype(np.uint8), 1)
count = sum(pad[dy:dy+360, dx:dx+360].astype(np.int32) for dy in range(3) for dx in range(3))
np.savetxt(dest / 'input_rgb.txt', rgb.reshape(-1, 3), fmt='%d')
for mode, binary in enumerate((mask, count >= 5)):
    image = binary.astype(np.uint8)*255
    np.savetxt(dest / f'expected_{mode}.txt', image.ravel(), fmt='%d')
    Image.fromarray(image).save(dest / f'expected_{mode}.png')
(dest / 'source.json').write_text(json.dumps({'source': str(sample), 'pixels': 129600}, indent=2), encoding='utf-8')
print(dest)
