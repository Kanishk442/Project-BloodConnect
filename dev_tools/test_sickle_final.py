# test_sickle_final.py
from disease_detector import sickle_cell_detector
import os

print("="*50)
print("SICKLE CELL DETECTOR FINAL TEST")
print("="*50)

if not sickle_cell_detector.model:
    print("Model not loaded!")
    exit(1)

print(f"[OK] Model loaded")
print(f"Threshold: {sickle_cell_detector.threshold}")

# Test with a sample image if available
test_images = []
test_folder = 'test_samples'

if os.path.exists(test_folder):
    for f in os.listdir(test_folder):
        if f.endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            test_images.append(os.path.join(test_folder, f))

if test_images:
    print(f"\nTesting {len(test_images)} images:")
    for img in test_images[:5]:
        result = sickle_cell_detector.predict(img)
        print(f"\n{os.path.basename(img)}:")
        print(f"  Raw: {result['raw_prediction']:.4f}")
        print(f"  Result: {'SICKLE CELL' if result['detected'] else 'NORMAL'}")
        print(f"  Confidence: {result['confidence']:.1f}%")
else:
    print("\nNo test images found. Please add images to test_samples folder")