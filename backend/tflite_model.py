# tflite_model.py - tiny wrapper around LiteRT (TFLite) so the server doesn't need TensorFlow (~700MB RAM)
import threading
import numpy as np

try:
    from ai_edge_litert.interpreter import Interpreter
except ImportError:  # fallbacks for other environments
    try:
        from tflite_runtime.interpreter import Interpreter
    except ImportError:
        from tensorflow.lite.python.interpreter import Interpreter


class TFLiteModel:
    """Thread-safe, Keras-like `predict()` over a .tflite file (single image batches)."""

    def __init__(self, path):
        self._lock = threading.Lock()
        self._it = Interpreter(model_path=path, num_threads=2)
        self._it.allocate_tensors()
        self._in = self._it.get_input_details()[0]
        self._out = self._it.get_output_details()[0]
        self.input_shape = tuple(int(x) for x in self._in['shape'])
        self.output_shape = tuple(int(x) for x in self._out['shape'])

    def predict(self, batch, verbose=0):
        batch = np.asarray(batch, dtype=np.float32)
        with self._lock:
            results = []
            for i in range(len(batch)):
                self._it.set_tensor(self._in['index'], batch[i:i + 1])
                self._it.invoke()
                results.append(self._it.get_tensor(self._out['index'])[0].copy())
        return np.stack(results)
