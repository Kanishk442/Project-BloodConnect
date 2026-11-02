# test_sickle.py
from disease_detector import sickle_cell_detector
import numpy as np

print('='*50)
print('SICKLE CELL DETECTOR TEST')
print('='*50)

if sickle_cell_detector.model:
    print('[OK] Model loaded!')
    print(f'   Input shape: {sickle_cell_detector.model.input_shape}')
    print(f'   Output shape: {sickle_cell_detector.model.output_shape}')
    print(f'   Threshold: {sickle_cell_detector.threshold}')
    
    test = np.random.rand(1, 128, 128, 3).astype(np.float32)
    pred = sickle_cell_detector.model.predict(test, verbose=0)[0][0]
    print(f'\nRandom test prediction: {pred:.4f}')
    
    if pred > sickle_cell_detector.threshold:
        print('Interpretation: SICKLE CELL')
    else:
        print('Interpretation: NORMAL')
    
    print('\n[OK] Sickle cell detector is ready!')
else:
    print('[ERROR] Model not loaded')