from pathlib import Path
import cv2
import numpy as np

project_dir = Path(__file__).resolve().parent
mask_path = project_dir / "outputs/skin_test/hand_mask_128.png"

mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
if mask is None:
    raise FileNotFoundError(f"无法读取：{mask_path}")

# HOG 使用 64×64 输入，降低后续计算量
mask_64 = cv2.resize(
    mask,
    (64, 64),
    interpolation=cv2.INTER_NEAREST
)

hog = cv2.HOGDescriptor(
    (64, 64),   # 输入尺寸
    (16, 16),   # 区块尺寸
    (8, 8),     # 区块移动步长
    (8, 8),     # 单元格尺寸
    9           # 梯度方向数量
)

features = hog.compute(mask_64).flatten()

output_dir = project_dir / "outputs/hog_test"
output_dir.mkdir(parents=True, exist_ok=True)

cv2.imwrite(str(output_dir / "hog_input_64.png"), mask_64)
np.save(str(output_dir / "palm_002_hog.npy"), features)

print("HOG 特征提取成功")
print("特征数量：", len(features))
print("前 10 个特征：", features[:10])