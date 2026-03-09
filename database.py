import sqlite3
from datetime import datetime
import os

class EDTShuttleDB:
    def __init__(self, db_name=None):
        """
        Initialize database connection
        
        Works with both SQLite (local) and PostgreSQL (cloud)
        """
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            self.db_name = db_name or 'edt_shuttle.db'
        else:
            self.db_name = db_name or 'edt_shuttle.db'
        
        self.create_tables()
    
    def create_tables(self):
        """Create all necessary tables if they don't exist"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                phone_number TEXT PRIMARY KEY,
                name TEXT,
                rides_left INTEGER DEFAULT 0,
                total_spent REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Drivers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drivers (
                phone_number TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                preferred_contact TEXT DEFAULT 'whatsapp',
                current_zone TEXT DEFAULT 'Campus',
                is_available INTEGER DEFAULT 1,
                device_type TEXT DEFAULT 'smartphone',
                vehicle_type TEXT DEFAULT 'Keke',
                total_rides_completed INTEGER DEFAULT 0,
                total_earnings REAL DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Rides table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_phone TEXT,
                destination TEXT,
                cost REAL,
                driver_phone TEXT,
                driver_name TEXT,
                status TEXT DEFAULT 'completed',
                seats_total INTEGER DEFAULT 1,
                seats_booked INTEGER DEFAULT 1,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_phone) REFERENCES users (phone_number),
                FOREIGN KEY (driver_phone) REFERENCES drivers (phone_number)
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_phone TEXT,
                type TEXT,
                amount REAL,
                rides_added INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_phone) REFERENCES users (phone_number)
            )
        ''')
        
        # Active trips table (for shared rides)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_phone TEXT,
                driver_name TEXT,
                destination TEXT,
                seats_total INTEGER DEFAULT 4,
                seats_available INTEGER DEFAULT 4,
                status TEXT DEFAULT 'active',
                departure_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (driver_phone) REFERENCES drivers (phone_number)
            )
        ''')
        
        # Pending dispatch table (for timeout tracking)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_dispatch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ride_id INTEGER,
                driver_phone TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (ride_id) REFERENCES rides (id),
                FOREIGN KEY (driver_phone) REFERENCES drivers (phone_number)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ==================== USER FUNCTIONS ====================
    
    def create_user(self, phone_number):
        """Create a new user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (phone_number)
            VALUES (?)
        ''', (phone_number,))
        
        conn.commit()
        conn.close()
    
    def get_user(self, phone_number):
        """Get user details"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT phone_number, name, rides_left, total_spent, created_at, last_active
            FROM users
            WHERE phone_number = ?
        ''', (phone_number,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'phone_number': result[0],
                'name': result[1],
                'rides_left': result[2],
                'total_spent': result[3],
                'created_at': result[4],
                'last_active': result[5]
            }
        return None
    
    def update_user_name(self, phone_number, name):
        """Update user's name"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET name = ?, last_active = CURRENT_TIMESTAMP
            WHERE phone_number = ?
        ''', (name, phone_number))
        
        conn.commit()
        conn.close()
    
    def add_rides(self, phone_number, rides):
        """Add rides to user's balance"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET rides_left = rides_left + ?,
                last_active = CURRENT_TIMESTAMP
            WHERE phone_number = ?
        ''', (rides, phone_number))
        
        conn.commit()
        conn.close()
    
    def use_ride(self, phone_number):
        """Deduct one ride from user's balance"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET rides_left = rides_left - 1,
                last_active = CURRENT_TIMESTAMP
            WHERE phone_number = ?
        ''', (phone_number,))
        
        conn.commit()
        conn.close()
    
    def record_ride(self, user_phone, destination, cost, driver_phone=None, driver_name=None):
        """Record a completed ride"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO rides (user_phone, destination, cost, driver_phone, driver_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_phone, destination, cost, driver_phone, driver_name))
        
        conn.commit()
        conn.close()
    
    def get_user_rides(self, phone_number, limit=10):
        """Get user's ride history"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT destination, cost, timestamp
            FROM rides
            WHERE user_phone = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (phone_number, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def record_transaction(self, phone_number, transaction_type, amount, rides_added=0):
        """Record a transaction (purchase, refund, etc.)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions (user_phone, type, amount, rides_added)
            VALUES (?, ?, ?, ?)
        ''', (phone_number, transaction_type, amount, rides_added))
        
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """Get overall platform statistics"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM rides')
        total_rides = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(amount) FROM transactions WHERE type = "purchase"')
        total_revenue = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT COUNT(*) FROM rides 
            WHERE DATE(timestamp) = DATE('now')
        ''')
        today_rides = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'total_rides': total_rides,
            'total_revenue': total_revenue,
            'today_rides': today_rides
        }
    
    # ==================== ADMIN FUNCTIONS ====================
    
    def get_all_users(self, limit=50):
        """Get all users (admin function)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, phone_number, rides_left, total_spent, created_at
            FROM users
            ORDER BY total_spent DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_low_balance_users(self, threshold=3):
        """Get users with low ride balance"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, phone_number, rides_left
            FROM users
            WHERE rides_left < ?
            ORDER BY rides_left ASC
        ''', (threshold,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_today_activity(self):
        """Get today's rides and purchases"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.destination, u.name, r.timestamp
            FROM rides r
            JOIN users u ON r.user_phone = u.phone_number
            WHERE DATE(r.timestamp) = DATE('now')
            ORDER BY r.timestamp DESC
        ''')
        rides = cursor.fetchall()
        
        cursor.execute('''
            SELECT u.name, t.rides_added, t.amount, t.timestamp
            FROM transactions t
            JOIN users u ON t.user_phone = u.phone_number
            WHERE DATE(t.timestamp) = DATE('now') AND t.type = 'purchase'
            ORDER BY t.timestamp DESC
        ''')
        purchases = cursor.fetchall()
        
        conn.close()
        
        return rides, purchases
    
    # ==================== DRIVER FUNCTIONS ====================
    
    def add_driver(self, name, phone_number, preferred_contact='whatsapp', 
                   current_zone='Campus', device_type='smartphone', vehicle_type='Keke'):
        """Add a new driver to the system"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO drivers (name, phone_number, preferred_contact, current_zone, device_type, vehicle_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, phone_number, preferred_contact, current_zone, device_type, vehicle_type))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def get_driver(self, phone_number):
        """Get driver details"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, phone_number, preferred_contact, current_zone, is_available, 
                   device_type, vehicle_type, total_rides_completed, total_earnings
            FROM drivers
            WHERE phone_number = ?
        ''', (phone_number,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'name': result[0],
                'phone_number': result[1],
                'preferred_contact': result[2],
                'current_zone': result[3],
                'is_available': result[4],
                'device_type': result[5],
                'vehicle_type': result[6],
                'total_rides_completed': result[7],
                'total_earnings': result[8]
            }
        return None
    
    def get_available_drivers(self, zone=None, vehicle_type=None):
        """Get available drivers, optionally filtered by zone and vehicle type"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        query = '''
            SELECT name, phone_number, preferred_contact, device_type, vehicle_type
            FROM drivers
            WHERE is_available = 1
        '''
        params = []
        
        if zone:
            query += ' AND current_zone = ?'
            params.append(zone)
        
        if vehicle_type:
            query += ' AND vehicle_type = ?'
            params.append(vehicle_type)
        
        query += ' ORDER BY total_rides_completed ASC'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_all_drivers(self):
        """Get all registered drivers (admin function)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, phone_number, preferred_contact, current_zone, is_available,
                   device_type, vehicle_type, total_rides_completed, total_earnings
            FROM drivers
            ORDER BY total_rides_completed DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def mark_driver_busy(self, phone_number):
        """Mark driver as busy/unavailable"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE drivers
            SET is_available = 0
            WHERE phone_number = ?
        ''', (phone_number,))
        
        conn.commit()
        conn.close()
    
    def mark_driver_available(self, phone_number):
        """Mark driver as available"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE drivers
            SET is_available = 1
            WHERE phone_number = ?
        ''', (phone_number,))
        
        conn.commit()
        conn.close()
    
    def update_driver_zone(self, phone_number, new_zone):
        """Update driver's current zone"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE drivers
            SET current_zone = ?
            WHERE phone_number = ?
        ''', (new_zone, phone_number))
        
        conn.commit()
        conn.close()
    
    def update_driver_earnings(self, phone_number, amount):
        """Update driver's earnings and ride count"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE drivers
            SET total_earnings = total_earnings + ?,
                total_rides_completed = total_rides_completed + 1
            WHERE phone_number = ?
        ''', (amount, phone_number))
        
        conn.commit()
        conn.close()
    
    def update_ride_status(self, ride_id, status):
        """Update the status of a ride"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE rides
            SET status = ?
            WHERE id = ?
        ''', (status, ride_id))
        
        conn.commit()
        conn.close()
    
    def get_pending_ride_for_driver(self, driver_phone):
        """Get pending ride assignment for a driver"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pd.id, pd.ride_id, r.destination, r.user_phone
            FROM pending_dispatch pd
            JOIN rides r ON pd.ride_id = r.id
            WHERE pd.driver_phone = ? AND pd.status = 'pending'
            ORDER BY pd.sent_at ASC
            LIMIT 1
        ''', (driver_phone,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result
    
    # ==================== ACTIVE TRIPS (SHARED RIDES) ====================
    
    def create_active_trip(self, driver_phone, driver_name, destination, seats_total=4):
        """Create a new active trip for shared rides"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO active_trips (driver_phone, driver_name, destination, seats_total, seats_available)
            VALUES (?, ?, ?, ?, ?)
        ''', (driver_phone, driver_name, destination, seats_total, seats_total - 1))
        
        conn.commit()
        conn.close()
    
    def get_active_trips(self, destination=None):
        """Get active trips, optionally filtered by destination"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        if destination:
            cursor.execute('''
                SELECT id, driver_phone, driver_name, destination, seats_total, seats_available, departure_time
                FROM active_trips
                WHERE destination = ? AND status = 'active' AND seats_available > 0
                ORDER BY departure_time DESC
            ''', (destination,))
        else:
            cursor.execute('''
                SELECT id, driver_phone, driver_name, destination, seats_total, seats_available, departure_time
                FROM active_trips
                WHERE status = 'active' AND seats_available > 0
                ORDER BY departure_time DESC
            ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def book_seat_in_trip(self, trip_id):
        """Book a seat in an active trip"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE active_trips
            SET seats_available = seats_available - 1
            WHERE id = ? AND seats_available > 0
        ''', (trip_id,))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rows_affected > 0
    
    def close_trip(self, trip_id):
        """Close an active trip"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE active_trips
            SET status = 'completed'
            WHERE id = ?
        ''', (trip_id,))
        
        conn.commit()
        conn.close()
    
    # ==================== PENDING DISPATCH ====================
    
    def create_pending_dispatch(self, ride_id, driver_phone):
        """Create a pending dispatch record"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pending_dispatch (ride_id, driver_phone)
            VALUES (?, ?)
        ''', (ride_id, driver_phone))
        
        conn.commit()
        conn.close()
    
    def update_dispatch_status(self, dispatch_id, status):
        """Update dispatch status"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE pending_dispatch
            SET status = ?
            WHERE id = ?
        ''', (status, dispatch_id))
        
        conn.commit()
        conn.close()
    
    def get_expired_pending_dispatches(self, timeout_seconds=60):
        """Get dispatches that have exceeded timeout"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, ride_id, driver_phone
            FROM pending_dispatch
            WHERE status = 'pending' 
            AND (julianday('now') - julianday(sent_at)) * 86400 > ?
        ''', (timeout_seconds,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results