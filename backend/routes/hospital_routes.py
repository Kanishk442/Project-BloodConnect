# routes/hospital_routes.py - Complete with all test types and donation system
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
import os
from werkzeug.utils import secure_filename
from config import Config
from datetime import datetime, timedelta
import uuid
import json
import traceback

hospital_bp = Blueprint('hospital', __name__)

def convert_dates(obj):
    if isinstance(obj, dict):
        return {k: convert_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates(item) for item in obj]
    elif isinstance(obj, (datetime, timedelta)):
        return str(obj)
    return obj

# ============================================
# DONATION RECORDING SYSTEM
# ============================================

@hospital_bp.route('/donations/record', methods=['POST'])
@jwt_required()
def record_donation():
    """Record a successful donation after blood test"""
    try:
        user_id = get_jwt_identity()
        
        # Get hospital info
        hospital = db.fetch_one("SELECT hospital_id, name FROM hospitals WHERE user_id = %s", (user_id,))
        if not hospital:
            return jsonify({'error': 'Hospital not found'}), 404
        
        data = request.get_json()
        donor_id = data.get('donor_id')
        test_type = data.get('test_type')
        test_result = data.get('test_result')
        quantity_ml = data.get('quantity_ml', 450)
        appointment_id = data.get('appointment_id')
        
        if not donor_id:
            return jsonify({'error': 'Donor ID is required'}), 400
        
        # Verify donor exists
        donor = db.fetch_one("SELECT donor_id, donation_count FROM donors WHERE donor_id = %s", (donor_id,))
        if not donor:
            return jsonify({'error': f'Donor with ID {donor_id} not found'}), 404
        
        # Record donation
        new_id = db.execute_query("""
            INSERT INTO donations (donor_id, hospital_id, appointment_id, quantity_ml, 
                                   test_type, test_result, donation_date)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (donor_id, hospital['hospital_id'], appointment_id, quantity_ml, 
              test_type, json.dumps(test_result)))
        
        donation_id = new_id
        
        # Update donor's donation count
        new_donation_count = (donor['donation_count'] or 0) + 1
        db.execute_query("""
            UPDATE donors SET donation_count = %s WHERE donor_id = %s
        """, (new_donation_count, donor_id))
        
        # Create donation confirmation alert
        db.execute_query("""
            INSERT INTO alerts (donor_id, alert_type, title, message, details, is_read)
            VALUES (%s, 'donation', 'Donation Completed', 
                    'Thank you for donating %s ml of blood! Your generosity saves lives.',
                    %s, FALSE)
        """, (donor_id, quantity_ml, json.dumps({
            'donation_id': donation_id,
            'quantity_ml': quantity_ml,
            'hospital_name': hospital['name'],
            'donation_count': new_donation_count
        })))
        
        # Check and award badges
        new_badges = check_and_award_badges(donor_id, new_donation_count)
        
        # Update appointment if provided
        if appointment_id:
            db.execute_query("""
                UPDATE appointments SET status = 'completed' 
                WHERE appointment_id = %s
            """, (appointment_id,))
        
        return jsonify({
            'success': True,
            'donation_id': donation_id,
            'donation_count': new_donation_count,
            'badges_awarded': new_badges,
            'message': 'Donation recorded successfully'
        }), 201
        
    except Exception as e:
        print(f"Record donation error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================
# ALERT SENDING SYSTEM
# ============================================

@hospital_bp.route('/alerts/send', methods=['POST'])
@jwt_required()
def send_alert():
    """Send alert to donor"""
    try:
        user_id = get_jwt_identity()
        
        # Verify hospital exists
        hospital = db.fetch_one("SELECT hospital_id FROM hospitals WHERE user_id = %s", (user_id,))
        if not hospital:
            return jsonify({'error': 'Hospital not found'}), 404
        
        data = request.get_json()
        donor_id = data.get('donor_id')
        alert_type = data.get('alert_type')
        title = data.get('title')
        message = data.get('message')
        details = data.get('details')
        
        if not all([donor_id, alert_type, title, message]):
            return jsonify({'error': 'Missing required fields: donor_id, alert_type, title, message'}), 400
        
        # Verify donor exists
        donor = db.fetch_one("SELECT donor_id FROM donors WHERE donor_id = %s", (donor_id,))
        if not donor:
            return jsonify({'error': f'Donor with ID {donor_id} not found'}), 404
        
        # Create alert
        db.execute_query("""
            INSERT INTO alerts (donor_id, alert_type, title, message, details, is_read)
            VALUES (%s, %s, %s, %s, %s, FALSE)
        """, (donor_id, alert_type, title, message, json.dumps(details) if details else None))
        
        return jsonify({
            'success': True,
            'message': 'Alert sent successfully'
        }), 201
        
    except Exception as e:
        print(f"Send alert error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================
# BADGE CHECKING HELPER FUNCTION
# ============================================

def check_and_award_badges(donor_id, donation_count):
    """Check and award badges based on donation count"""
    new_badges = []
    
    # Define badge thresholds
    badge_thresholds = [
        {
            'threshold': 1,
            'name': 'First Blood',
            'icon': '🩸',
            'message': 'Congratulations on your first donation! You\'ve started your journey as a lifesaver.'
        },
        {
            'threshold': 3,
            'name': 'Lifesaver',
            'icon': '💪',
            'message': 'You\'ve completed 3 donations! You\'ve saved multiple lives with your generosity.'
        },
        {
            'threshold': 5,
            'name': 'Hero Badge',
            'icon': '🏆',
            'message': 'Hero Badge Unlocked! 5 donations completed. You\'re a true hero to many patients.'
        },
        {
            'threshold': 10,
            'name': 'Platinum Donor',
            'icon': '💎',
            'message': 'Platinum Donor Status Achieved! 10 donations - you\'re an inspiration to the community.'
        }
    ]
    
    # Get already earned badges
    earned_badges = db.fetch_all("""
        SELECT badge_name FROM badges WHERE donor_id = %s
    """, (donor_id,))
    
    earned_names = [b['badge_name'] for b in earned_badges]
    
    # Check each badge threshold
    for badge in badge_thresholds:
        if donation_count >= badge['threshold'] and badge['name'] not in earned_names:
            # Award the badge
            db.execute_query("""
                INSERT INTO badges (donor_id, badge_name, badge_icon, badge_message, awarded_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (donor_id, badge['name'], badge['icon'], badge['message']))
            
            # Create badge alert
            db.execute_query("""
                INSERT INTO alerts (donor_id, alert_type, title, message, details, is_read)
                VALUES (%s, 'badge',CONCAT('🏆 Badge Earned: ', %s), %s, 
                        %s, FALSE)
            """, (donor_id, badge['name'], badge['message'], 
                  json.dumps({'badge_name': badge['name'], 'badge_icon': badge['icon']})))
            
            new_badges.append(badge)
    
    return new_badges

# ============================================
# CELL TYPE CLASSIFICATION (WBC)
# ============================================
@hospital_bp.route('/blood-test/cell', methods=['POST'])
@jwt_required()
def test_cell_type():
    try:
        user_id = get_jwt_identity()
        
        hospital = db.fetch_one("SELECT hospital_id FROM hospitals WHERE user_id = %s", (user_id,))
        if not hospital:
            return jsonify({'error': 'Hospital not found'}), 404
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        donor_id = request.form.get('donor_id')
        appointment_id = request.form.get('appointment_id')
        
        if not donor_id:
            return jsonify({'error': 'Donor ID required'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Verify donor exists
        donor = db.fetch_one("SELECT donor_id FROM donors WHERE donor_id = %s", (donor_id,))
        if not donor:
            return jsonify({'error': f'Donor with ID {donor_id} not found'}), 404
        
        # Save the file
        filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Run cell classification
        try:
            from ml_integration import classifier
            result = classifier.predict(filepath)
        except Exception as ml_error:
            print(f"Cell classification error: {ml_error}")
            return jsonify({'error': 'Analysis service unavailable. Please try again later.'}), 503
        
        if result.get('error'):
            return jsonify({'error': 'Analysis service unavailable. Please try again later.'}), 503
        
        # Determine if eligible for donation
        is_eligible = result.get('is_healthy', False)
        
        # Save test record
        new_id = db.execute_query("""
            INSERT INTO blood_tests (appointment_id, donor_id, hospital_id, image_path, 
                                     ml_cell_type, ml_confidence, diseases_detected, is_healthy)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (appointment_id if appointment_id else None, donor_id, hospital['hospital_id'], filepath,
              result['cell_type'], result['confidence'], result['diseases'], result['is_healthy']))
        
        test_id = new_id
        
        # Create health alert based on results
        alert_title = "Cell Type Analysis Complete"
        if not is_eligible:
            alert_message = f"URGENT: Abnormal cells detected. Cell type: {result['cell_type']}. " \
                          f"Possible conditions: {result['diseases']}. Please consult a doctor immediately."
        else:
            alert_message = f"Cell type analysis complete. Detected: {result['cell_type']}. " \
                          f"Results appear normal. You may be eligible for donation."
        
        db.execute_query("""
            INSERT INTO alerts (donor_id, test_id, title, message, alert_type, is_read)
            VALUES (%s, %s, %s, %s, 'health', FALSE)
        """, (donor_id, test_id, alert_title, alert_message))
        
        return jsonify({
            'message': 'Cell type analysis complete',
            'test_id': test_id,
            'result': result,
            'is_eligible': is_eligible
        }), 201
        
    except Exception as e:
        print(f"Upload error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================
# MALARIA DETECTION (RBC)
# ============================================
@hospital_bp.route('/blood-test/malaria', methods=['POST'])
@jwt_required()
def test_malaria():
    try:
        user_id = get_jwt_identity()
        
        hospital = db.fetch_one("SELECT hospital_id FROM hospitals WHERE user_id = %s", (user_id,))
        if not hospital:
            return jsonify({'error': 'Hospital not found'}), 404
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        donor_id = request.form.get('donor_id')
        appointment_id = request.form.get('appointment_id')
        
        if not donor_id:
            return jsonify({'error': 'Donor ID required'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Verify donor exists
        donor = db.fetch_one("SELECT donor_id FROM donors WHERE donor_id = %s", (donor_id,))
        if not donor:
            return jsonify({'error': f'Donor with ID {donor_id} not found'}), 404
        
        # Save the file
        filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Run malaria detection
        try:
            from disease_detector import malaria_detector
            result = malaria_detector.predict(filepath)
        except Exception as ml_error:
            print(f"Malaria detection error: {ml_error}")
            return jsonify({'error': 'Analysis service unavailable. Please try again later.'}), 503
        
        if result.get('error'):
            return jsonify({'error': 'Analysis service unavailable. Please try again later.'}), 503
        
        # Determine if eligible for donation
        is_eligible = not result.get('detected', False)
        
        # Format result for database
        if result['detected']:
            diseases_detected = f"Malaria ({result['confidence']:.1f}%)"
            is_healthy = False
            ml_cell_type = "Plasmodium (Malaria)"
            ml_confidence = result['confidence']
        else:
            diseases_detected = "No Malaria detected"
            is_healthy = True
            ml_cell_type = "Normal RBC"
            ml_confidence = result['confidence']
        
        # Save test record
        new_id = db.execute_query("""
            INSERT INTO blood_tests (appointment_id, donor_id, hospital_id, image_path, 
                                     ml_cell_type, ml_confidence, diseases_detected, is_healthy)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (appointment_id if appointment_id else None, donor_id, hospital['hospital_id'], filepath,
              ml_cell_type, ml_confidence, diseases_detected, is_healthy))
        
        test_id = new_id
        
        # Create alert
        alert_title = "Malaria Test Results"
        if result['detected']:
            alert_message = f"URGENT: Malaria detected! Confidence: {result['confidence']:.1f}%. Please consult a doctor immediately."
        else:
            alert_message = f"Malaria test negative. Confidence: {result['confidence']:.1f}%."
        
        db.execute_query("""
            INSERT INTO alerts (donor_id, test_id, title, message, alert_type, is_read)
            VALUES (%s, %s, %s, %s, 'health', FALSE)
        """, (donor_id, test_id, alert_title, alert_message))
        
        return jsonify({
            'message': 'Malaria test complete',
            'test_id': test_id,
            'result': result,
            'is_eligible': is_eligible
        }), 201
        
    except Exception as e:
        print(f"Upload error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================
# LEUKEMIA DETECTION (ALL)
# ============================================
@hospital_bp.route('/blood-test/leukemia', methods=['POST'])
@jwt_required()
def test_leukemia():
    try:
        user_id = get_jwt_identity()
        
        hospital = db.fetch_one("SELECT hospital_id FROM hospitals WHERE user_id = %s", (user_id,))
        if not hospital:
            return jsonify({'error': 'Hospital not found'}), 404
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        donor_id = request.form.get('donor_id')
        appointment_id = request.form.get('appointment_id')
        
        if not donor_id:
            return jsonify({'error': 'Donor ID required'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Verify donor exists
        donor = db.fetch_one("SELECT donor_id FROM donors WHERE donor_id = %s", (donor_id,))
        if not donor:
            return jsonify({'error': f'Donor with ID {donor_id} not found'}), 404
        
        # Save the file
        filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Run leukemia detection
        try:
            from disease_detector import leukemia_detector
            result = leukemia_detector.predict(filepath)
            print(f"[Leukemia] Detection result: {result}")
        except Exception as ml_error:
            print(f"Leukemia detection error: {ml_error}")
            traceback.print_exc()
            return jsonify({'error': 'Analysis service unavailable. Please try again later.'}), 503
        
        if result.get('error'):
            return jsonify({'error': 'Analysis service unavailable. Please try again later.'}), 503
        
        # Determine if eligible for donation
        is_eligible = not result.get('detected', False)
        
        # Format result for database
        if result.get('detected', False):
            diseases_detected = f"Leukemia ({result.get('confidence', 0):.1f}%)"
            is_healthy = False
            ml_cell_type = "ALL (Leukemia)"
            ml_confidence = result.get('confidence', 0)
        else:
            diseases_detected = "No Leukemia detected"
            is_healthy = True
            ml_cell_type = "Normal"
            ml_confidence = result.get('confidence', 100)
        
        # Save test record
        new_id = db.execute_query("""
            INSERT INTO blood_tests (appointment_id, donor_id, hospital_id, image_path, 
                                     ml_cell_type, ml_confidence, diseases_detected, is_healthy)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (appointment_id if appointment_id else None, donor_id, hospital['hospital_id'], filepath,
              ml_cell_type, ml_confidence, diseases_detected, is_healthy))
        
        test_id = new_id
        
        # Create alert
        alert_title = "Leukemia Screening Results"
        if result.get('detected', False):
            alert_message = f"URGENT: Leukemia detected! Confidence: {result.get('confidence', 0):.1f}%. Please consult a hematologist immediately."
        else:
            alert_message = f"Leukemia screening negative. Confidence: {result.get('confidence', 100):.1f}%."
        
        db.execute_query("""
            INSERT INTO alerts (donor_id, test_id, title, message, alert_type, is_read)
            VALUES (%s, %s, %s, %s, 'health', FALSE)
        """, (donor_id, test_id, alert_title, alert_message))
        
        return jsonify({
            'message': 'Leukemia screening complete',
            'test_id': test_id,
            'result': result,
            'is_eligible': is_eligible
        }), 201
        
    except Exception as e:
        print(f"Upload error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================
# SICKLE CELL DETECTION
# ============================================
@hospital_bp.route('/blood-test/sickle', methods=['POST'])
@jwt_required()
def test_sickle_cell():
    try:
        user_id = get_jwt_identity()
        
        hospital = db.fetch_one("SELECT hospital_id FROM hospitals WHERE user_id = %s", (user_id,))
        if not hospital:
            return jsonify({'error': 'Hospital not found'}), 404
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        donor_id = request.form.get('donor_id')
        appointment_id = request.form.get('appointment_id')
        
        if not donor_id:
            return jsonify({'error': 'Donor ID required'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Verify donor exists
        donor = db.fetch_one("SELECT donor_id FROM donors WHERE donor_id = %s", (donor_id,))
        if not donor:
            return jsonify({'error': f'Donor with ID {donor_id} not found'}), 404
        
        # Save the file
        filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Run sickle cell detection
        try:
            from disease_detector import sickle_cell_detector
            result = sickle_cell_detector.predict(filepath)
        except Exception as ml_error:
            print(f"Sickle cell detection error: {ml_error}")
            return jsonify({'error': 'Analysis service unavailable. Please try again later.'}), 503
        
        if result.get('error'):
            return jsonify({'error': 'Analysis service unavailable. Please try again later.'}), 503
        
        # Determine if eligible for donation
        is_eligible = not result.get('detected', False)
        
        # Format result for database
        if result['detected']:
            diseases_detected = f"Sickle Cell Disease ({result['confidence']:.1f}%)"
            is_healthy = False
            ml_cell_type = "Sickle Cell"
            ml_confidence = result['confidence']
        else:
            diseases_detected = "No Sickle Cell detected"
            is_healthy = True
            ml_cell_type = "Normal RBC"
            ml_confidence = result['confidence']
        
        # Save test record
        new_id = db.execute_query("""
            INSERT INTO blood_tests (appointment_id, donor_id, hospital_id, image_path, 
                                     ml_cell_type, ml_confidence, diseases_detected, is_healthy)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (appointment_id if appointment_id else None, donor_id, hospital['hospital_id'], filepath,
              ml_cell_type, ml_confidence, diseases_detected, is_healthy))
        
        test_id = new_id
        
        # Create alert
        alert_title = "Sickle Cell Screening Results"
        if result['detected']:
            alert_message = f"URGENT: Sickle Cell Disease detected! Confidence: {result['confidence']:.1f}%. Please consult a hematologist immediately."
        else:
            alert_message = f"Sickle Cell screening negative. Confidence: {result['confidence']:.1f}%."
        
        db.execute_query("""
            INSERT INTO alerts (donor_id, test_id, title, message, alert_type, is_read)
            VALUES (%s, %s, %s, %s, 'health', FALSE)
        """, (donor_id, test_id, alert_title, alert_message))
        
        return jsonify({
            'message': 'Sickle Cell screening complete',
            'test_id': test_id,
            'result': result,
            'is_eligible': is_eligible
        }), 201
        
    except Exception as e:
        print(f"Upload error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================
# EXISTING ENDPOINTS (Dashboard, Appointments, etc.)
# ============================================

@hospital_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    try:
        user_id = get_jwt_identity()
        
        hospital = db.fetch_one("SELECT * FROM hospitals WHERE user_id = %s", (user_id,))
        if not hospital:
            return jsonify({'error': 'Hospital not found'}), 404
        
        hospital_id = hospital['hospital_id']
        
        today_appointments = db.fetch_all("""
            SELECT a.appointment_id, a.donor_id, a.appointment_date, a.appointment_time, a.status,
                   d.full_name as donor_name, d.blood_group, d.phone as donor_phone
            FROM appointments a
            JOIN donors d ON a.donor_id = d.donor_id
           WHERE a.hospital_id = %s
            ORDER BY a.appointment_time ASC
        """, (hospital_id,))
        
        pending_appointments = db.fetch_all("""
            SELECT a.appointment_id, a.donor_id, a.appointment_date, a.appointment_time, a.status,
                   d.full_name as donor_name, d.blood_group, d.phone as donor_phone
            FROM appointments a
            JOIN donors d ON a.donor_id = d.donor_id
            WHERE a.hospital_id = %s AND a.status = 'pending'
            ORDER BY a.appointment_date ASC
            LIMIT 10
        """, (hospital_id,))
        
        recent_tests = db.fetch_all("""
            SELECT bt.test_id, bt.image_path, bt.ml_cell_type, bt.ml_confidence, 
                   bt.diseases_detected, bt.is_healthy, bt.tested_at,
                   d.full_name as donor_name
            FROM blood_tests bt
            JOIN donors d ON bt.donor_id = d.donor_id
            WHERE bt.hospital_id = %s
            ORDER BY bt.tested_at DESC
            LIMIT 10
        """, (hospital_id,))
        
        return jsonify({
            'hospital': convert_dates(hospital),
            'today_appointments': convert_dates(today_appointments),
            'pending_appointments': convert_dates(pending_appointments),
            'recent_tests': convert_dates(recent_tests)
        }), 200
    except Exception as e:
        print(f"Dashboard error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@hospital_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    try:
        user_id = get_jwt_identity()
        
        hospital = db.fetch_one("SELECT hospital_id FROM hospitals WHERE user_id = %s", (user_id,))
        if not hospital:
            return jsonify({'error': 'Hospital not found'}), 404
        
        hospital_id = hospital['hospital_id']
        status = request.args.get('status', '')
        
        if status:
            appointments = db.fetch_all("""
                SELECT a.appointment_id, a.donor_id, a.appointment_date, a.appointment_time, a.status,
                       d.full_name as donor_name, d.blood_group, d.phone, d.age
                FROM appointments a
                JOIN donors d ON a.donor_id = d.donor_id
                WHERE a.hospital_id = %s AND a.status = %s
                ORDER BY a.appointment_date DESC
            """, (hospital_id, status))
        else:
            appointments = db.fetch_all("""
                SELECT a.appointment_id, a.donor_id, a.appointment_date, a.appointment_time, a.status,
                       d.full_name as donor_name, d.blood_group, d.phone, d.age
                FROM appointments a
                JOIN donors d ON a.donor_id = d.donor_id
                WHERE a.hospital_id = %s
                ORDER BY a.appointment_date DESC
            """, (hospital_id,))
        
        return jsonify(convert_dates(appointments)), 200
    except Exception as e:
        print(f"Appointments error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@hospital_bp.route('/appointments/<int:appointment_id>/update', methods=['PUT'])
@jwt_required()
def update_appointment_status(appointment_id):
    try:
        user_id = get_jwt_identity()
        
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Status required'}), 400
        
        hospital = db.fetch_one("SELECT hospital_id FROM hospitals WHERE user_id = %s", (user_id,))
        if not hospital:
            return jsonify({'error': 'Hospital not found'}), 404
        
        appointment = db.fetch_one("""
            SELECT * FROM appointments WHERE appointment_id = %s AND hospital_id = %s
        """, (appointment_id, hospital['hospital_id']))
        
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        db.execute_query("""
            UPDATE appointments SET status = %s WHERE appointment_id = %s
        """, (new_status, appointment_id))
        
        # Create alert for donor
        donor_id = appointment['donor_id']
        db.execute_query("""
            INSERT INTO alerts (donor_id, alert_type, title, message, is_read)
            VALUES (%s, 'appointment', 'Appointment Update', 
                    CONCAT('Your appointment has been ', %s), FALSE)
        """, (donor_id, new_status))
        
        return jsonify({'message': f'Appointment status updated to {new_status}'}), 200
    except Exception as e:
        print(f"Update error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@hospital_bp.route('/blood-tests', methods=['GET'])
@jwt_required()
def get_blood_tests():
    try:
        user_id = get_jwt_identity()
        
        hospital = db.fetch_one("SELECT hospital_id FROM hospitals WHERE user_id = %s", (user_id,))
        if not hospital:
            return jsonify({'error': 'Hospital not found'}), 404
        
        tests = db.fetch_all("""
            SELECT bt.test_id, bt.image_path, bt.ml_cell_type, bt.ml_confidence, 
                   bt.diseases_detected, bt.is_healthy, bt.tested_at,
                   d.full_name as donor_name
            FROM blood_tests bt
            JOIN donors d ON bt.donor_id = d.donor_id
            WHERE bt.hospital_id = %s
            ORDER BY bt.tested_at DESC
            LIMIT 50
        """, (hospital['hospital_id'],))
        
        return jsonify(convert_dates(tests)), 200
    except Exception as e:
        print(f"Blood tests error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500