# test_pretrained.py
import tensorflow as tf
import numpy as np
import os
from PIL import Image

print("="*60)
print("TESTING PRETRAINED SICKLE CELL MODEL")
print("="*60)

# Load the model
model_path = 'models/sickle_cell_pretrained.h5'
model = tf.keras.models.load_model(model_path, compile=False)
print(f"[OK] Model loaded from: {model_path}")
print(f"Input shape: {model.input_shape}")
print(f"Output shape: {model.output_shape}")

# Test with random input
test = np.random.rand(1, 128, 128, 3).astype(np.float32)
pred = model.predict(test, verbose=0)[0][0]
print(f"\nRandom test prediction: {pred:.4f}")

# If you have test images, test them
test_folder = 'test_samples'
if os.path.exists(test_folder):
    images = [f for f in os.listdir(test_folder) if f.endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
    if images:
        print(f"\nTesting {len(images)} images from test_samples:")
        for img in images[:5]:
            img_path = os.path.join(test_folder, img)
            img_data = tf.keras.preprocessing.image.load_img(img_path, target_size=(128, 128))
            img_array = tf.keras.preprocessing.image.img_to_array(img_data) / 255.0
            img_array = np.expand_dims(img_array, axis=0)
            pred = model.predict(img_array, verbose=0)[0][0]
            result = "SICKLE" if pred > 0.5 else "NORMAL"
            print(f"  {img}: {pred:.4f} -> {result}")
    else:
        print("\nNo test images found in test_samples folder")
else:
    print("\ntest_samples folder not found")

print("\n[OK] Model ready for integration!")