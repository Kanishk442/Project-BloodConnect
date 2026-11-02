# test_malaria_load.py
import os
import tensorflow as tf

model_path = "d:\\BloodConnect\\backend\\models\\malaria_model.h5"

print("="*50)
print("MALARIA MODEL TEST")
print("="*50)
print(f"Model exists: {os.path.exists(model_path)}")
print(f"File size: {os.path.getsize(model_path):,} bytes ({os.path.getsize(model_path)/1024/1024:.1f} MB)")

try:
    print("\nAttempting to load model...")
    model = tf.keras.models.load_model(model_path, compile=False)
    print("[OK] Model loaded successfully!")
    print(f"Input shape: {model.input_shape}")
    print(f"Output shape: {model.output_shape}")
    print("\nModel layers:")
    for i, layer in enumerate(model.layers):
        print(f"  {i}: {layer.name} - {layer.output_shape}")
    
    # Test with random input
    import numpy as np
    test_input = np.random.rand(1, 128, 128, 3).astype(np.float32)
    prediction = model.predict(test_input, verbose=0)
    print(f"\nTest prediction: {prediction[0][0]:.4f}")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()