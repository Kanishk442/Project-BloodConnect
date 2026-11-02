# fix_passwords.py
import bcrypt
import mysql.connector

# Connect to database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='bloodconnect'
)
cursor = conn.cursor()

# Get all users
cursor.execute("SELECT user_id, email, password FROM users")
users = cursor.fetchall()

print("="*50)
print("Fixing passwords in database")
print("="*50)

for user in users:
    user_id, email, old_password = user
    
    # Check if password is already hashed (starts with $2b$)
    if not old_password.startswith('$2b$'):
        # Hash the plain text password
        hashed = bcrypt.hashpw(old_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update database
        cursor.execute("UPDATE users SET password = %s WHERE user_id = %s", (hashed, user_id))
        print(f"[OK] Updated: {email}")
    else:
        print(f"[SKIP] Already hashed: {email}")

conn.commit()
print("\n[OK] All passwords updated!")

# Verify by testing login
print("\nTesting login for john@example.com...")
cursor.execute("SELECT password FROM users WHERE email = 'john@example.com'")
result = cursor.fetchone()
if result:
    hashed = result[0]
    test_password = "password123"
    if bcrypt.checkpw(test_password.encode('utf-8'), hashed.encode('utf-8')):
        print("[OK] Login test successful!")
    else:
        print("[FAIL] Login test failed!")
else:
    print("[ERROR] User not found!")

conn.close()
print("\n[DONE] Password fix complete!")