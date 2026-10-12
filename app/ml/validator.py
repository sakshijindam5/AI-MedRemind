"""
Leaf & Vegetation Validator
Prevents non-leaf images (shoes, walls, cars, faces, random objects)
from reaching the deep learning model.
"""

from PIL import Image
import numpy as np

def is_valid_leaf_image(pil_image: Image.Image, min_vegetation_ratio: float = 0.12) -> tuple[bool, str]:
    """
    Analyzes an uploaded image to verify if it contains crop/foliage characteristics.
    
    Returns:
        (is_valid: bool, reason: str)
    """
    try:
        # Resize to thumbnail for ultra-fast validation (<10ms)
        img_thumb = pil_image.copy().convert("RGB").resize((128, 128))
        img_arr = np.array(img_thumb, dtype=np.float32)

        r = img_arr[:, :, 0]
        g = img_arr[:, :, 1]
        b = img_arr[:, :, 2]

        # 1. Excess Green Index (ExG = 2*G - R - B)
        # Identifies green chlorophyll foliage
        exg = 2.0 * g - r - b
        green_pixels = (exg > 15) & (g > 35)

        # 2. Plant Necrosis / Blight / Dried Leaf Index
        # Brown/yellow diseased spots on leaves have high R and G, low B (R > B + 20 and G > B + 10)
        brown_yellow_pixels = (r > (b + 25)) & (g > (b + 10)) & (r > 60) & (g > 50) & (b < 140)

        # Total pixels matching plant tissue (healthy green OR diseased brown/yellow)
        plant_mask = green_pixels | brown_yellow_pixels
        total_pixels = 128 * 128
        vegetation_ratio = float(np.sum(plant_mask) / total_pixels)

        # Check: Low vegetation presence
        if vegetation_ratio < min_vegetation_ratio:
            return False, f"Non-leaf image detected ({vegetation_ratio * 100:.1f}% plant pixels). Please capture a close-up photo of the crop leaf."

        # Check: Pure black or pure white over-exposure
        mean_brightness = float(np.mean(img_arr))
        if mean_brightness < 20:
            return False, "Photo is too dark/underexposed. Please take a photo in better lighting."
        if mean_brightness > 245:
            return False, "Photo is overexposed/too bright. Please take a photo without direct flash."

        return True, "Valid leaf image."

    except Exception as e:
        # Graceful fallback: allow image if validation crashes
        return True, f"Validation passed with warning: {e}"
