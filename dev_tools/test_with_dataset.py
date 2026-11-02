# find_optimal_threshold.py
import tensorflow as tf
import os
import numpy as np
from PIL import Image
from sklearn.metrics import accuracy_score

print("="*60)
print("FINDING OPTIMAL THRESHOLD")
print("="*60)

# Load model
model = tf.keras.models.load_model('models/sickle_cell_pretrained.h5', compile=False)
print("[OK] Model loaded")

# Get all images
sickle_path = r"D:\BloodConnect\sickle\Positive\Labelled"
normal_path = r"D:\BloodConnect\sickle\Negative\Clear"

sickle_images = []
normal_images = []

if os.path.exists(sickle_path):
    sickle_images = [os.path.join(sickle_path, f) for f in os.listdir(sickle_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
if os.path.exists(normal_path):
    normal_images = [os.path.join(normal_path, f) for f in os.listdir(normal_path) if f.endswith(('.jpg', '.jpeg', '.png'))]

print(f"Sickle images: {len(sickle_images)}")
print(f"Normal images: {len(normal_images)}")

# Predict all images
def predict_image(image_path):
    img = Image.open(image_path).convert('RGB')
    img = img.resize((128, 128))
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return float(model.predict(img_array, verbose=0)[0][0])

print("\nPredicting...")
sickle_scores = [predict_image(img) for img in sickle_images]
normal_scores = [predict_image(img) for img in normal_images]

# Try different thresholds
thresholds = [0.70, 0.72, 0.74, 0.75, 0.76, 0.78, 0.80, 0.82, 0.85]

print("\n" + "="*60)
print("THRESHOLD ANALYSIS")
print("="*60)

best_threshold = None
best_accuracy = 0

for th in thresholds:
    # Calculate accuracy
    sickle_correct = sum(1 for s in sickle_scores if s > th)
    normal_correct = sum(1 for n in normal_scores if n <= th)
    
    sickle_acc = sickle_correct / len(sickle_scores) * 100
    normal_acc = normal_correct / len(normal_scores) * 100
    total_acc = (sickle_correct + normal_correct) / (len(sickle_scores) + len(normal_scores)) * 100
    
    print(f"\nThreshold: {th:.2f}")
    print(f"  Sickle detection: {sickle_correct}/{len(sickle_scores)} ({sickle_acc:.1f}%)")
    print(f"  Normal detection: {normal_correct}/{len(normal_scores)} ({normal_acc:.1f}%)")
    print(f"  Total accuracy: {total_acc:.1f}%")
    
    if total_acc > best_accuracy:
        best_accuracy = total_acc
        best_threshold = th

print("\n" + "="*60)
print(f"BEST THRESHOLD: {best_threshold:.2f}")
print(f"BEST ACCURACY: {best_accuracy:.1f}%")
print("="*60)

# Test on a few samples with best threshold
print("\n" + "="*60)
print("SAMPLE RESULTS WITH BEST THRESHOLD")
print("="*60)

print("\nSickle cell samples (should be > threshold):")
for img in sickle_images[:5]:
    pred = predict_image(img)
    result = "SICKLE" if pred > best_threshold else "NORMAL"
    print(f"  {os.path.basename(img)}: {pred:.4f} -> {result}")

print("\nNormal samples (should be < threshold):")
for img in normal_images[:5]:
    pred = predict_image(img)
    result = "SICKLE" if pred > best_threshold else "NORMAL"
    print(f"  {os.path.basename(img)}: {pred:.4f} -> {result}")