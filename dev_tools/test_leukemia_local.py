# test_leukemia_local.py
import tensorflow as tf
import numpy as np
from PIL import Image
import os
import matplotlib.pyplot as plt

print("="*60)
print("LEUKEMIA MODEL LOCAL TEST")
print("="*60)

# Step 1: Load the model
model_path = 'models/leukemia_model_final.h5'

print(f"\n[INFO] Loading model from: {model_path}")

if not os.path.exists(model_path):
    print(f"[ERROR] Model not found at {model_path}")
    print("\nAvailable models in models folder:")
    for f in os.listdir('models'):
        if f.endswith('.h5'):
            print(f"  - {f}")
    exit(1)

try:
    model = tf.keras.models.load_model(model_path, compile=False)
    print("[OK] Model loaded successfully!")
    print(f"   Input shape: {model.input_shape}")
    print(f"   Output shape: {model.output_shape}")
except Exception as e:
    print(f"[ERROR] Error loading model: {e}")
    exit(1)

# Step 2: Find test images
test_folder = 'test_samples'
if not os.path.exists(test_folder):
    print(f"\n[ERROR] Test folder not found: {test_folder}")
    print("Please create a 'test_samples' folder with leukemia and normal images")
    exit(1)

# Get all images
images = [f for f in os.listdir(test_folder) if f.endswith(('.bmp', '.jpg', '.png'))]
print(f"\n[INFO] Found {len(images)} test images")

if len(images) == 0:
    print("No images found in test_samples folder")
    exit(1)

# Step 3: Test each image
print("\n" + "="*60)
print("PREDICTION RESULTS")
print("="*60)

def predict_image(image_path, model):
    img = tf.keras.preprocessing.image.load_img(image_path, target_size=(128, 128))
    img_array = tf.keras.preprocessing.image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    prediction = model.predict(img_array, verbose=0)[0][0]
    return float(prediction)

results = []

for img_file in sorted(images):
    img_path = os.path.join(test_folder, img_file)
    prediction = predict_image(img_path, model)
    
    # Based on Gemini output: 0.879 = Healthy, so >0.5 = Normal, <0.5 = Leukemia
    if prediction > 0.5:
        result = "NORMAL"
        confidence = prediction * 100
        status = "HEALTHY"
    else:
        result = "LEUKEMIA DETECTED"
        confidence = (1 - prediction) * 100
        status = "URGENT"
    
    results.append({
        'file': img_file,
        'result': result,
        'confidence': confidence,
        'raw': prediction,
        'status': status
    })
    
    print(f"\n[FILE] {img_file}")
    print(f"   Raw Score: {prediction:.4f}")
    print(f"   Result: {result}")
    print(f"   Confidence: {confidence:.1f}%")

# Step 4: Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

leukemia_count = sum(1 for r in results if 'LEUKEMIA' in r['result'])
normal_count = sum(1 for r in results if 'NORMAL' in r['result'])

print(f"Total images: {len(results)}")
print(f"Leukemia detected: {leukemia_count}")
print(f"Normal detected: {normal_count}")

if leukemia_count > 0:
    avg_conf = sum(r['confidence'] for r in results if 'LEUKEMIA' in r['result']) / leukemia_count
    print(f"Average confidence for Leukemia: {avg_conf:.1f}%")
if normal_count > 0:
    avg_conf = sum(r['confidence'] for r in results if 'NORMAL' in r['result']) / normal_count
    print(f"Average confidence for Normal: {avg_conf:.1f}%")

# Step 5: Visualize results (optional)
try:
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    axes = axes.flatten()
    
    for i, result in enumerate(results[:6]):
        img_path = os.path.join(test_folder, result['file'])
        img = plt.imread(img_path)
        axes[i].imshow(img, cmap='gray')
        color = 'red' if 'LEUKEMIA' in result['result'] else 'green'
        axes[i].set_title(f"{result['file']}\n{result['result']}\n{result['confidence']:.1f}%", 
                         color=color, fontsize=9)
        axes[i].axis('off')
    
    plt.tight_layout()
    plt.savefig('leukemia_test_results.png')
    print(f"\n[OK] Visualization saved as: leukemia_test_results.png")
    plt.show()
except Exception as e:
    print(f"\n[WARN] Could not create visualization: {e}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)