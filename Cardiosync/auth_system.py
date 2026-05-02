"""
auth_system.py
User authentication and database management for CardioSync
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime
import os


class AuthSystem:
    """
    Handles user authentication, registration, and account management
    """
    
    def __init__(self, db_path='cardiosync_users.db'):
        """
        Initialize authentication system with database
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self._create_tables()
    
    
    def _create_tables(self):
        """
        Create database tables if they don't exist
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT,
                consent_given INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Patient data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_data (
                data_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                age INTEGER,
                sex TEXT,
                bp_systolic INTEGER,
                bp_diastolic INTEGER,
                total_cholesterol INTEGER,
                hdl INTEGER,
                ldl INTEGER,
                smoking TEXT,
                exercise_days INTEGER,
                diet_quality TEXT,
                location TEXT,
                genomic_risk REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        ''')
        
        # Risk assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_assessments (
                assessment_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                total_risk REAL NOT NULL,
                clinical_risk REAL,
                genomic_risk REAL,
                environmental_risk REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    
    def _hash_password(self, password):
        """
        Hash password using SHA-256
        
        Args:
            password (str): Plain text password
        
        Returns:
            str: Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    
    def _generate_user_id(self):
        """
        Generate unique user ID
        
        Returns:
            str: Unique user ID
        """
        return f"user_{secrets.token_hex(8)}"
    
    
    def register_user(self, email, password, full_name):
        """
        Register a new user
        
        Args:
            email (str): User's email
            password (str): User's password
            full_name (str): User's full name
        
        Returns:
            tuple: (success: bool, message: str, user_id: str or None)
        """
        # Validate inputs
        if not email or '@' not in email:
            return False, "Invalid email address", None
        
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters", None
        
        if not full_name:
            return False, "Full name is required", None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute('SELECT email FROM users WHERE email = ?', (email.lower(),))
            if cursor.fetchone():
                conn.close()
                return False, "Email already registered", None
            
            # Create new user
            user_id = self._generate_user_id()
            password_hash = self._hash_password(password)
            created_at = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO users (user_id, email, password_hash, full_name, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (user_id, email.lower(), password_hash, full_name, created_at))
            
            conn.commit()
            conn.close()
            
            return True, "Account created successfully!", user_id
        
        except Exception as e:
            return False, f"Registration failed: {str(e)}", None
    
    
    def login_user(self, email, password):
        """
        Authenticate user login
        
        Args:
            email (str): User's email
            password (str): User's password
        
        Returns:
            tuple: (success: bool, message: str, user_data: dict or None)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user by email
            cursor.execute('''
                SELECT user_id, email, password_hash, full_name, is_active
                FROM users
                WHERE email = ?
            ''', (email.lower(),))
            
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return False, "Invalid email or password", None
            
            user_id, email, stored_hash, full_name, is_active = user
            
            # Check if account is active
            if not is_active:
                conn.close()
                return False, "Account has been deactivated", None
            
            # Verify password
            password_hash = self._hash_password(password)
            if password_hash != stored_hash:
                conn.close()
                return False, "Invalid email or password", None
            
            # Update last login
            cursor.execute('''
                UPDATE users
                SET last_login = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
            
            conn.commit()
            conn.close()
            
            user_data = {
                'user_id': user_id,
                'email': email,
                'full_name': full_name
            }
            
            return True, "Login successful!", user_data
        
        except Exception as e:
            return False, f"Login failed: {str(e)}", None
    
    
    def get_user_profile(self, user_id):
        """
        Get user profile information
        
        Args:
            user_id (str): User ID
        
        Returns:
            dict or None: User profile data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, email, full_name, created_at, last_login
                FROM users
                WHERE user_id = ? AND is_active = 1
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'user_id': user[0],
                    'email': user[1],
                    'full_name': user[2],
                    'created_at': user[3],
                    'last_login': user[4]
                }
            return None
        
        except Exception as e:
            print(f"Error getting profile: {e}")
            return None
    
    
    def save_patient_data(self, user_id, patient_data):
        """
        Save or update patient health data
        
        Args:
            user_id (str): User ID
            patient_data (dict): Patient information
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if patient data already exists
            cursor.execute('SELECT data_id FROM patient_data WHERE user_id = ?', (user_id,))
            existing = cursor.fetchone()
            
            timestamp = datetime.now().isoformat()
            
            if existing:
                # Update existing data
                cursor.execute('''
                    UPDATE patient_data
                    SET age = ?, sex = ?, bp_systolic = ?, bp_diastolic = ?,
                        total_cholesterol = ?, hdl = ?, ldl = ?, smoking = ?,
                        exercise_days = ?, diet_quality = ?, location = ?,
                        genomic_risk = ?, updated_at = ?
                    WHERE user_id = ?
                ''', (
                    patient_data.get('age'),
                    patient_data.get('sex'),
                    patient_data.get('bp_systolic'),
                    patient_data.get('bp_diastolic'),
                    patient_data.get('total_cholesterol'),
                    patient_data.get('hdl'),
                    patient_data.get('ldl'),
                    patient_data.get('smoking'),
                    patient_data.get('exercise_days'),
                    patient_data.get('diet_quality'),
                    patient_data.get('location'),
                    patient_data.get('genomic_risk', 1.0),
                    timestamp,
                    user_id
                ))
            else:
                # Insert new data
                data_id = f"data_{secrets.token_hex(8)}"
                cursor.execute('''
                    INSERT INTO patient_data (
                        data_id, user_id, age, sex, bp_systolic, bp_diastolic,
                        total_cholesterol, hdl, ldl, smoking, exercise_days,
                        diet_quality, location, genomic_risk, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data_id, user_id,
                    patient_data.get('age'),
                    patient_data.get('sex'),
                    patient_data.get('bp_systolic'),
                    patient_data.get('bp_diastolic'),
                    patient_data.get('total_cholesterol'),
                    patient_data.get('hdl'),
                    patient_data.get('ldl'),
                    patient_data.get('smoking'),
                    patient_data.get('exercise_days'),
                    patient_data.get('diet_quality'),
                    patient_data.get('location'),
                    patient_data.get('genomic_risk', 1.0),
                    timestamp,
                    timestamp
                ))
            
            conn.commit()
            conn.close()
            
            return True, "Patient data saved successfully"
        
        except Exception as e:
            return False, f"Failed to save data: {str(e)}"
    
    def update_genomic_data(self, user_id, genomic_risk, genomic_genotypes):
        """Update genomic data after VCF upload"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
        
            cursor.execute('''
                UPDATE patient_data
                SET genomic_risk = ?, genomic_genotypes = ?, vcf_uploaded = 1, updated_at = ?
                WHERE user_id = ?
                ''', (genomic_risk, genomic_genotypes, timestamp, user_id))
        
            conn.commit()
            conn.close()
            return True, "Genomic data updated"
        except Exception as e:
            return False, f"Failed to update genomic data: {str(e)}"
    
    
    def get_patient_data(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            cursor.execute('''
            SELECT p.age, p.sex, p.bp_systolic, p.bp_diastolic, p.total_cholesterol,
            p.hdl, p.ldl, p.smoking, p.exercise_days, p.diet_quality, p.location,
            p.genomic_risk, p.genomic_genotypes, p.vcf_uploaded, p.updated_at, u.full_name
            FROM patient_data p
            JOIN users u ON p.user_id = u.user_id
            WHERE p.user_id = ?
            ''', (user_id,))    
        
            data = cursor.fetchone()
            conn.close()
        
            if data:
                return {
                    'full_name': data[13],
                    'age': data[0],
                    'sex': data[1],
                    'bp_systolic': data[2],
                    'bp_diastolic': data[3],
                    'total_cholesterol': data[4],
                    'hdl': data[5],
                    'ldl': data[6],
                    'smoking': data[7],
                    'exercise_days': data[8],
                    'diet_quality': data[9],
                    'location': data[10],
                    'genomic_risk': data[11],
                    'last_updated': data[12],
                    'genomic_risk': data[11],
                    'genomic_genotypes': data[12] if len(data) > 12 else None,
                    'vcf_uploaded': data[13] if len(data) > 13 else 0,
                    'last_updated': data[14] if len(data) > 14 else None,
            }
            return None
    
        except Exception as e:
            print(f"Error getting patient data: {e}")
            return None
    
    def save_risk_assessment(self, user_id, total_risk, clinical_risk, genomic_risk, environmental_risk):
        """
        Save risk assessment result
        
        Args:
            user_id (str): User ID
            total_risk (float): Total risk percentage
            clinical_risk (float): Clinical component
            genomic_risk (float): Genomic component
            environmental_risk (float): Environmental component
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            assessment_id = f"assess_{secrets.token_hex(8)}"
            timestamp = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO risk_assessments (
                    assessment_id, user_id, total_risk, clinical_risk,
                    genomic_risk, environmental_risk, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (assessment_id, user_id, total_risk, clinical_risk, genomic_risk, environmental_risk, timestamp))
            
            conn.commit()
            conn.close()
            
            return True, "Risk assessment saved"
        
        except Exception as e:
            return False, f"Failed to save assessment: {str(e)}"
    
    
    def get_risk_history(self, user_id, limit=10):
        """
        Get user's risk assessment history
        
        Args:
            user_id (str): User ID
            limit (int): Number of recent assessments to return
        
        Returns:
            list: List of risk assessments
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT total_risk, clinical_risk, genomic_risk, environmental_risk, created_at
                FROM risk_assessments
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            assessments = cursor.fetchall()
            conn.close()
            
            return [{
                'total_risk': a[0],
                'clinical_risk': a[1],
                'genomic_risk': a[2],
                'environmental_risk': a[3],
                'date': a[4]
            } for a in assessments]
        
        except Exception as e:
            print(f"Error getting risk history: {e}")
            return []
    
    
    def delete_user_account(self, user_id):
        """
        Permanently delete user account and all associated data
        
        Args:
            user_id (str): User ID to delete
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete patient data (CASCADE will handle this, but being explicit)
            cursor.execute('DELETE FROM patient_data WHERE user_id = ?', (user_id,))
            
            # Delete risk assessments
            cursor.execute('DELETE FROM risk_assessments WHERE user_id = ?', (user_id,))
            
            # Delete user account
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            
            deleted_rows = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if deleted_rows > 0:
                return True, "Account and all associated data permanently deleted"
            else:
                return False, "User not found"
        
        except Exception as e:
            return False, f"Failed to delete account: {str(e)}"
    
    
    def get_all_users_count(self):
        """
        Get total number of registered users (for admin purposes)
        
        Returns:
            int: Number of active users
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
        
        except Exception as e:
            print(f"Error counting users: {e}")
            return 0


# Example usage
if __name__ == "__main__":
    # Initialize auth system
    auth = AuthSystem()
    
    # Register a user
    success, message, user_id = auth.register_user(
        email="john@example.com",
        password="secure123",
        full_name="John Doe"
    )
    print(f"Registration: {message}")
    
    # Login
    success, message, user_data = auth.login_user(
        email="john@example.com",
        password="secure123"
    )
    print(f"Login: {message}")
    if success:
        print(f"User data: {user_data}")
    
    # Save patient data
    if user_data:
        patient_info = {
            'age': 45,
            'sex': 'Male',
            'bp_systolic': 145,
            'bp_diastolic': 90,
            'total_cholesterol': 240,
            'hdl': 35,
            'ldl': 180,
            'smoking': 'Current',
            'exercise_days': 0,
            'diet_quality': 'Poor',
            'location': 'Lagos, Nigeria',
            'genomic_risk': 1.8
        }
        
        success, message = auth.save_patient_data(user_data['user_id'], patient_info)
        print(f"Save data: {message}")
        
        # Get patient data
        retrieved = auth.get_patient_data(user_data['user_id'])
        print(f"Retrieved data: {retrieved}")
        
        # Delete account
        # success, message = auth.delete_user_account(user_data['user_id'])
        # print(f"Delete account: {message}")
    
    print(f"\nTotal users: {auth.get_all_users_count()}")