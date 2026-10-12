from pathlib import Path
import cv2
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "dataset/features/hog_dataset.npz"

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

# 每个类别分别划分，约 75% 训练、25% 测试
rng = np.random.default_rng(42)
train_indices = []
test_indices = []

for label in range(len(CLASS_NAMES)):
    indices = np.where(y == label)[0]
    rng.shuffle(indices)

    test_count = max(2, round(len(indices) * 0.25))
    test_count = min(test_count, len(indices) - 1)

    test_indices.extend(indices[:test_count])
    train_indices.extend(indices[test_count:])

train_indices = np.asarray(train_indices)
test_indices = np.asarray(test_indices)

X_train = X[train_indices]
y_train = y[train_indices]
X_test = X[test_indices]
y_test = y[test_indices]

# HOG 特征归一化
X_train /= np.linalg.norm(X_train, axis=1, keepdims=True) + 1e-8
X_test /= np.linalg.norm(X_test, axis=1, keepdims=True) + 1e-8

# 线性支持向量机
svm = cv2.ml.SVM_create()
svm.setType(cv2.ml.SVM_C_SVC)
svm.setKernel(cv2.ml.SVM_LINEAR)
svm.setC(1.0)

svm.train(X_train, cv2.ml.ROW_SAMPLE, y_train)

_, prediction = svm.predict(X_test)
y_pred = prediction.flatten().astype(np.int32)

accuracy = np.mean(y_pred == y_test)

confusion = np.zeros(
    (len(CLASS_NAMES), len(CLASS_NAMES)),
    dtype=np.int32
)

for true_label, predicted_label in zip(y_test, y_pred):
    confusion[true_label, predicted_label] += 1

print("初步独立测试完成")
print("训练样本数：", len(y_train))
print("测试样本数：", len(y_test))
print("测试准确率：", f"{accuracy * 100:.2f}%")

print("\n混淆矩阵")
print("行=真实类别，列=预测类别")
print("类别顺序：", CLASS_NAMES)
print(confusion)

print("\n逐张测试结果")
for true_label, predicted_label in zip(y_test, y_pred):
    result = "正确" if true_label == predicted_label else "错误"
    print(
        f"真实={CLASS_NAMES[true_label]:10s} "
        f"预测={CLASS_NAMES[predicted_label]:10s} "
        f"{result}"
    )