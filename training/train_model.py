"""
Smart Crop Disease Detector - PyTorch Model Training Script
Architecture: MobileNetV2 with Transfer Learning
Google Colab Ready & Local Laptop Compatible
"""

import os
import json
import time
import copy
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix

# ---------------------------------------------------------------------------
# 1. Hyperparameters and Configuration
# ---------------------------------------------------------------------------
DATA_DIR = Path("dataset_split")      # Path containing train/, val/, test/ folders
MODEL_SAVE_PATH = Path("weights/crop_mobilenetv2_best.pth")
TORCHSCRIPT_SAVE_PATH = Path("weights/crop_mobilenetv2_scripted.pt")
CLASS_NAMES_FILE = Path("training/class_names.json")
CLASS_WEIGHTS_FILE = Path("training/class_weights.json")

BATCH_SIZE = 32                       # Use 16 if training on low-memory laptop GPU
NUM_EPOCHS = 15                       # 15 epochs is optimal for fine-tuning
LEARNING_RATE = 0.0003                # Smooth learning rate for fine-tuning
IMG_SIZE = 224                        # Standard MobileNetV2 input resolution
RANDOM_SEED = 42

# Ensure reproducibility
torch.manual_seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(RANDOM_SEED)

# Device selection: Auto-detect GPU (Colab T4 / Laptop NVIDIA) or fallback to CPU
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f"[*] Training Device: {device}")
if device.type == "cuda":
    print(f"[*] GPU Name: {torch.cuda.get_device_name(0)}")


# ---------------------------------------------------------------------------
# 2. Data Augmentation & Preprocessing
# ---------------------------------------------------------------------------
# ImageNet normalization stats (required for pre-trained PyTorch models)
NORMALIZE_MEAN = [0.485, 0.456, 0.406]
NORMALIZE_STD = [0.229, 0.224, 0.225]

data_transforms = {
    'train': transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        # Random flips and rotations mimic leaves taken from different angles in the field
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.2),
        transforms.RandomRotation(degrees=25),
        # Color jitter simulates different sunlight conditions (bright midday vs evening)
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(NORMALIZE_MEAN, NORMALIZE_STD)
    ]),
    'val': transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(NORMALIZE_MEAN, NORMALIZE_STD)
    ]),
    'test': transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(NORMALIZE_MEAN, NORMALIZE_STD)
    ]),
}


# ---------------------------------------------------------------------------
# 3. Dataset Loading
# ---------------------------------------------------------------------------
def load_data(data_dir: Path):
    """Loads train, val, and test datasets using torchvision ImageFolder."""
    image_datasets = {
        x: datasets.ImageFolder(data_dir / x, transform=data_transforms[x])
        for x in ['train', 'val', 'test']
    }
    
    dataloaders = {
        x: DataLoader(
            image_datasets[x],
            batch_size=BATCH_SIZE,
            shuffle=(x == 'train'),
            num_workers=2 if os.name != 'nt' else 0, # Windows uses 0 workers for safety
            pin_memory=torch.cuda.is_available()
        )
        for x in ['train', 'val', 'test']
    }
    
    dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val', 'test']}
    class_names = image_datasets['train'].classes
    
    print(f"[*] Total Samples: Train={dataset_sizes['train']}, Val={dataset_sizes['val']}, Test={dataset_sizes['test']}")
    print(f"[*] Detected {len(class_names)} classes: {class_names}")
    
    # Save the exact order of class names so the FastAPI backend matches predictions
    CLASS_NAMES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CLASS_NAMES_FILE, 'w', encoding='utf-8') as f:
        json.dump(class_names, f, indent=2)
    print(f"[*] Saved class labels mapping to {CLASS_NAMES_FILE}")
    
    return dataloaders, dataset_sizes, class_names


