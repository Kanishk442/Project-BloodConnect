# ml_integration.py
import numpy as np
import os
from PIL import Image
from config import Config
from tflite_model import TFLiteModel

class BloodCellClassifier:
    def __init__(self, model_path=None):
        self.img_size = (128, 128)
        self.class_names = ['EOSINOPHIL', 'LYMPHOCYTE', 'MONOCYTE', 'NEUTROPHIL']
        
        self.disease_map = {
            'LYMPHOCYTE': ['Lymphoma', 'Lymphocytic Leukemia (ALL/CLL)', 'Viral Infections'],
            'NEUTROPHIL': ['Bacterial Infections', 'Inflammation', 'Myeloid Leukemia'],
            'MONOCYTE': ['Chronic Infections', 'Monocytic Leukemia', 'Tuberculosis'],
            'EOSINOPHIL': ['Allergic Reactions', 'Parasitic Infections', 'Asthma']
        }
        
        if model_path is None:
            model_path = os.path.join(Config.MODELS_DIR, 'cell_classifier.tflite')

        self.model = None
        if os.path.exists(model_path):
            try:
                self.model = TFLiteModel(model_path)
                print(f"[OK] Cell classifier loaded: {model_path}")
            except Exception as e:
                print(f"[ERROR] Error loading cell classifier: {e}")
        else:
            print(f"[WARNING] Cell classifier not found at {model_path}")

    def predict(self, image_path):
        """
        Predict cell type from blood cell image
        Returns dictionary with cell_type, confidence, diseases, is_healthy
        """
        if self.model is None:
            return {'cell_type': 'UNKNOWN', 'confidence': 0, 'diseases': 'Model not loaded', 'is_healthy': False, 'error': 'Model not loaded'}
        
        try:
            # Check if image exists
            if not os.path.exists(image_path):
                print(f"[ERROR] Image file not found: {image_path}")
                return {
                    'cell_type': 'UNKNOWN',
                    'confidence': 0,
                    'diseases': 'Image file not found',
                    'is_healthy': False,
                    'error': 'Image not found'
                }
            
            # Load and preprocess image
            img = Image.open(image_path).convert('RGB').resize(self.img_size, Image.NEAREST)  # matches Keras load_img default
            img_array = np.expand_dims(np.array(img, dtype=np.float32) / 255.0, axis=0)
            
            # Make prediction
            predictions = self.model.predict(img_array, verbose=0)[0]
            predicted_class = np.argmax(predictions)
            confidence = float(predictions[predicted_class] * 100)
            cell_type = self.class_names[predicted_class]
            diseases = self.disease_map.get(cell_type, ["Unknown"])
            
            # Get all predictions for debugging
            all_predictions = {
                self.class_names[i]: float(predictions[i] * 100) 
                for i in range(len(self.class_names))
            }
            
            print(f"[INFO] Prediction: {cell_type} with {confidence:.2f}% confidence")
            print(f"[INFO] All predictions: {all_predictions}")
            
            # For cell type classification, is_healthy is True for all normal cell types
            # Abnormal conditions would be detected by high counts, not single cell identification
            return {
                'cell_type': cell_type,
                'confidence': confidence,
                'diseases': ', '.join(diseases),
                'is_healthy': True,
                'all_predictions': all_predictions
            }
            
        except Exception as e:
            print(f"[ERROR] Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'cell_type': 'UNKNOWN',
                'confidence': 0,
                'diseases': f'Analysis error: {str(e)}',
                'is_healthy': False,
                'error': str(e)
            }
    
    def predict_batch(self, image_paths):
        """
        Predict cell types for multiple images
        """
        results = []
        for path in image_paths:
            result = self.predict(path)
            results.append({
                'image_path': path,
                'result': result
            })
        return results
    
    def get_model_info(self):
        """
        Return information about the loaded model
        """
        if self.model is None:
            return {
                'loaded': False,
                'message': 'Model not loaded'
            }
        
        return {
            'loaded': True,
            'input_shape': self.model.input_shape,
            'output_shape': self.model.output_shape,
            'classes': self.class_names,
            'image_size': self.img_size
        }

# Lazy global instance (model loads on first access)
_classifier = None

def __getattr__(name):
    global _classifier
    if name == 'classifier':
        if _classifier is None:
            _classifier = BloodCellClassifier()
        return _classifier
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Test function to verify model loading
def test_classifier():
    classifier = __getattr__('classifier')
    """Test if classifier is working properly"""
    info = classifier.get_model_info()
    print("\n" + "="*50)
    print("CLASSIFIER STATUS")
    print("="*50)
    if info['loaded']:
        print(f"[OK] Model loaded successfully")
        print(f"Input shape: {info['input_shape']}")
        print(f"Output shape: {info['output_shape']}")
        print(f"Classes: {info['classes']}")
        print(f"Image size: {info['image_size']}")
    else:
        print(f"[ERROR] Model not loaded: {info['message']}")
    print("="*50)
    return info['loaded']

# Run test on import
if __name__ == "__main__":
    test_classifier()