import aiosqlite
import asyncio

class Database:
    def __init__(self, db_path="bookings.db"):
        self.db_path = db_path
    
    async def create_table(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    user_name TEXT,
                    service TEXT,
                    date TEXT,
                    time_slot TEXT,
                    status TEXT DEFAULT 'new'
                )
            ''')
            await db.commit()
    
    async def add_booking(self, user_id, user_name, service, date, time_slot):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO bookings (user_id, user_name, service, date, time_slot) VALUES (?, ?, ?, ?, ?)",
                (user_id, user_name, service, date, time_slot)
            )
            await db.commit()

# Глобальная инстанция для использования в других модулях
db = Database()