# ---------------------------------------------------------------------------
# 4. Model Architecture: MobileNetV2 with Transfer Learning
# ---------------------------------------------------------------------------
def build_model(num_classes: int):
    """
    Downloads MobileNetV2 pretrained on ImageNet (1000 general classes),
    freezes bottom layers to retain edge/texture feature extraction,
    and replaces the final classification head for our 12 crop classes.
    """
    print("[*] Loading pretrained MobileNetV2 weights...")
    weights = models.MobileNet_V2_Weights.DEFAULT
    model = models.mobilenet_v2(weights=weights)
    
    # Freeze the base feature extractor layers to prevent catastrophic forgetting
    for param in model.features.parameters():
        param.requires_grad = False
        
    # Unfreeze the last convolutional inverted residual block for fine-tuning
    for param in model.features[-2:].parameters():
        param.requires_grad = True

    # Replace the final linear classification layer
    in_features = model.classifier[1].in_features  # 1280
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),                         # Prevents overfitting
        nn.Linear(in_features, num_classes)
    )
    
    return model.to(device)


# ---------------------------------------------------------------------------
# 5. Model Training Function
# ---------------------------------------------------------------------------
def train_model(model, dataloaders, dataset_sizes, class_names, num_epochs=NUM_EPOCHS):
    """Trains the model and keeps the checkpoint with the highest validation accuracy."""
    
    # Setup loss function with class imbalance weights if available
    if CLASS_WEIGHTS_FILE.exists():
        with open(CLASS_WEIGHTS_FILE, 'r', encoding='utf-8') as f:
            weights_dict = json.load(f)
        weight_list = [weights_dict.get(cls_name, 1.0) for cls_name in class_names]
        weights_tensor = torch.tensor(weight_list, dtype=torch.float).to(device)
        criterion = nn.CrossEntropyLoss(weight=weights_tensor)
        print("[*] Using class-weighted CrossEntropyLoss for imbalance mitigation.")
    else:
        criterion = nn.CrossEntropyLoss()
        print("[*] Using standard CrossEntropyLoss.")

    # Adam optimizer on trainable parameters only
    optimizer = optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=LEARNING_RATE,
        weight_decay=1e-4
    )
    
    # Learning rate scheduler: decay LR by 0.5 every 5 epochs
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    since = time.time()
    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    train_loss_history = []
    val_loss_history = []
    train_acc_history = []
    val_acc_history = []

    print("\n" + "="*50)
    print("        Starting Model Training Pipeline")
    print("="*50)

    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch + 1}/{num_epochs}")
        print("-" * 25)

        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()  # Enable dropout and batchnorm training
            else:
                model.eval()   # Disable dropout for evaluation

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                # Forward pass: track gradients only in train phase
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    # Backward pass + optimize only in training phase
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            if phase == 'train':
                scheduler.step()

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = (running_corrects.double() / dataset_sizes[phase]).item()

            print(f"{phase.capitalize()} Loss: {epoch_loss:.4f} | Acc: {epoch_acc * 100:.2f}%")

            if phase == 'train':
                train_loss_history.append(epoch_loss)
                train_acc_history.append(epoch_acc)
            else:
                val_loss_history.append(epoch_loss)
                val_acc_history.append(epoch_acc)

                # Save best checkpoint
                if epoch_acc > best_acc:
                    best_acc = epoch_acc
                    best_model_wts = copy.deepcopy(model.state_dict())
                    MODEL_SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
                    torch.save(best_model_wts, MODEL_SAVE_PATH)
                    print(f"[*] New best validation accuracy: {best_acc * 100:.2f}%! Saved model.")

    time_elapsed = time.time() - since
    print("\n" + "="*50)
    print(f"Training completed in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s")
    print(f"Best Validation Accuracy: {best_acc * 100:.2f}%")
    print("="*50)

    # Load best model weights before returning
    model.load_state_dict(best_model_wts)
    
    # Export to TorchScript format (portable, faster, runs without class architecture code)
    try:
        model.eval()
        example_input = torch.rand(1, 3, IMG_SIZE, IMG_SIZE).to(device)
        traced_script_module = torch.jit.trace(model, example_input)
        traced_script_module.save(TORCHSCRIPT_SAVE_PATH)
        print(f"[*] Exported optimized TorchScript model to: {TORCHSCRIPT_SAVE_PATH}")
    except Exception as e:
        print(f"[!] Warning: Could not trace TorchScript model: {e}")

    # Plot training metrics
    plot_training_curves(train_loss_history, val_loss_history, train_acc_history, val_acc_history)

    return model


