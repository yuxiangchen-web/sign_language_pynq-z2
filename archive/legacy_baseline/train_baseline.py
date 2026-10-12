from pathlib import Path
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "dataset" / "features" / "hog_dataset.npz"
MODEL_DIR = PROJECT_DIR / "models"

CLASS_NAMES = [
    "palm",
    "fist",
    "victory",
    "ok",
    "thumbs_up",
    "unknown",
]

data = np.load(DATA_PATH, allow_pickle=True)
X = data["features"].astype(np.float32)
y = data["labels"].astype(np.int32)

if len(X) == 0:
    raise RuntimeError("特征数据为空")

# 每个特征向量做归一化
X_norm = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-8)

centroids = []
centroid_labels = []

for label in sorted(set(y.tolist())):
    class_features = X_norm[y == label]
    centroid = class_features.mean(axis=0)
    centroid = centroid / (np.linalg.norm(centroid) + 1e-8)

    centroids.append(centroid)
    centroid_labels.append(label)

centroids = np.asarray(centroids, dtype=np.float32)
centroid_labels = np.asarray(centroid_labels, dtype=np.int32)

# 用余弦相似度进行分类
scores = X_norm @ centroids.T
predicted_index = np.argmax(scores, axis=1)
predicted_labels = centroid_labels[predicted_index]

accuracy = np.mean(predicted_labels == y)

MODEL_DIR.mkdir(parents=True, exist_ok=True)

np.savez(
    MODEL_DIR / "prototype_model.npz",
    centroids=centroids,
    labels=centroid_labels,
    class_names=np.asarray(CLASS_NAMES)
)

print("基线分类器训练完成")
print("样本数：", len(X))
print("类别数：", len(centroids))
print("训练集回测准确率：", f"{accuracy * 100:.2f}%")
print("模型保存位置：", MODEL_DIR / "prototype_model.npz")

for true_label, pred_label in zip(y, predicted_labels):
    print(
        f"真实：{CLASS_NAMES[true_label]:10s}"
        f"预测：{CLASS_NAMES[pred_label]}"
    )