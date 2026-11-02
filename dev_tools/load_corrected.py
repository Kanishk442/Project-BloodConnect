# load_corrected.py
import tensorflow as tf
import numpy as np
import os

print("="*60)
print("LOADING LEUKEMIA MODEL WITH CUSTOM OBJECTS")
print("="*60)

# Define the custom Dense layer that ignores quantization_config
class CompatibleDense(tf.keras.layers.Dense):
    def __init__(self, *args, **kwargs):
        # Remove quantization_config if present
        kwargs.pop('quantization_config', None)
        super().__init__(*args, **kwargs)

# Register the custom layer
custom_objects = {'CompatibleDense': CompatibleDense}

# Load the model with custom objects
model_path = 'models/leukemia_model_compatible.h5'

if not os.path.exists(model_path):
    print(f"Model not found at {model_path}")
    exit(1)

print(f"\n[INFO] Loading model from: {model_path}")

try:
    model = tf.keras.models.load_model(
        model_path,
        compile=False,
        custom_objects=custom_objects
    )
    print("[OK] Model loaded successfully!")
    print(f"   Input shape: {model.input_shape}")
    print(f"   Output shape: {model.output_shape}")
    
    # Test with random input
    test_input = np.random.rand(1, 224, 224, 3).astype(np.float32)
    pred = model.predict(test_input, verbose=0)[0][0]
    print(f"   Test prediction: {pred:.4f}")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()