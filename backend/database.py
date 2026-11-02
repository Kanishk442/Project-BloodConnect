# database.py - pooled MySQL access (works with local MySQL and TiDB Cloud)
import os
import threading

import bcrypt
import mysql.connector
from mysql.connector import Error, pooling

from config import Config


def _ssl_args():
    if not Config.MYSQL_SSL:
        return {}
    ca = Config.MYSQL_SSL_CA
    if not ca:
        for candidate in ('/etc/ssl/certs/ca-certificates.crt', '/etc/pki/tls/certs/ca-bundle.crt'):
            if os.path.exists(candidate):
                ca = candidate
                break
    args = {'ssl_disabled': False, 'ssl_verify_cert': bool(ca)}
    if ca:
        args['ssl_ca'] = ca
    return args


class Database:
    """Connection-pool wrapper. Connections are created lazily and re-established automatically."""

    def __init__(self):
        self._pool = None
        self._lock = threading.Lock()

    def _get_pool(self):
        if self._pool is None:
            with self._lock:
                if self._pool is None:
                    self._pool = pooling.MySQLConnectionPool(
                        pool_name='bloodconnect',
                        pool_size=Config.MYSQL_POOL_SIZE,
                        pool_reset_session=True,
                        host=Config.MYSQL_HOST,
                        port=Config.MYSQL_PORT,
                        user=Config.MYSQL_USER,
                        password=Config.MYSQL_PASSWORD,
                        database=Config.MYSQL_DATABASE,
                        connection_timeout=10,
                        **_ssl_args(),
                    )
        return self._pool

    def _conn(self):
        conn = self._get_pool().get_connection()
        conn.ping(reconnect=True, attempts=2, delay=1)   # recover from idle timeouts
        return conn

    def is_connected(self):
        try:
            conn = self._conn()
            conn.close()
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False

    # kept for backwards compatibility with older code (`if not db.connection`)
    @property
    def connection(self):
        return self.is_connected()

    def execute_query(self, query, params=None):
        """INSERT -> returns lastrowid; UPDATE/DELETE -> True; error -> None."""
        try:
            conn = self._conn()
        except Error as e:
            print(f"Query error (connect): {e}")
            return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            conn.commit()
            if query.strip().upper().startswith("INSERT"):
                return cursor.lastrowid
            return True
        except Error as e:
            print(f"Query error: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

    def fetch_one(self, query, params=None):
        try:
            conn = self._conn()
        except Error as e:
            print(f"Fetch one error (connect): {e}")
            return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except Error as e:
            print(f"Fetch one error: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    def fetch_all(self, query, params=None):
        try:
            conn = self._conn()
        except Error as e:
            print(f"Fetch all error (connect): {e}")
            return []
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            print(f"Fetch all error: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

    def hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password, hashed):
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def close(self):
        self._pool = None


# Global instance (no connection is made until first query)
db = Database()
