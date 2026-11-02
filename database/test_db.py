# test_db.py
import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='bloodconnect'
    )
    cursor = conn.cursor(dictionary=True)
    
    print("="*50)
    print("BLOODCONNECT DATABASE CONNECTION SUCCESSFUL!")
    print("="*50)
    
    # Show all tables
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print("\nTables in database:")
    for table in tables:
        print(f"  - {list(table.values())[0]}")
    
    # Get counts
    cursor.execute("""
        SELECT 'Users' as Name, COUNT(*) as Count FROM users
        UNION ALL SELECT 'Donors', COUNT(*) FROM donors
        UNION ALL SELECT 'Hospitals', COUNT(*) FROM hospitals
        UNION ALL SELECT 'Blood Banks', COUNT(*) FROM blood_banks
        UNION ALL SELECT 'Appointments', COUNT(*) FROM appointments
    """)
    counts = cursor.fetchall()
    print("\nRecord Counts:")
    for row in counts:
        print(f"  - {row['Name']}: {row['Count']}")
    
    # Show sample users
    cursor.execute("SELECT user_id, email, role FROM users")
    users = cursor.fetchall()
    print("\nSample Users:")
    for user in users:
        print(f"  - {user['email']} ({user['role']})")
    
    # Show sample donors
    cursor.execute("SELECT donor_id, full_name, blood_group, city FROM donors")
    donors = cursor.fetchall()
    print("\nSample Donors:")
    for donor in donors:
        print(f"  - {donor['full_name']} - {donor['blood_group']} - {donor['city']}")
    
    # Show sample hospitals
    cursor.execute("SELECT hospital_id, name, city FROM hospitals")
    hospitals = cursor.fetchall()
    print("\nSample Hospitals:")
    for hospital in hospitals:
        print(f"  - {hospital['name']} - {hospital['city']}")
    
    # Show sample appointments (fixed - no special characters)
    cursor.execute("""
        SELECT a.appointment_id, d.full_name as donor, h.name as hospital, 
               a.appointment_date, a.status
        FROM appointments a
        JOIN donors d ON a.donor_id = d.donor_id
        JOIN hospitals h ON a.hospital_id = h.hospital_id
    """)
    appointments = cursor.fetchall()
    print("\nSample Appointments:")
    for apt in appointments:
        print(f"  - {apt['donor']} -> {apt['hospital']} on {apt['appointment_date']} ({apt['status']})")
    
    # Show blood bank inventory
    cursor.execute("SELECT name, city, o_positive, a_positive FROM blood_banks")
    banks = cursor.fetchall()
    print("\nBlood Bank Inventory:")
    for bank in banks:
        print(f"  - {bank['name']} ({bank['city']})")
        print(f"    O+: {bank['o_positive']} units | A+: {bank['a_positive']} units")
    
    conn.close()
    print("\n" + "="*50)
    print("Database test passed! Ready for backend development.")
    print("="*50)
    
except Exception as e:
    print(f"Error: {e}")