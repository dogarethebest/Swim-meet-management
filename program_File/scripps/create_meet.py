import qrcode
import sqlite3
import os
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H

def generate_qr_code(data: str, save_path: str):

    # Create QR code object
    qr = qrcode.QRCode(
        version=15,
        error_correction=ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    # Add data and make the QR code
    qr.add_data(data)
    qr.make(fit=True)

    # Generate the image
    img = qr.make_image(fill_color="black", back_color="white")

    # Save to file
    img.save(save_path)
    print(f"QR code saved to: {save_path}")
def initialize_database_at_path(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gender TEXT NOT NULL CHECK(gender IN ('Boys', 'Girls')),
        distance INTEGER NOT NULL,
        stroke TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS heats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        heat_num INTEGER NOT NULL,
        FOREIGN KEY (event_id) REFERENCES events(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lanes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        heat_id INTEGER NOT NULL,
        lane_num INTEGER NOT NULL CHECK(lane_num BETWEEN 1 AND 7),
        swimmer_name TEXT NOT NULL,
        timer1_time REAL NOT NULL,
        timer2_time REAL NOT NULL,
        timer3_time REAL NOT NULL,
        total_time REAL NOT NULL,
        FOREIGN KEY (heat_id) REFERENCES heats(id)
    );
    """)

    conn.commit()
    conn.close()
def create_event(db_path: str, gender: str, distance: int, stroke: str) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events (gender, distance, stroke)
        VALUES (?, ?, ?)
    """, (gender, distance, stroke))
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()
    return event_id
def add_heat(db_path: str, event_id: int, heat_num: int) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO heats (event_id, heat_num)
        VALUES (?, ?)
    """, (event_id, heat_num))
    conn.commit()
    heat_id = cursor.lastrowid
    conn.close()
    return heat_id
def add_swimmer_to_lane(db_path: str, heat_id: int, lane_num: int, swimmer_name: str,
                        timer1: float, timer2: float, timer3: float) -> int:
    total_time = round((timer1 + timer2 + timer3) / 3, 3)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO lanes (heat_id, lane_num, swimmer_name, timer1_time, timer2_time, timer3_time, total_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (heat_id, lane_num, swimmer_name, timer1, timer2, timer3, total_time))
    conn.commit()
    lane_id = cursor.lastrowid
    conn.close()
    return lane_id
def get_all_events(db_path: str) -> list:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    conn.close()
    return events



# Define your path — change this to your preferred location
db_path = "Active_meet/swim_meet.db"

# Ensure the directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Connect to (and create) the database
conn = sqlite3.connect(db_path)

# Now the file /Users/nicholaskitt/Documents/swim_meet/my_meet.db exists
conn.close()
print("meet will be created automatically through script")
initialize_database_at_path(db_path)