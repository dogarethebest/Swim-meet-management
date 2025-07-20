import qrcode
import sqlite3
import os
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
import hashlib
import time
from PIL import ImageDraw ,ImageFont ,Image
import random

                                                                                              
def generate_time_based_id(input_text: str) -> str:
    timestamp = str(time.time())
    combined = input_text + timestamp
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]
def generate_qr_code(data: str, save_path: str):

    # Create QR code object
    qr = qrcode.QRCode(
        version=5,
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
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
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
    save_path = f"Active_meet/qr_code/event/{event_id}.png"
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

    qr_data = f"Event ID: {event_id}, heat Id:{heat_id}"
    save_path = f"Active_meet/qr_code/heat/{heat_id}.png"
    generate_qr_code(qr_data, save_path)

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

    event_id = get_event_id_from_heat(db_path, heat_id)
    qr_data = f"Event ID: {event_id}, heat Id:{heat_id},lane num:{lane_num} lane id: {lane_id}"
    save_path = f"Active_meet/qr_code/lane/{lane_id}.png"

    generate_qr_code(qr_data, save_path)

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
        SELECT swimmer_name, total_time, heats.heat_num, lanes.lane_num,
               timer1_time, timer2_time, timer3_time
        FROM lanes
        JOIN heats ON lanes.heat_id = heats.id
        WHERE heats.event_id = ? AND total_time IS NOT NULL
        ORDER BY total_time ASC
        LIMIT 1
    """, (event_id,))
    result = cursor.fetchone()
    conn.close()
    return result
def list_all_swimmers(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT swimmer_name, heats.heat_num, lanes.lane_num, events.id AS event_id,
               events.stroke, timer1_time, timer2_time, timer3_time, total_time
        FROM lanes
        JOIN heats ON lanes.heat_id = heats.id
        JOIN events ON heats.event_id = events.id
        ORDER BY event_id, heats.heat_num, lanes.lane_num
    """)
    swimmers = cursor.fetchall()
    conn.close()
    return swimmers
def list_swimmers_in_event(db_path: str, event_id: int):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT swimmer_name, heats.heat_num, lanes.lane_num,
               timer1_time, timer2_time, timer3_time, total_time
        FROM lanes
        JOIN heats ON lanes.heat_id = heats.id
        WHERE heats.event_id = ?
        ORDER BY heats.heat_num, lanes.lane_num
    """, (event_id,))
    swimmers = cursor.fetchall()
    conn.close()
    return swimmers
def get_event_results(db_path: str, event_id: int):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT swimmer_name, heats.heat_num, lanes.lane_num,
               timer1_time, timer2_time, timer3_time, total_time
        FROM lanes
        JOIN heats ON lanes.heat_id = heats.id
        WHERE heats.event_id = ? AND total_time IS NOT NULL
        ORDER BY total_time ASC
    """, (event_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_lane_id_by_heat_and_lane(db_path: str, heat_id: int, lane_num: int) -> int | None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM lanes WHERE heat_id = ? AND lane_num = ?
    """, (heat_id, lane_num))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None
def get_event_id_from_heat(db_path: str, heat_id: int) -> int | None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT event_id FROM heats
        WHERE id = ?
    """, (heat_id,))
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None
def get_swimmer_name_from_lane(db_path: str, lane_id: int) -> str | None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT swimmer_name FROM lanes
        WHERE id = ?
    """, (lane_id,))
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None

def rendered_timesheets(db_path: str, event_id: int):



    bg_width = 1000     # width of the white background
    bg_height = 600    # height of the white background
    qr_size = 125      # size to resize the QR code
    Lane_ID = 1
    
    
    
    # Open and resize QR code
    qr_code = Image.open(f"Active_meet/qr_code/lane/1.png").convert("RGBA")
    qr_code = qr_code.resize((qr_size, qr_size))

    # Create a white background box
    background = Image.new("RGBA", (bg_width, bg_height), (255, 255, 255, 255))  # white box
    
    line_y = qr_size + 15

    draw = ImageDraw.Draw(background)
    draw.line([(0, line_y), (bg_width, line_y)], fill=(0, 0, 0), width=2)

    swimmer_name = get_swimmer_name_from_lane(db_path,Lane_ID)

    font = ImageFont.load_default()
    draw.text((qr_size + 15+10,100), swimmer_name, fill=(0, 0, 0), font=font)

    # Position to center the QR code
    x = (15)
    y = (15)

    # Paste the QR code onto the white background
    background.paste(qr_code, (x, y), qr_code)  # third arg = transparency mask
    
   
    os.makedirs(os.path.dirname(f"Active_meet/Time_sheets/{event_id}/{Lane_ID}/,"), exist_ok=True)
    # Save the final stacked image
    background.save(f"Active_meet/Time_sheets/{event_id}/{Lane_ID}qr_on_white_box.png")




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



def generate_simple_test_data(db_path: str):
    genders = ["Boys", "Girls"]
    strokes = ["freestyle", "backstroke", "breaststroke"]
    age_ranges = [(9, 10), (11, 12), (13, 14)]

    swimmer_id = 1

    for i in range(10):  # 3 events
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

generate_simple_test_data(db_path)
rendered_timesheets(db_path,1)