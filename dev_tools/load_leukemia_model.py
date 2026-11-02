# load_leukemia_model.py
import tensorflow as tf
import numpy as np
from tensorflow.keras import layers, models
import os

print("="*60)
print("FIXING LEUKEMIA MODEL LOADING")
print("="*60)

# Define a custom Dense layer that ignores quantization_config
class CompatibleDense(layers.Dense):
    def __init__(self, *args, **kwargs):
        # Remove quantization_config if present
        kwargs.pop('quantization_config', None)
        super().__init__(*args, **kwargs)

# Register the custom layer
custom_objects = {'Dense': CompatibleDense}

# Load the model with custom objects
model_path = 'models/leukemia_model_final.h5'

if os.path.exists(model_path):
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
        
        # Save in compatible format
        model.save('models/leukemia_model_compatible.h5')
        print("\n[OK] Saved compatible version as: models/leukemia_model_compatible.h5")
        
    except Exception as e:
        print(f"[ERROR] {e}")
else:
    print(f"[ERROR] Model not found at {model_path}")