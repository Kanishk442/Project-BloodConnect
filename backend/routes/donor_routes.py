# routes/donor_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from datetime import datetime, timedelta

donor_bp = Blueprint('donor', __name__)

def convert_dates(obj):
    """Convert datetime objects to strings for JSON serialization"""
    if isinstance(obj, dict):
        return {k: convert_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates(item) for item in obj]
    elif isinstance(obj, (datetime, timedelta)):
        return str(obj)
    return obj

@donor_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    user_id = get_jwt_identity()
    
    # Get donor from user_id
    donor = db.fetch_one("SELECT * FROM donors WHERE user_id = %s", (user_id,))
    if not donor:
        return jsonify({'error': 'Donor not found'}), 404
    
    # Convert datetime objects in donor
    donor = convert_dates(donor)
    
    # Get unread alerts count
    alerts = db.fetch_one("SELECT COUNT(*) as count FROM alerts WHERE donor_id = %s AND is_read = FALSE", (donor['donor_id'],))
    
    # Get upcoming appointments
    appointments = db.fetch_all("""
        SELECT a.*, h.name as hospital_name, h.address as hospital_address
        FROM appointments a
        JOIN hospitals h ON a.hospital_id = h.hospital_id
        WHERE a.donor_id = %s AND a.status IN ('pending', 'confirmed')
        ORDER BY a.appointment_date ASC
        LIMIT 5
    """, (donor['donor_id'],))
    
    # Get recent donations
    recent_donations = db.fetch_all("""
        SELECT d.*, h.name as hospital_name
        FROM donations d
        JOIN hospitals h ON d.hospital_id = h.hospital_id
        WHERE d.donor_id = %s
        ORDER BY d.donation_date DESC
        LIMIT 5
    """, (donor['donor_id'],))
    
    # Convert datetime objects
    appointments = convert_dates(appointments)
    recent_donations = convert_dates(recent_donations)
    
    return jsonify({
        'donor': donor,
        'unread_alerts': alerts['count'] if alerts else 0,
        'upcoming_appointments': appointments,
        'recent_donations': recent_donations
    }), 200

@donor_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    user_id = get_jwt_identity()
    
    donor = db.fetch_one("SELECT donor_id FROM donors WHERE user_id = %s", (user_id,))
    if not donor:
        return jsonify({'error': 'Donor not found'}), 404
    
    appointments = db.fetch_all("""
        SELECT a.*, h.name as hospital_name, h.address, h.phone as hospital_phone
        FROM appointments a
        JOIN hospitals h ON a.hospital_id = h.hospital_id
        WHERE a.donor_id = %s
        ORDER BY a.appointment_date DESC
    """, (donor['donor_id'],))
    
    # Convert datetime objects to strings
    appointments = convert_dates(appointments)
    
    return jsonify(appointments), 200

@donor_bp.route('/appointments/book', methods=['POST'])
@jwt_required()
def book_appointment():
    user_id = int(get_jwt_identity())
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data received'}), 400
    hospital_id = data.get('hospital_id')
    appointment_date = data.get('appointment_date')
    appointment_time = data.get('appointment_time')
    notes = data.get('notes', '')
    
    if not hospital_id or not appointment_date or not appointment_time:
        return jsonify({'error': 'Missing required fields'}), 400
    
    donor = db.fetch_one("SELECT donor_id FROM donors WHERE user_id = %s", (user_id,))
    if not donor:
        return jsonify({'error': 'Donor not found'}), 404
    
    # Check for duplicate appointment
    existing = db.fetch_one("""
        SELECT * FROM appointments 
        WHERE donor_id = %s AND appointment_date = %s AND status != 'cancelled'
    """, (donor['donor_id'], appointment_date))
    
    if existing:
        return jsonify({'error': 'You already have an appointment on this date'}), 400
    
    # Insert appointment
    appointment_id = db.execute_query("""
    INSERT INTO appointments 
    (donor_id, hospital_id, appointment_date, appointment_time, notes, status)
    VALUES (%s, %s, %s, %s, %s, 'pending')
""", (donor['donor_id'], hospital_id, appointment_date, appointment_time, notes))
    
    # Create notification alert for donor
    db.execute_query("""
    INSERT INTO alerts (donor_id, alert_type, title, message, is_read)
    VALUES (%s, 'appointment', 'Appointment Request Submitted', 
            CONCAT('Your appointment request for ', %s, ' at ', %s, ' has been submitted. Awaiting confirmation.'), FALSE)
""", (donor['donor_id'], appointment_date, appointment_time))

    return jsonify({
    'message': 'Appointment booked successfully',
    'appointment_id': appointment_id
}), 201

