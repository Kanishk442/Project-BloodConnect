# test_all.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from disease_detector import leukemia_detector

print("="*60)
print("TESTING ALL IMAGES")
print("="*60)

if leukemia_detector.model is None:
    print("[ERROR] Model not loaded")
    sys.exit(1)

print(f"[OK] Model loaded\n")

test_folder = 'test_samples'
images = [f for f in os.listdir(test_folder) if f.endswith(('.bmp', '.jpg', '.png'))]

print(f"Found {len(images)} images\n")
print("-"*70)

for img_file in sorted(images):
    img_path = os.path.join(test_folder, img_file)
    result = leukemia_detector.predict(img_path)
    
    # Determine expected based on filename
    if 'leukemia' in img_file.lower() or 'all' in img_file.lower():
        expected = "LEUKEMIA"
    else:
        expected = "NORMAL"
    
    status = "✓" if expected == ("LEUKEMIA" if result['detected'] else "NORMAL") else "✗"
    
    print(f"{img_file[:30]:30} | Raw: {result.get('raw_prediction', 0):.4f} | {result['result'][:7]:7} | {result['confidence']:5.1f}% | {status}")

print("-"*70)
print("\n[INFO] Threshold used: >0.5 = NORMAL, <0.5 = LEUKEMIA")