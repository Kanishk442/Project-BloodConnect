# app.py
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from database import db
import os

# Import blueprints
from auth import auth_bp

# Import donor routes
from routes.donor_routes import donor_bp

# Import hospital routes
from routes.hospital_routes import hospital_bp

# Import admin routes (optional, for future)
# from routes.admin_routes import admin_bp

# Create Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
Config.validate()
app.config.from_object(Config)
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Enable CORS
CORS(app)

# Initialize JWT
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(donor_bp, url_prefix='/api/donor')
app.register_blueprint(hospital_bp, url_prefix='/api/hospital')
# app.register_blueprint(admin_bp, url_prefix='/api/admin')

# ============================================
# FRONTEND ROUTES - Serve HTML pages
# ============================================

@app.route('/')
def serve_index():
    """Serve the main landing page"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/login')
def serve_login():
    """Serve login page"""
    return send_from_directory('../frontend', 'login.html')

@app.route('/register')
def serve_register():
    """Serve registration page"""
    return send_from_directory('../frontend', 'register.html')

@app.route('/donor/<path:filename>')
def serve_donor_pages(filename):
    """Serve donor dashboard pages"""
    return send_from_directory('../frontend/donor', filename)

@app.route('/hospital/<path:filename>')
def serve_hospital_pages(filename):
    """Serve hospital dashboard pages"""
    return send_from_directory('../frontend/hospital', filename)

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files"""
    return send_from_directory('../frontend/css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files"""
    return send_from_directory('../frontend/js', filename)

# ============================================
# API STATUS ENDPOINTS
# ============================================

@app.route('/api/status')
def api_status():
    """Check API status"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'database': 'connected' if db.is_connected() else 'unreachable',
        'ml_models_present': all(os.path.exists(os.path.join(Config.MODELS_DIR, f)) for f in (
            'cell_classifier.tflite', 'malaria.tflite', 'leukemia.tflite', 'sickle.tflite'))
    }), 200

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    print(f"BloodConnect running on http://localhost:{port}")
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=port)
