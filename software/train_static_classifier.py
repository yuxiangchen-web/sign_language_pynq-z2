from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms


DATA_ROOT = Path("dataset/processed_static_v1")
MODEL_PATH = Path("software/sign_classifier.pth")

transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
])

dataset = datasets.ImageFolder(DATA_ROOT, transform=transform)

train_size = int(0.8 * len(dataset))
test_size = len(dataset) - train_size
train_set, test_set = random_split(
    dataset,
    [train_size, test_size],
    generator=torch.Generator().manual_seed(42),
)

train_loader = DataLoader(train_set, batch_size=8, shuffle=True)
test_loader = DataLoader(test_set, batch_size=8)


class SmallCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 8, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(8, 16, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.classifier = nn.Linear(16, 5)

    def forward(self, x):
        x = self.features(x)
        return self.classifier(x.flatten(1))


device = "cpu"
model = SmallCNN().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.CrossEntropyLoss()

for epoch in range(20):
    model.train()

    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        loss = loss_fn(model(images), labels)
        loss.backward()
        optimizer.step()

    model.eval()
    correct = total = 0

    with torch.no_grad():
        for images, labels in test_loader:
            output = model(images)
            correct += (output.argmax(1) == labels).sum().item()
            total += labels.size(0)

    accuracy = correct / total if total else 0
    print(f"epoch {epoch + 1:02d}: accuracy={accuracy:.3f}")

torch.save(
    {
        "model_state": model.state_dict(),
        "classes": dataset.classes,
    },
    MODEL_PATH,
)

print(f"saved: {MODEL_PATH}")
print(f"classes: {dataset.classes}")