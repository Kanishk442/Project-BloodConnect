# test_all_detectors.py
from disease_detector import malaria_detector, leukemia_detector, sickle_cell_detector
import numpy as np

print('='*50)
print('ALL DETECTORS TEST')
print('='*50)

# Test random input
test_input = np.random.rand(1, 128, 128, 3).astype(np.float32)

# Malaria
pred = malaria_detector.model.predict(test_input, verbose=0)[0][0]
print(f'\nMalaria: {pred:.4f}')
if pred < 0.5:
    print('  Result: MALARIA DETECTED')
else:
    print('  Result: NO MALARIA')

# Sickle Cell
pred = sickle_cell_detector.model.predict(test_input, verbose=0)[0][0]
print(f'\nSickle Cell: {pred:.4f}')
if pred > 0.5:
    print('  Result: SICKLE CELL DETECTED')
else:
    print('  Result: NO SICKLE CELL')

# Leukemia (needs 224x224)
test_input_224 = np.random.rand(1, 224, 224, 3).astype(np.float32)
pred = leukemia_detector.model.predict(test_input_224, verbose=0)[0][0]
print(f'\nLeukemia: {pred:.4f}')
if pred < 0.52:
    print('  Result: LEUKEMIA DETECTED')
else:
    print('  Result: NO LEUKEMIA')