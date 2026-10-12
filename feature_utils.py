"""HOG 特征参数与提取（静态/动态共用，B 负责）。"""

import numpy as np
from skimage.feature import hog

HOG_PARAMS = dict(
    orientations=9,
    pixels_per_cell=(16, 16),
    cells_per_block=(2, 2),
    block_norm="L2-Hys",
    feature_vector=True,
)


def hog_feature(binary_128):
    """对 128x128 二值图提取 HOG，返回一维 float32 向量。"""
    img = np.asarray(binary_128, dtype=np.uint8)
    if img.shape != (128, 128):
        raise ValueError(f"HOG 输入必须是 128x128，当前 {img.shape}")
    return hog(img / 255.0, **HOG_PARAMS).astype(np.float32)
