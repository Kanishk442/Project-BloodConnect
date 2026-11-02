# test_trained_model.py
import tensorflow as tf
import numpy as np
import os

print("="*60)
print("TESTING TRAINED SICKLE CELL MODEL")
print("="*60)

# Load the trained model
model_path = r'D:\BloodConnect\backend\models\sickle_cell_model_trained.h5'

if os.path.exists(model_path):
    print(f"\n[OK] Model found at: {model_path}")
    
    try:
        model = tf.keras.models.load_model(model_path, compile=False)
        print("[OK] Model loaded successfully!")
        print(f"   Input shape: {model.input_shape}")
        print(f"   Output shape: {model.output_shape}")
        
        # Test with random input
        test_input = np.random.rand(1, 128, 128, 3).astype(np.float32)
        pred = model.predict(test_input, verbose=0)[0][0]
        print(f"\nRandom test prediction: {pred:.4f}")
        
        # Test with different inputs to see range
        print("\nTesting multiple random inputs:")
        predictions = []
        for i in range(10):
            test = np.random.rand(1, 128, 128, 3).astype(np.float32)
            p = model.predict(test, verbose=0)[0][0]
            predictions.append(p)
            print(f"  {i+1}: {p:.4f}")
        
        print(f"\nRange: min={min(predictions):.4f}, max={max(predictions):.4f}, mean={np.mean(predictions):.4f}")
        
        print("\n[OK] Model is ready for use!")
        
    except Exception as e:
        print(f"[ERROR] Failed to load model: {e}")
else:
    print(f"[ERROR] Model not found at {model_path}")