# ---------------------------------------------------------------------------
# 6. Evaluation on Unseen Test Set
# ---------------------------------------------------------------------------
def evaluate_model(model, dataloader, dataset_size, class_names):
    """
    Evaluates final model performance on the untouched test set.
    Generates:
      1. Overall test accuracy
      2. Per-class precision, recall, and F1-score
      3. Confusion matrix heatmap saved as confusion_matrix.png
    """
    model.eval()
    all_preds = []
    all_labels = []

    print("\n[*] Evaluating on Test Set...")
    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)

            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    test_accuracy = np.mean(all_preds == all_labels)
    print(f"\n=======================================================")
    print(f"   FINAL TEST SET ACCURACY: {test_accuracy * 100:.2f}%")
    print(f"=======================================================\n")

    # Classification Report (Precision, Recall, F1)
    report = classification_report(all_labels, all_preds, target_names=class_names, digits=4)
    print("Classification Report:\n")
    print(report)

    # Save report to text file for your MCA viva documentation
    with open("training/evaluation_report.txt", "w", encoding="utf-8") as f:
        f.write(f"Test Accuracy: {test_accuracy * 100:.2f}%\n\n")
        f.write(report)
    print("[*] Saved evaluation report to training/evaluation_report.txt")

    # Confusion Matrix Plot
    cm = confusion_matrix(all_labels, all_preds)
    plot_confusion_matrix(cm, class_names)


def plot_training_curves(train_loss, val_loss, train_acc, val_acc):
    """Plots loss and accuracy curves and saves as training_curves.png"""
    plt.figure(figsize=(12, 5))

    # Loss Curve
    plt.subplot(1, 2, 1)
    plt.plot(train_loss, label='Train Loss', color='#10b981', linewidth=2)
    plt.plot(val_loss, label='Val Loss', color='#ef4444', linewidth=2)
    plt.title('Training & Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)

    # Accuracy Curve
    plt.subplot(1, 2, 2)
    plt.plot([a * 100 for a in train_acc], label='Train Acc', color='#10b981', linewidth=2)
    plt.plot([a * 100 for a in val_acc], label='Val Acc', color='#3b82f6', linewidth=2)
    plt.title('Training & Validation Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig('training/training_curves.png', dpi=300)
    plt.close()
    print("[*] Saved training loss/acc curves to training/training_curves.png")


def plot_confusion_matrix(cm, class_names):
    """Plots and saves the confusion matrix heatmap."""
    plt.figure(figsize=(10, 8))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Greens)
    plt.title('Crop Disease Confusion Matrix')
    plt.colorbar()

    tick_marks = np.arange(len(class_names))
    # Abbreviate class names for clean display on axis
    short_names = [name.replace("___", "\n") for name in class_names]
    plt.xticks(tick_marks, short_names, rotation=45, ha='right', fontsize=8)
    plt.yticks(tick_marks, short_names, fontsize=8)

    # Normalize matrix to show percentages on cell labels
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], 'd'),
                     ha="center", va="center",
                     color="white" if cm[i, j] > thresh else "black",
                     fontsize=9)

    plt.ylabel('True Disease Label')
    plt.xlabel('Predicted Disease Label')
    plt.tight_layout()
    plt.savefig('training/confusion_matrix.png', dpi=300)
    plt.close()
    print("[*] Saved confusion matrix to training/confusion_matrix.png")


# ---------------------------------------------------------------------------
# 7. Main Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if not DATA_DIR.exists():
        print(f"[!] Directory '{DATA_DIR}' does not exist.")
        print("    Run 'python training/prepare_dataset.py' after populating dataset_raw/ first.")
    else:
        dataloaders, dataset_sizes, class_names = load_data(DATA_DIR)
        model = build_model(len(class_names))
        trained_model = train_model(model, dataloaders, dataset_sizes, class_names, num_epochs=NUM_EPOCHS)
        evaluate_model(trained_model, dataloaders['test'], dataset_sizes['test'], class_names)
