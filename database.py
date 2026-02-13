import sqlite3
from datetime import datetime, timedelta


class Database:
    def __init__(self, db_name="assassin.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    pro_expiry TEXT, 
                    daily_usage_count INTEGER DEFAULT 0,
                    last_reset_date TEXT,
                    referred_by INTEGER,
                    referral_count INTEGER DEFAULT 0
                )
            """)

    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        today = datetime.now().strftime('%Y-%m-%d')

        if not user:
            self.conn.execute("INSERT INTO users (user_id, pro_expiry, last_reset_date) VALUES (?, ?, ?)",
                              (user_id, None, today))
            self.conn.commit()
            return (user_id, None, 0, today, None, 0)

        if user[3] != today:
            self.conn.execute("UPDATE users SET daily_usage_count = 0, last_reset_date = ? WHERE user_id = ?",
                              (today, user_id))
            self.conn.commit()
            return (user_id, user[1], 0, today, user[4], user[5])
        return user

    def is_user_pro(self, user_id):
        user = self.get_user(user_id)
        if not user[1]: return False
        try:
            return datetime.fromisoformat(user[1]) > datetime.now()
        except:
            return False

    def add_pro_days(self, user_id, days):
        user = self.get_user(user_id)
        current_expiry = user[1]
        start_date = datetime.now()
        if current_expiry and datetime.fromisoformat(current_expiry) > datetime.now():
            start_date = datetime.fromisoformat(current_expiry)

        new_expiry = (start_date + timedelta(days=days)).isoformat()
        with self.conn:
            self.conn.execute("UPDATE users SET pro_expiry = ? WHERE user_id = ?", (new_expiry, user_id))

    def set_lifetime_pro(self, user_id):
        infinite_date = datetime(2099, 12, 31).isoformat()
        with self.conn:
            self.conn.execute("UPDATE users SET pro_expiry = ? WHERE user_id = ?", (infinite_date, user_id))

    def cancel_pro(self, user_id):
        with self.conn:
            self.conn.execute("UPDATE users SET pro_expiry = NULL WHERE user_id = ?", (user_id,))

    def process_referral(self, new_user_id, referrer_id):
        if new_user_id == referrer_id: return False
        cursor = self.conn.cursor()
        cursor.execute("SELECT referred_by FROM users WHERE user_id = ?", (new_user_id,))
        row = cursor.fetchone()
        if row is None or row[0] is None:
            self.get_user(new_user_id)
            with self.conn:
                self.conn.execute("UPDATE users SET referred_by = ? WHERE user_id = ?", (referrer_id, new_user_id))
                self.conn.execute("UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?",
                                  (referrer_id,))
            self.add_pro_days(referrer_id, 2)
            return True
        return False

    def increment_usage(self, user_id):
        with self.conn:
            self.conn.execute("UPDATE users SET daily_usage_count = daily_usage_count + 1 WHERE user_id = ?",
                              (user_id,))


db = Database()