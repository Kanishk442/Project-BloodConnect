# auth.py
from flask import Blueprint, request, jsonify
from database import db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import re
import traceback

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'donor')
        full_name = data.get('full_name')
        phone = data.get('phone')
        blood_group = data.get('blood_group')
        age = data.get('age')
        weight_kg = data.get('weight_kg')
        city = data.get('city')
        
        # Validation
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user exists
        existing = db.fetch_one("SELECT user_id FROM users WHERE email = %s", (email,))
        if existing:
            return jsonify({'error': 'Email already registered'}), 400
        
        if role not in ('donor', 'hospital'):
            return jsonify({'error': 'Invalid role'}), 400

        # Validate role-specific details BEFORE creating anything
        if role == 'donor':
            if not full_name or not phone or not blood_group:
                return jsonify({'error': 'Donor details required'}), 400
        else:
            hospital_name = data.get('hospital_name')
            license_number = data.get('license_number')
            address = data.get('address')
            if not hospital_name or not license_number:
                return jsonify({'error': 'Hospital details required'}), 400

        hashed_password = db.hash_password(password)
        user_id = db.execute_query("""
            INSERT INTO users (email, password, role, is_verified)
            VALUES (%s, %s, %s, %s)
        """, (email, hashed_password, role, True))

        if not user_id:
            return jsonify({'error': 'Registration failed'}), 500

        if role == 'donor':
            ok = db.execute_query("""
                INSERT INTO donors (user_id, full_name, age, blood_group, weight_kg, phone, city, donation_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, full_name, age, blood_group, weight_kg, phone, city, 0))
        else:
            ok = db.execute_query("""
                INSERT INTO hospitals (user_id, name, license_number, address, city, phone, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, hospital_name, license_number, address, city, phone, False))

        if not ok:
            db.execute_query("DELETE FROM users WHERE user_id = %s", (user_id,))
            return jsonify({'error': 'Registration failed'}), 500

        return jsonify({
            'message': 'Registration successful',
            'user_id': user_id,
            'role': role
        }), 201
        
    except Exception as e:
        print(f"❌ Registration error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        # Check database connection
        if not db.is_connected():
            return jsonify({'error': 'Database connection error'}), 500
        
        user = db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check password
        if not db.check_password(password, user['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Update last login (using CURRENT_TIMESTAMP for MySQL)
        db.execute_query(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s",
            (user['user_id'],)
        )
        
        # Get role-specific data - FIX: Remove hero_badge if column doesn't exist
        extra_data = {}
        if user['role'] == 'donor':
            donor = db.fetch_one("SELECT * FROM donors WHERE user_id = %s", (user['user_id'],))
            if donor:
                extra_data = {
                    'donor_id': donor['donor_id'],
                    'full_name': donor['full_name'],
                    'blood_group': donor['blood_group'],
                    'donation_count': donor.get('donation_count', 0),
                    'age': donor.get('age'),
                    'weight_kg': donor.get('weight_kg')
                }
        elif user['role'] == 'hospital':
            hospital = db.fetch_one("SELECT * FROM hospitals WHERE user_id = %s", (user['user_id'],))
            if hospital:
                extra_data = {
                    'hospital_id': hospital['hospital_id'],
                    'name': hospital['name'],
                    'is_verified': hospital.get('is_verified', False)
                }
        elif user['role'] == 'admin':
            extra_data = {
                'is_admin': True
            }
        
        # Create JWT token - FIX: Use consistent identity (integer or string)
        access_token = create_access_token(identity=str(user['user_id']))
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'user_id': user['user_id'],
                'email': user['email'],
                'role': user['role'],
                **extra_data
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_id = get_jwt_identity()
        
        user = db.fetch_one("SELECT user_id, email, role, created_at FROM users WHERE user_id = %s", (current_user_id,))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        profile = {
            'user_id': user['user_id'],
            'email': user['email'], 
            'role': user['role'],
            'created_at': str(user['created_at']) if user.get('created_at') else None
        }
        
        if user['role'] == 'donor':
            donor = db.fetch_one("SELECT * FROM donors WHERE user_id = %s", (user['user_id'],))
            if donor:
                # Remove sensitive fields
                donor.pop('donor_id', None)
                profile.update(donor)
        elif user['role'] == 'hospital':
            hospital = db.fetch_one("SELECT * FROM hospitals WHERE user_id = %s", (user['user_id'],))
            if hospital:
                hospital.pop('hospital_id', None)
                profile.update(hospital)
        
        return jsonify(profile), 200
        
    except Exception as e:
        print(f"❌ Profile error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # JWT is stateless, just return success
    # Client should remove the token from storage
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Old and new password required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400
        
        # Get user
        user = db.fetch_one("SELECT password FROM users WHERE user_id = %s", (current_user_id,))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify old password
        if not db.check_password(old_password, user['password']):
            return jsonify({'error': 'Invalid old password'}), 401
        
        # Hash new password
        hashed_password = db.hash_password(new_password)
        
        # Update password
        db.execute_query(
            "UPDATE users SET password = %s WHERE user_id = %s",
            (hashed_password, current_user_id)
        )
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        print(f"❌ Change password error: {e}")
        return jsonify({'error': str(e)}), 500