@donor_bp.route('/appointments/<int:appointment_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_appointment(appointment_id):
    user_id = int(get_jwt_identity())
    
    donor = db.fetch_one("SELECT donor_id FROM donors WHERE user_id = %s", (user_id,))
    if not donor:
        return jsonify({'error': 'Donor not found'}), 404
    
    # Check if appointment exists and belongs to donor
    appointment = db.fetch_one("""
        SELECT * FROM appointments 
        WHERE appointment_id = %s AND donor_id = %s AND status = 'pending'
    """, (appointment_id, donor['donor_id']))
    
    if not appointment:
        return jsonify({'error': 'Appointment not found or cannot be cancelled'}), 404
    
    # Update appointment status
    db.execute_query("""
        UPDATE appointments SET status = 'cancelled'
        WHERE appointment_id = %s
    """, (appointment_id,))
    
    # Create cancellation alert
    db.execute_query("""
    INSERT INTO alerts (donor_id, alert_type, title, message, is_read)
    VALUES (%s, 'appointment', 'Appointment Cancelled', 
            CONCAT('Your appointment for ', %s, ' has been cancelled.'), FALSE)
""", (donor['donor_id'], appointment['appointment_date']))

    return jsonify({'message': 'Appointment cancelled successfully'}), 200

@donor_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    user_id = get_jwt_identity()
    
    donor = db.fetch_one("SELECT donor_id FROM donors WHERE user_id = %s", (user_id,))
    if not donor:
        return jsonify({'error': 'Donor not found'}), 404
    
    alerts = db.fetch_all("""
        SELECT * FROM alerts
        WHERE donor_id = %s
        ORDER BY created_at DESC
    """, (donor['donor_id'],))
    
    # Convert datetime objects
    alerts = convert_dates(alerts)
    
    return jsonify(alerts), 200

@donor_bp.route('/alerts/<int:alert_id>/read', methods=['PUT'])
@jwt_required()
def mark_alert_read(alert_id):
    user_id = get_jwt_identity()
    
    donor = db.fetch_one("SELECT donor_id FROM donors WHERE user_id = %s", (user_id,))
    if not donor:
        return jsonify({'error': 'Donor not found'}), 404
    
    db.execute_query("""
        UPDATE alerts SET is_read = TRUE, read_at = NOW()
        WHERE alert_id = %s AND donor_id = %s
    """, (alert_id, donor['donor_id']))
    
    return jsonify({'message': 'Alert marked as read'}), 200

@donor_bp.route('/alerts/mark-all-read', methods=['PUT'])
@jwt_required()
def mark_all_alerts_read():
    user_id = get_jwt_identity()
    
    donor = db.fetch_one("SELECT donor_id FROM donors WHERE user_id = %s", (user_id,))
    if not donor:
        return jsonify({'error': 'Donor not found'}), 404
    
    db.execute_query("""
        UPDATE alerts SET is_read = TRUE, read_at = NOW()
        WHERE donor_id = %s AND is_read = FALSE
    """, (donor['donor_id'],))
    
    return jsonify({'message': 'All alerts marked as read'}), 200

@donor_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
@jwt_required()
def delete_alert(alert_id):
    user_id = get_jwt_identity()
    
    donor = db.fetch_one("SELECT donor_id FROM donors WHERE user_id = %s", (user_id,))
    if not donor:
        return jsonify({'error': 'Donor not found'}), 404
    
    db.execute_query("""
        DELETE FROM alerts
        WHERE alert_id = %s AND donor_id = %s
    """, (alert_id, donor['donor_id']))
    
    return jsonify({'message': 'Alert deleted successfully'}), 200

@donor_bp.route('/badges', methods=['GET'])
@jwt_required()
def get_badges():
    """Get donor badges with unlock status"""
    user_id = get_jwt_identity()
    
    donor = db.fetch_one("SELECT donor_id, donation_count FROM donors WHERE user_id = %s", (user_id,))
    if not donor:
        return jsonify({'error': 'Donor not found'}), 404
    
    donation_count = donor['donation_count'] or 0
    
    # Get earned badges from database
    earned_badges = db.fetch_all("""
        SELECT badge_name, badge_icon, badge_message, awarded_at
        FROM badges
        WHERE donor_id = %s
    """, (donor['donor_id'],))
    
    earned_badge_names = [badge['badge_name'] for badge in earned_badges]
    
    # Define all badges
    badge_definitions = [
        {
            'id': 1,
            'name': 'First Blood',
            'icon': '🩸',
            'description': 'First successful donation',
            'required': 1,
            'unlocked': donation_count >= 1,
            'unlocked_date': next((b['awarded_at'] for b in earned_badges if b['badge_name'] == 'First Blood'), None)
        },
        {
            'id': 2,
            'name': 'Lifesaver',
            'icon': '💪',
            'description': '3 donations completed',
            'required': 3,
            'unlocked': donation_count >= 3,
            'unlocked_date': next((b['awarded_at'] for b in earned_badges if b['badge_name'] == 'Lifesaver'), None)
        },
        {
            'id': 3,
            'name': 'Hero Badge',
            'icon': '🏆',
            'description': '5+ donations - Elite donor',
            'required': 5,
            'unlocked': donation_count >= 5,
            'unlocked_date': next((b['awarded_at'] for b in earned_badges if b['badge_name'] == 'Hero Badge'), None)
        },
        {
            'id': 4,
            'name': 'Platinum Donor',
            'icon': '💎',
            'description': '10+ donations - Platinum status',
            'required': 10,
            'unlocked': donation_count >= 10,
            'unlocked_date': next((b['awarded_at'] for b in earned_badges if b['badge_name'] == 'Platinum Donor'), None)
        }
    ]
    
    # Convert datetime objects
    badge_definitions = convert_dates(badge_definitions)
    
    return jsonify(badge_definitions), 200

@donor_bp.route('/badges/check', methods=['GET'])
@jwt_required()
def check_badge_eligibility():
    """Check if new badges are earned"""
    user_id = get_jwt_identity()
    
    donor = db.fetch_one("SELECT donor_id, donation_count FROM donors WHERE user_id = %s", (user_id,))
    if not donor:
        return jsonify({'error': 'Donor not found'}), 404
    
    donation_count = donor['donation_count'] or 0
    new_badges = []
    
    # Get already earned badges
    earned_badges = db.fetch_all("""
        SELECT badge_name FROM badges WHERE donor_id = %s
    """, (donor['donor_id'],))
    
    earned_names = [b['badge_name'] for b in earned_badges]
    
    # Check each badge threshold
    badge_thresholds = [
        {'threshold': 1, 'name': 'First Blood', 'icon': '🩸', 'message': 'Congratulations on your first donation! 🎉'},
        {'threshold': 3, 'name': 'Lifesaver', 'icon': '💪', 'message': 'You\'ve saved 3 lives! Thank you for your generosity!'},
        {'threshold': 5, 'name': 'Hero Badge', 'icon': '🏆', 'message': 'Hero Badge Unlocked! You\'re a true hero!'},
        {'threshold': 10, 'name': 'Platinum Donor', 'icon': '💎', 'message': 'Platinum Donor Status Achieved! You\'re an inspiration!'}
    ]
    
    for badge in badge_thresholds:
        if donation_count >= badge['threshold'] and badge['name'] not in earned_names:
            # Award the badge
            db.execute_query("""
                INSERT INTO badges (donor_id, badge_name, badge_icon, badge_message)
                VALUES (%s, %s, %s, %s)
            """, (donor['donor_id'], badge['name'], badge['icon'], badge['message']))
            
            # Create alert for the badge
            db.execute_query("""
                INSERT INTO alerts (donor_id, alert_type, title, message, is_read)
                VALUES (%s, 'badge', CONCAT('Badge Earned: ', %s), %s, FALSE)
            """, (donor['donor_id'], badge['name'], badge['message']))
            
            new_badges.append(badge)
    
    return jsonify({
        'new_badges': new_badges,
        'donation_count': donation_count
    }), 200

@donor_bp.route('/donations', methods=['GET'])
@jwt_required()
def get_donation_history():
    """Get donation history"""
    user_id = get_jwt_identity()
    
    donor = db.fetch_one("SELECT donor_id FROM donors WHERE user_id = %s", (user_id,))
    if not donor:
        return jsonify({'error': 'Donor not found'}), 404
    
    donations = db.fetch_all("""
        SELECT d.*, h.name as hospital_name
        FROM donations d
        JOIN hospitals h ON d.hospital_id = h.hospital_id
        WHERE d.donor_id = %s
        ORDER BY d.donation_date DESC
    """, (donor['donor_id'],))
    
    # Convert datetime objects
    donations = convert_dates(donations)
    
    return jsonify(donations), 200

@donor_bp.route('/hospitals/nearby', methods=['GET'])
def get_nearby_hospitals():
    city = request.args.get('city', '')
    
    if not city:
        hospitals = db.fetch_all("SELECT * FROM hospitals WHERE is_verified = TRUE LIMIT 20")
    else:
        hospitals = db.fetch_all("SELECT * FROM hospitals WHERE city LIKE %s AND is_verified = TRUE", (f'%{city}%',))
    
    # Convert datetime objects
    hospitals = convert_dates(hospitals)
    
    return jsonify(hospitals), 200

@donor_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """Get donor statistics"""
    user_id = get_jwt_identity()
    
    donor = db.fetch_one("SELECT donor_id, donation_count FROM donors WHERE user_id = %s", (user_id,))
    if not donor:
        return jsonify({'error': 'Donor not found'}), 404
    
    # Get total donations count
    total_donations = donor['donation_count'] or 0
    
    # Get total blood donated
    total_blood = db.fetch_one("""
        SELECT COALESCE(SUM(quantity_ml), 0) as total_ml
        FROM donations
        WHERE donor_id = %s
    """, (donor['donor_id'],))
    
    # Get number of lives saved (assuming each donation saves 3 lives)
    lives_saved = total_donations * 3
    
    # Get last donation date
    last_donation = db.fetch_one("""
        SELECT donation_date
        FROM donations
        WHERE donor_id = %s
        ORDER BY donation_date DESC
        LIMIT 1
    """, (donor['donor_id'],))
    
    return jsonify({
        'total_donations': total_donations,
        'total_blood_ml': total_blood['total_ml'] if total_blood else 0,
        'lives_saved': lives_saved,
        'last_donation_date': convert_dates(last_donation['donation_date']) if last_donation else None,
        'next_milestone': get_next_milestone(total_donations)
    }), 200

def get_next_milestone(current_donations):
    """Get next badge milestone"""
    milestones = [1, 3, 5, 10]
    for milestone in milestones:
        if current_donations < milestone:
            return {
                'required': milestone,
                'remaining': milestone - current_donations,
                'badge_name': get_badge_name(milestone)
            }
    return None

def get_badge_name(threshold):
    """Get badge name for threshold"""
    badges = {
        1: 'First Blood',
        3: 'Lifesaver',
        5: 'Hero Badge',
        10: 'Platinum Donor'
    }
    return badges.get(threshold, 'Next Badge')