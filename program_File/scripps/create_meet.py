import qrcode
import sqlite3
import os
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
import hashlib
import time
                                                                                              
def generate_time_based_id(input_text: str) -> str:
    timestamp = str(time.time())
    combined = input_text + timestamp
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]
def generate_qr_code(data: str, save_path: str):

    # Create QR code object
    qr = qrcode.QRCode(
        version=10,
        error_correction=ERROR_CORRECT_H,
        box_size=2,
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
        age_min INTEGER NOT NULL,
        age_max INTEGER NOT NULL,
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
        lane_num INTEGER NOT NULL CHECK(lane_num BETWEEN 1 AND 8),
        swimmer_name TEXT NOT NULL,
        timer1_time REAL ,
        timer2_time REAL ,
        timer3_time REAL ,
        total_time REAL ,
        FOREIGN KEY (heat_id) REFERENCES heats(id)
    );
    """)

    conn.commit()
    conn.close()
def create_event(db_path: str, gender: str, age_min: int, age_max: int, distance: int, stroke: str) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events (gender, age_min, age_max, distance, stroke)
        VALUES (?, ?, ?, ?, ?)
    """, (gender, age_min, age_max, distance, stroke))
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()

    # Generate QR code with full event info
    age_range = f"{age_min}-{age_max}"
    
    qr_data = f"Event ID: {event_id}, {gender}, {age_range}, {distance} yd, {stroke}"
    save_path = f"Active_meet/qr_event_{event_id}.png"
    x = generate_time_based_id(qr_data)
    qr_data = qr_data + (f", Event uuid:{x}")
    generate_qr_code(qr_data, save_path)

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
def add_swimmer_to_lane(db_path: str, heat_id: int, lane_num: int, swimmer_name: str) -> int:
    # No timers provided yet, so set to None (which inserts NULL in SQLite)
    timer1 = timer2 = timer3 = total_time = None

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
def update_lane_times(db_path: str, lane_id: int, timer1: float, timer2: float, timer3: float):
    total_time = round((timer1 + timer2 + timer3) / 3, 3)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE lanes
        SET timer1_time = ?, timer2_time = ?, timer3_time = ?, total_time = ?
        WHERE id = ?
    """, (timer1, timer2, timer3, total_time, lane_id))
    conn.commit()
    conn.close()


def get_all_events(db_path: str) -> list:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    conn.close()
    return events
def get_all_events(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    conn.close()
    return events
def get_heats_for_event(db_path: str, event_id: int):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM heats WHERE event_id = ?", (event_id,))
    heats = cursor.fetchall()
    conn.close()
    return heats
def get_swimmers_in_heat(db_path: str, heat_id: int):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT lane_num, swimmer_name, timer1_time, timer2_time, timer3_time, total_time
        FROM lanes
        WHERE heat_id = ?
        ORDER BY lane_num
    """, (heat_id,))
    swimmers = cursor.fetchall()
    conn.close()
    return swimmers
def get_fastest_swimmer_in_event(db_path: str, event_id: int):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT swimmer_name, total_time, heats.heat_num, lanes.lane_num
        FROM lanes
        JOIN heats ON lanes.heat_id = heats.id
        WHERE heats.event_id = ? AND total_time IS NOT NULL
        ORDER BY total_time ASC
        LIMIT 1
    """, (event_id,))
    result = cursor.fetchone()
    conn.close()
    return result



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

import random

def generate_simple_test_data(db_path: str):
    genders = ["Boys", "Girls"]
    strokes = ["freestyle", "backstroke", "breaststroke"]
    age_ranges = [(9, 10), (11, 12), (13, 14)]

    swimmer_id = 1

    for i in range(100):  # 3 events
        gender = genders[i % len(genders)]
        age_min, age_max = age_ranges[i % len(age_ranges)]
        distance = 50 if i % 2 == 0 else 100
        stroke = strokes[i % len(strokes)]

        event_id = create_event(db_path, gender, age_min, age_max, distance, stroke)

        for heat_num in range(1, 5):  # 1 heat per event
            heat_id = add_heat(db_path, event_id, heat_num)

            for lane_num in range(1, 9):  # 8 lanes
                swimmer_name = f"Swimmer {swimmer_id}"
                lane_id = add_swimmer_to_lane(db_path, heat_id, lane_num, swimmer_name)

                # Generate random timer values (25.00 to 45.00 seconds)
                t1 = round(random.uniform(25.0, 45.0), 2)
                t2 = round(random.uniform(25.0, 45.0), 2)
                t3 = round(random.uniform(25.0, 45.0), 2)

                update_lane_times(db_path, lane_id, t1, t2, t3)

                swimmer_id += 1

    print("Simple test data generated.")

# Call the function
generate_simple_test_data(db_path)


print (get_all_events(db_path))