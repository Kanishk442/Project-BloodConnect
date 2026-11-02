# disease_detector.py - malaria / leukemia / sickle-cell screening models (TFLite)
import os
import numpy as np
from PIL import Image

from tflite_model import TFLiteModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')


def _load(label, filename):
    path = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        print(f"[{label}] Model not found at {path}")
        return None
    try:
        model = TFLiteModel(path)
        print(f"[{label}] Model loaded. Input shape: {model.input_shape}")
        return model
    except Exception as e:
        print(f"[{label}] Error loading model: {e}")
        return None


def _prepare(image_path, size):
    img = Image.open(image_path).convert('RGB').resize((size, size))
    return np.expand_dims(np.array(img, dtype=np.float32) / 255.0, axis=0)


def _error(message):
    return {'detected': False, 'confidence': round(0.0, 1), 'message': message, 'error': True}


class _BaseDetector:
    label = 'Detector'
    filename = ''
    img_size = 128
    threshold = 0.5

    def __init__(self):
        self.model = _load(self.label, self.filename)

    def _score(self, image_path):
        """Returns raw model score, or an error dict."""
        if self.model is None:
            return None, _error(f'{self.label} model not available')
        if not os.path.exists(image_path):
            return None, _error(f'Image not found: {image_path}')
        try:
            score = float(self.model.predict(_prepare(image_path, self.img_size), verbose=0)[0][0])
            print(f"[{self.label}] Raw prediction: {score:.4f}")
            return score, None
        except Exception as e:
            print(f"[{self.label}] Prediction error: {e}")
            return None, _error(f'Error: {e}')


class MalariaDetector(_BaseDetector):
    """Score < threshold = parasitized (malaria)."""
    label, filename, img_size, threshold = 'Malaria', 'malaria.tflite', 128, 0.5

    def predict(self, image_path):
        score, err = self._score(image_path)
        if err:
            return err
        if score < self.threshold:
            return {'detected': True, 'confidence': round((1 - score) * 100, 1), 'raw_prediction': score, 'error': False,
                    'message': 'Malaria detected (Parasitized) - Please consult a doctor immediately'}
        return {'detected': False, 'confidence': round(score * 100, 1), 'raw_prediction': score, 'error': False,
                'message': 'No malaria detected - Normal result'}


class LeukemiaDetector(_BaseDetector):
    """Score > threshold = normal, score < threshold = leukemia (ALL)."""
    label, filename, img_size, threshold = 'Leukemia', 'leukemia.tflite', 224, 0.52

    def predict(self, image_path):
        score, err = self._score(image_path)
        if err:
            return err
        if score > self.threshold:
            return {'detected': False, 'confidence': round(score * 100, 1), 'raw_prediction': score, 'error': False,
                    'message': 'No leukemia detected - Normal result'}
        return {'detected': True, 'confidence': round((1 - score) * 100, 1), 'raw_prediction': score, 'error': False,
                'message': 'Leukemia (ALL) detected - Please consult a hematologist immediately'}


class SickleCellDetector(_BaseDetector):
    """Score > threshold = sickle cell (sigmoid output, sickle = class 1)."""
    label, filename, img_size, threshold = 'Sickle Cell', 'sickle.tflite', 128, 0.45

    def predict(self, image_path):
        score, err = self._score(image_path)
        if err:
            return err
        if score > self.threshold:
            return {'detected': True, 'confidence': round(score * 100, 1), 'raw_prediction': score, 'error': False,
                    'message': 'Sickle cell indicators detected - Please consult a hematologist'}
        return {'detected': False, 'confidence': round((1 - score) * 100, 1), 'raw_prediction': score, 'error': False,
                'message': 'No sickle cell indicators detected - Normal result'}


# Lazy singletons: models are loaded on first use (fast startup, low RAM)
_FACTORIES = {
    'malaria_detector': MalariaDetector,
    'leukemia_detector': LeukemiaDetector,
    'sickle_cell_detector': SickleCellDetector,
}
_instances = {}


def __getattr__(name):
    if name in _FACTORIES:
        if name not in _instances:
            _instances[name] = _FACTORIES[name]()
        return _instances[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
