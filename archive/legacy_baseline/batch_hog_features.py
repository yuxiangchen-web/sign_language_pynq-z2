from pathlib import Path
import cv2
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent
INPUT_DIR = PROJECT_DIR / "dataset" / "processed"
OUTPUT_DIR = PROJECT_DIR / "dataset" / "features"

CLASSES = ["palm", "fist", "victory", "ok", "thumbs_up", "unknown"]

hog = cv2.HOGDescriptor(
    (64, 64),   # 输入尺寸
    (16, 16),   # 区块尺寸
    (8, 8),     # 区块步长
    (8, 8),     # 单元格尺寸
    9           # 梯度方向
)

features = []
labels = []
paths = []

for label, class_name in enumerate(CLASSES):
    class_dir = INPUT_DIR / class_name
    files = sorted(class_dir.glob("*_mask.png"))

    print(f"[{class_name}] {len(files)} 张")

    for image_path in files:
        image = cv2.imread(
            str(image_path),
            cv2.IMREAD_GRAYSCALE
        )

        if image is None:
            print("读取失败：", image_path)
            continue

        image_64 = cv2.resize(
            image,
            (64, 64),
            interpolation=cv2.INTER_NEAREST
        )

        vector = hog.compute(image_64).flatten()

        features.append(vector)
        labels.append(label)
        paths.append(str(image_path))

if not features:
    raise RuntimeError("没有找到任何预处理图片")

X = np.asarray(features, dtype=np.float32)
y = np.asarray(labels, dtype=np.int32)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

np.savez(
    OUTPUT_DIR / "hog_dataset.npz",
    features=X,
    labels=y,
    paths=np.asarray(paths)
)

print("\nHOG 特征数据集生成完成")
print("特征矩阵形状：", X.shape)
print("标签形状：", y.shape)
print("保存位置：", OUTPUT_DIR / "hog_dataset.npz")