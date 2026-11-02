# test_single_image.py
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from disease_detector import leukemia_detector

print("="*60)
print("SINGLE IMAGE LEUKEMIA TEST")
print("="*60)

# Check if model loaded
if leukemia_detector.model is None:
    print("[ERROR] Model not loaded")
    sys.exit(1)

print(f"[OK] Model loaded - Input: {leukemia_detector.model.input_shape}")

# Test with a leukemia image
image_path = "test_samples/leukemia_1.bmp"

if not os.path.exists(image_path):
    print(f"\n[ERROR] Image not found: {image_path}")
    print("\nAvailable images:")
    for f in os.listdir('test_samples'):
        print(f"  - {f}")
    sys.exit(1)

print(f"\n[INFO] Testing image: {image_path}")

result = leukemia_detector.predict(image_path)

print(f"\n[RESULT]")
print(f"  Raw Score: {result.get('raw_prediction', 0):.4f}")
print(f"  Result: {'LEUKEMIA' if result['detected'] else 'NORMAL'}")
print(f"  Confidence: {result['confidence']:.1f}%")
print(f"  Message: {result['message']}")