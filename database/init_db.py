"""Create tables (and optional demo data) on whatever DB the env vars point to.
   python database/init_db.py          -> schema only
   python database/init_db.py --demo   -> schema + demo donor/hospital accounts (password: Demo@1234)
"""
import os, sys, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import db  # noqa: E402

def run_schema():
    sql = open(os.path.join(os.path.dirname(__file__), 'schema.sql'), encoding='utf-8').read()
    sql = re.sub(r'--.*', '', sql)
    for stmt in filter(None, (s.strip() for s in sql.split(';'))):
        if db.execute_query(stmt) is None:
            sys.exit(f'Failed: {stmt[:60]}...')
    print('Schema ready.')

def seed_demo():
    if db.fetch_one("SELECT user_id FROM users WHERE email=%s", ('donor@demo.com',)):
        return print('Demo data already present.')
    pw = db.hash_password('Demo@1234')
    du = db.execute_query("INSERT INTO users (email,password,role) VALUES (%s,%s,'donor')", ('donor@demo.com', pw))
    db.execute_query("INSERT INTO donors (user_id,full_name,age,blood_group,weight_kg,phone,city) VALUES (%s,'Demo Donor',28,'O+',70,'9999999999','Bhopal')", (du,))
    hu = db.execute_query("INSERT INTO users (email,password,role) VALUES (%s,%s,'hospital')", ('hospital@demo.com', pw))
    db.execute_query("INSERT INTO hospitals (user_id,name,license_number,address,city,phone,is_verified) VALUES (%s,'Demo City Hospital','LIC-0001','MP Nagar','Bhopal','8888888888',TRUE)", (hu,))
    db.execute_query("INSERT INTO blood_banks (name,city,a_positive,b_positive,o_positive,ab_positive) VALUES ('City Blood Bank','Bhopal',12,9,20,4)")
    print('Demo accounts: donor@demo.com / hospital@demo.com  (password Demo@1234)')

if __name__ == '__main__':
    if not db.is_connected():
        sys.exit('Cannot connect to the database - check MYSQL_* environment variables.')
    run_schema()
    if '--demo' in sys.argv:
        seed_demo()
