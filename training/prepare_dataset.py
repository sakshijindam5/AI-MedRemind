"""
Dataset Preparation and Cleaning Script for Smart Crop Disease Detector
- Verifies and filters corrupted images
- Ensures all images are 3-channel RGB (removes RGBA/Grayscale artifacts)
- Stratified 70-15-15 split into Train, Validation, and Test folders
- Calculates class weights for handling class imbalance in PyTorch CrossEntropyLoss
"""

import os
import shutil
import random
from pathlib import Path
from PIL import Image
import json

# Set random seed for reproducible train/val/test splits
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

def verify_and_clean_image(image_path: Path) -> bool:
    """
    Checks if an image file is valid, readable, and can be converted to RGB.
    Returns True if valid, False if corrupted.
    """
    try:
        with Image.open(image_path) as img:
            # Verify internal integrity
            img.verify()
            
        # Re-open for actual conversion test (verify() closes file pointer)
        with Image.open(image_path) as img:
            # Convert to RGB (handles RGBA PNGs or CMYK images)
            rgb_img = img.convert("RGB")
            # Filter out microscopic thumbnails (< 64x64) that degrade training
            if rgb_img.width < 64 or rgb_img.height < 64:
                return False
        return True
    except Exception:
        return False

def prepare_dataset_splits(
    raw_data_dir: str = "dataset_raw",
    output_dir: str = "dataset_split",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15
):
    """
    Splits raw crop disease folders into train/, val/, test/ subdirectories.
    """
    raw_path = Path(raw_data_dir)
    out_path = Path(output_dir)
    
    if not raw_path.exists():
        print(f"[!] Error: Raw data directory '{raw_data_dir}' not found.")
        print("    Please place your downloaded crop folders inside 'dataset_raw/' first.")
        return

    # Identify class folders
    classes = [d.name for d in raw_path.iterdir() if d.is_dir()]
    print(f"[*] Found {len(classes)} classes: {classes}\n")

    splits = ['train', 'val', 'test']
    for s in splits:
        for c in classes:
            (out_path / s / c).mkdir(parents=True, exist_ok=True)

    class_counts = {}
    corrupted_count = 0

    for class_name in classes:
        class_folder = raw_path / class_name
        valid_images = []
        
        # Scan and verify all image files
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.PNG"):
            for img_file in class_folder.glob(ext):
                if verify_and_clean_image(img_file):
                    valid_images.append(img_file)
                else:
                    corrupted_count += 1
                    print(f"[-] Removed corrupted or unreadable image: {img_file.name}")

        # Shuffle deterministically
        random.shuffle(valid_images)
        total = len(valid_images)
        class_counts[class_name] = total

        if total == 0:
            print(f"[!] Warning: Class '{class_name}' has 0 valid images. Skipping.")
            continue

        n_train = int(total * train_ratio)
        n_val = int(total * val_ratio)
        # Test gets the remainder to avoid rounding leaks
        train_imgs = valid_images[:n_train]
        val_imgs = valid_images[n_train:n_train + n_val]
        test_imgs = valid_images[n_train + n_val:]

        print(f"Class '{class_name}': Total {total} -> Train: {len(train_imgs)}, Val: {len(val_imgs)}, Test: {len(test_imgs)}")

        # Copy images to respective folders
        for img in train_imgs:
            shutil.copy2(img, out_path / 'train' / class_name / img.name)
        for img in val_imgs:
            shutil.copy2(img, out_path / 'val' / class_name / img.name)
        for img in test_imgs:
            shutil.copy2(img, out_path / 'test' / class_name / img.name)

    print("\n---------------------------------------------------------")
    print(f"[*] Split complete. Corrupted files skipped: {corrupted_count}")
    print("---------------------------------------------------------")
    
    # Calculate inverse frequency class weights to balance CrossEntropyLoss
    max_count = max(class_counts.values()) if class_counts else 1
    class_weights = {}
    for c, count in class_counts.items():
        # Inverse weight: heavier penalty for under-represented classes
        weight = round(max_count / max(count, 1), 4)
        class_weights[c] = weight

    weights_file = Path("training/class_weights.json")
    with open(weights_file, "w", encoding="utf-8") as f:
        json.dump(class_weights, f, indent=2)

    print(f"[*] Class weights saved to {weights_file.as_posix()}:")
    for c, w in class_weights.items():
        print(f"    - {c}: {w} (Sample count: {class_counts[c]})")

if __name__ == "__main__":
    prepare_dataset_splits()
