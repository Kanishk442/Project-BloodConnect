# config.py - all secrets/settings come from environment variables (see .env.example)
import os

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
except ImportError:
    pass


def _bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


class Config:
    ENV = os.getenv('APP_ENV', 'development')
    DEBUG = _bool('FLASK_DEBUG', False)

    # Secrets: set real values in production (the app refuses to start with defaults there)
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-secret-change-me-0123456789abcdef')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-only-jwt-secret-change-me-0123456789abcdef')

    # MySQL / TiDB Cloud
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'bloodconnect')
    MYSQL_SSL = _bool('MYSQL_SSL', False)            # set true for TiDB Cloud
    MYSQL_SSL_CA = os.getenv('MYSQL_SSL_CA', '')     # blank = system CA bundle
    MYSQL_POOL_SIZE = int(os.getenv('MYSQL_POOL_SIZE', '5'))

    # File upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

    # ML
    MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
    MODEL_PATH = os.path.join(MODELS_DIR, 'cell_classifier.tflite')

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    @classmethod
    def validate(cls):
        if cls.ENV == 'production':
            if 'dev-only' in cls.SECRET_KEY or 'dev-only' in cls.JWT_SECRET_KEY:
                raise RuntimeError('Set SECRET_KEY and JWT_SECRET_KEY environment variables in production.')
