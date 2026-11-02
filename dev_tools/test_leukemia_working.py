# test_leukemia_working.py
import tensorflow as tf
import numpy as np
from PIL import Image
import os

print("="*60)
print("LEUKEMIA DETECTOR TEST")
print("="*60)

# Import the detector
from disease_detector import leukemia_detector

if leukemia_detector.model is None:
    print("❌ Model not loaded")
    exit(1)

print("✅ Model loaded successfully")

# Test with images in test_samples folder
test_folder = 'test_samples'
if not os.path.exists(test_folder):
    print(f"\n⚠️ Test folder not found: {test_folder}")
    exit(1)

images = [f for f in os.listdir(test_folder) if f.endswith(('.bmp', '.jpg', '.png'))]
print(f"\n📁 Found {len(images)} test images")
print("="*60)

for img_file in sorted(images):
    img_path = os.path.join(test_folder, img_file)
    result = leukemia_detector.predict(img_path)
    
    print(f"\n📷 {img_file}")
    print(f"   Raw Score: {result.get('raw_prediction', 0):.4f}")
    print(f"   Result: {'⚠️ LEUKEMIA' if result['detected'] else '✅ NORMAL'}")
    print(f"   Confidence: {result['confidence']:.1f}%")
    print(f"   Message: {result['message']}")