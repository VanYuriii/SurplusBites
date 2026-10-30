import sqlite3
import uuid
import json
import math
from typing import List, Optional
from datetime import datetime
from models.user import Donor, Recipient, User
from models.listing import FoodListing
from models.transaction import DonationTransaction

class PlatformManager:
    """
    Controller class managing the state and business logic of the SurplusBite platform.
    Uses SQLite for data persistence.
    """
    def __init__(self, db_path="surplusbite.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._observers: List[Recipient] = []
        self._initialize_database()
        self._seed_mock_users()

    def _initialize_database(self):
        """Creates the necessary tables if they do not exist."""
        cursor = self.conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                password TEXT,
                role TEXT,
                name TEXT,
                contact_info TEXT,
                address TEXT,
                specific_id TEXT
            )
        ''')
        
        # Try to add columns to existing users table
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN password TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN latitude REAL DEFAULT 0.0")
            cursor.execute("ALTER TABLE users ADD COLUMN longitude REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass
        
        # Create listings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS listings (
                listing_id TEXT PRIMARY KEY,
                donor_id TEXT,
                items TEXT,
                status TEXT,
                pickup_window TEXT,
                expires_at TEXT
            )
        ''')
        
        try:
            cursor.execute("ALTER TABLE listings ADD COLUMN expires_at TEXT")
        except sqlite3.OperationalError:
            pass
        
        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                listing_id TEXT,
                recipient_id TEXT,
                driver_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN driver_id TEXT")
        except sqlite3.OperationalError:
            pass
        
        # Create ratings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
                rater_id TEXT,
                ratee_id TEXT,
                listing_id TEXT,
                score INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Try to add listing_id column to existing ratings table
        try:
            cursor.execute("ALTER TABLE ratings ADD COLUMN listing_id TEXT")
        except sqlite3.OperationalError:
            pass # Column already exists
            
        self.conn.commit()

    def _seed_mock_users(self):
        cursor = self.conn.cursor()
        # Matina coordinates: ~ 7.065, 125.595
        # Agdao coordinates: ~ 7.085, 125.620
        mocks = [
            ('donor_matina', 'pass', 'Donor', 'Matina Bakery', 'contact1', 'Matina', 'TAX-1', 7.065, 125.595),
            ('recip_matina', 'pass', 'Recipient', 'Matina Orphanage', 'contact2', 'Matina', 'REG-1', 7.066, 125.596),
            ('recip_agdao', 'pass', 'Recipient', 'Agdao Shelter', 'contact3', 'Agdao', 'REG-2', 7.085, 125.620)
        ]
        for mock in mocks:
            try:
                cursor.execute(
                    'INSERT INTO users (user_id, password, role, name, contact_info, address, specific_id, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    mock
                )
            except sqlite3.IntegrityError:
                pass
        self.conn.commit()

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great-circle distance between two points in km."""
        R = 6371.0 # Radius of the Earth in km
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def attach_observer(self, recipient: Recipient):
        if recipient not in self._observers:
            self._observers.append(recipient)

    def detach_observer(self, recipient: Recipient):
        if recipient in self._observers:
            self._observers.remove(recipient)

    def notify_recipients(self, listing: FoodListing):
        cursor = self.conn.cursor()
        cursor.execute("SELECT latitude, longitude FROM users WHERE user_id = ?", (listing.donor_id,))
        donor_row = cursor.fetchone()
        if not donor_row:
            return
            
        donor_lat, donor_lon = donor_row['latitude'], donor_row['longitude']
        
        # In a real app, max radius could be a setting per recipient, we'll use a 5km default
        for recipient in self._observers:
            dist = self.calculate_distance(donor_lat, donor_lon, recipient.latitude, recipient.longitude)
            if dist <= 5.0:
                recipient.update(listing)

    def add_rating(self, rater_id: str, ratee_id: str, listing_id: str, score: int):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO ratings (rater_id, ratee_id, listing_id, score) VALUES (?, ?, ?, ?)',
            (rater_id, ratee_id, listing_id, score)
        )
        self.conn.commit()
        
    def has_user_rated_listing(self, rater_id: str, listing_id: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM ratings WHERE rater_id = ? AND listing_id = ?', (rater_id, listing_id))
        return cursor.fetchone() is not None

    def get_average_rating(self, user_id: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute('SELECT AVG(score), COUNT(score) FROM ratings WHERE ratee_id = ?', (user_id,))
        row = cursor.fetchone()
        avg, count = row[0], row[1]
        if avg is None:
            return "No ratings yet"
        return f"{avg:.1f} / 5.0 ({count} ratings)"

    def register_user(self, role: str, user_id: str, password: str, name: str, contact: str, address: str, specific_id: str):
        """Registers a new user in the database."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (user_id, password, role, name, contact_info, address, specific_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (user_id, password, role, name, contact, address, specific_id)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            raise ValueError(f"User ID '{user_id}' already exists.")

    def authenticate(self, user_id: str, password: str):
        """Authenticates a user by their user_id and password, returning the appropriate User model."""
        cursor = self.conn.cursor()
        # Querying by both user_id and password for basic authentication
        cursor.execute('SELECT * FROM users WHERE user_id = ? AND password = ?', (user_id, password))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        role = row['role']
        if role == 'Donor':
            return Donor(
                user_id=row['user_id'], 
                name=row['name'], 
                contact_info=row['contact_info'], 
                address=row['address'], 
                business_type="N/A",
                tax_id=row['specific_id'],
                latitude=row['latitude'] if 'latitude' in row.keys() else 0.0,
                longitude=row['longitude'] if 'longitude' in row.keys() else 0.0
            )
        elif role == 'Recipient':
            recip = Recipient(
                user_id=row['user_id'],
                name=row['name'],
                contact_info=row['contact_info'],
                address=row['address'],
                charity_registration_number=row['specific_id'],
                capacity="N/A",
                latitude=row['latitude'] if 'latitude' in row.keys() else 0.0,
                longitude=row['longitude'] if 'longitude' in row.keys() else 0.0
            )
            self.attach_observer(recip)
            return recip
        return None

    def add_listing(self, donor_id: str, items_dict: dict, pickup_window: str, expires_at: Optional[datetime] = None) -> FoodListing:
        """Creates a new FoodListing and stores it in the database."""
        listing_id = f"LST-{uuid.uuid4().hex[:6].upper()}"
        items_json = json.dumps(items_dict)
        expires_at_str = expires_at.isoformat() if expires_at else None
        
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO listings (listing_id, donor_id, items, status, pickup_window, expires_at) VALUES (?, ?, ?, ?, ?, ?)',
            (listing_id, donor_id, items_json, 'Available', pickup_window, expires_at_str)
        )
        self.conn.commit()
        
        listing = FoodListing(listing_id, donor_id, items_dict, pickup_window, expires_at)
        self.notify_recipients(listing)
        return listing

    def get_available_listings(self, recipient_id: str = None, max_radius_km: float = None) -> list:
        """Returns a list of all available listings from the database."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM listings WHERE status = "Available"')
        rows = cursor.fetchall()
        
        recip_lat, recip_lon = None, None
        if recipient_id and max_radius_km:
            cursor.execute("SELECT latitude, longitude FROM users WHERE user_id = ?", (recipient_id,))
            r_row = cursor.fetchone()
            if r_row:
                recip_lat, recip_lon = r_row['latitude'], r_row['longitude']
        
        available_listings = []
        for row in rows:
            items_dict = json.loads(row['items'])
            
            # Perishability check
            expires_at = datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None
            listing = FoodListing(
                listing_id=row['listing_id'],
                donor_id=row['donor_id'],
                items=items_dict,
                pickup_window=row['pickup_window'],
                expires_at=expires_at
            )
            
            if listing.is_expired:
                continue # Skip expired listings
                
            # Distance filter
            if recip_lat is not None and recip_lon is not None:
                cursor.execute("SELECT latitude, longitude FROM users WHERE user_id = ?", (listing.donor_id,))
                d_row = cursor.fetchone()
                if d_row:
                    dist = self.calculate_distance(recip_lat, recip_lon, d_row['latitude'], d_row['longitude'])
                    if dist > max_radius_km:
                        continue
                        
            available_listings.append(listing)
            
        return available_listings

    def get_donor_listings(self, donor_id: str) -> list:
        """Returns a list of all listings for a specific donor from the database."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM listings WHERE donor_id = ?', (donor_id,))
        rows = cursor.fetchall()
        
        donor_listings = []
        for row in rows:
            items_dict = json.loads(row['items'])
            listing = FoodListing(
                listing_id=row['listing_id'],
                donor_id=row['donor_id'],
                items=items_dict,
                pickup_window=row['pickup_window']
            )
            listing._status = row['status']
            donor_listings.append(listing)
            
        return donor_listings

    def claim_listing(self, listing_id: str, recipient_id: str) -> DonationTransaction:
        """Updates a listing's status to Claimed and generates a transaction in the database."""
        cursor = self.conn.cursor()
        
        # Check if available
        cursor.execute('SELECT status FROM listings WHERE listing_id = ?', (listing_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Listing {listing_id} not found.")
        if row['status'] != 'Available':
            raise ValueError(f"Listing {listing_id} is not available for claiming.")
            
        # Update status
        cursor.execute('UPDATE listings SET status = "Pending Confirmation" WHERE listing_id = ?', (listing_id,))
        
        # Create transaction
        transaction_id = f"TXN-{uuid.uuid4().hex[:6].upper()}"
        cursor.execute(
            'INSERT INTO transactions (transaction_id, listing_id, recipient_id) VALUES (?, ?, ?)',
            (transaction_id, listing_id, recipient_id)
        )
        
        self.conn.commit()
        print(f"Listing {listing_id} claimed by {recipient_id}. Transaction {transaction_id} created in DB.")
        
        return DonationTransaction(transaction_id, listing_id, recipient_id)

    def get_listing_recipient(self, listing_id: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute('SELECT recipient_id FROM transactions WHERE listing_id = ? ORDER BY timestamp DESC LIMIT 1', (listing_id,))
        row = cursor.fetchone()
        if row:
            return row['recipient_id']
        return None

    def confirm_listing(self, listing_id: str):
        """Confirms a claimed listing."""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE listings SET status = "Claimed" WHERE listing_id = ?', (listing_id,))
        self.conn.commit()
        print(f"Listing {listing_id} confirmed by donor.")

    def reject_listing(self, listing_id: str):
        """Rejects a claimed listing, returning it to available status."""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE listings SET status = "Available" WHERE listing_id = ?', (listing_id,))
        cursor.execute('DELETE FROM transactions WHERE listing_id = ?', (listing_id,))
        self.conn.commit()
        print(f"Listing {listing_id} rejected by donor. Returned to available.")

    def delete_listing(self, listing_id: str):
        """Deletes a listing and its associated transactions from the database."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM listings WHERE listing_id = ?', (listing_id,))
        cursor.execute('DELETE FROM transactions WHERE listing_id = ?', (listing_id,))
        self.conn.commit()
        print(f"Listing {listing_id} and associated transactions deleted.")

    def cancel_claim(self, listing_id: str):
        """Cancels a recipient's claim on a listing, resetting it to Available and removing the transaction."""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE listings SET status = "Available" WHERE listing_id = ?', (listing_id,))
        cursor.execute('DELETE FROM transactions WHERE listing_id = ?', (listing_id,))
        self.conn.commit()
        print(f"Claim for listing {listing_id} cancelled. Returned to Available.")

    def get_recipient_claims(self, recipient_id: str) -> list:
        """Returns a list of listings claimed by a specific recipient (pending confirmation or claimed)."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT listings.* FROM listings 
            JOIN transactions ON listings.listing_id = transactions.listing_id 
            WHERE transactions.recipient_id = ?
        ''', (recipient_id,))
        rows = cursor.fetchall()
        
        claimed_listings = []
        for row in rows:
            items_dict = json.loads(row['items'])
            listing = FoodListing(
                listing_id=row['listing_id'],
                donor_id=row['donor_id'],
                items=items_dict,
                pickup_window=row['pickup_window']
            )
            listing._status = row['status']
            claimed_listings.append(listing)
            
        return claimed_listings

