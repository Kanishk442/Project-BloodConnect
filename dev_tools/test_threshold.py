# test_threshold.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from disease_detector import leukemia_detector

# Get model
model = leukemia_detector.model
if model is None:
    print("Model not loaded")
    sys.exit(1)

test_folder = r"D:\BloodConnect\backend\test_samples"
images = [f for f in os.listdir(test_folder) if f.endswith('.bmp')]

print("="*70)
print("TESTING WITH DIFFERENT THRESHOLDS")
print("="*70)

thresholds = [0.4, 0.45, 0.5, 0.55, 0.6, 0.65]

for img in sorted(images):
    img_path = os.path.join(test_folder, img)
    
    # Load and predict
    from PIL import Image
    import numpy as np
    
    img_pil = Image.open(img_path).convert('RGB')
    img_pil = img_pil.resize((224, 224))
    arr = np.expand_dims(np.array(img_pil) / 255.0, axis=0)
    
    pred = model.predict(arr, verbose=0)[0][0]
    
    expected = "LEUKEMIA" if 'leukemia' in img.lower() or 'all' in img.lower() else "NORMAL"
    
    print(f"\n{img}: Raw = {pred:.4f} (Expected: {expected})")
    print("  ", end="")
    
    for t in thresholds:
        result = "LEUKEMIA" if pred < t else "NORMAL"
        status = "✓" if result == expected else "✗"
        print(f"th={t}: {result} {status}  ", end="")
    print()