import qrcode
import sqlite3
from qrcode.constants import ERROR_CORRECT_H
import hashlib
import time
from PIL import ImageDraw ,ImageFont ,Image
import random
import datetime
import inspect
import pprint
import shutil
import zipfile
import tempfile
import os


def full_state_dump(db_path: str, tag: str = ""):
    # Timestamp and safe filename
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_tag = tag.replace(" ", "_").strip("_")
    zip_filename = f"{timestamp}_{safe_tag}.zip" if safe_tag else f"{timestamp}.zip"

    # Base directory of script
    base_dir = os.path.abspath(os.path.dirname(__file__))

    # Output: ../data/debug/
    zip_output_path = os.path.abspath(os.path.join(base_dir, "../app_data/debug", zip_filename))
    os.makedirs(os.path.dirname(zip_output_path), exist_ok=True)

    # Temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:

        # ===== 1. Variable Dump =====
        var_log_path = os.path.join(temp_dir, "variables.txt")
        with open(var_log_path, "w", encoding="utf-8") as f:
            f.write(f"===== Variable Dump @ {timestamp} =====\n\n")

            # Globals
            frame = inspect.currentframe()
            caller_globals = frame.f_back.f_globals
            f.write("-- GLOBAL VARIABLES --\n")
            for var, val in caller_globals.items():
                if var.startswith("__"):
                    continue
                try:
                    f.write(f"{var} = {pprint.pformat(val)}\n")
                except Exception as e:
                    f.write(f"{var} = <UNPRINTABLE: {e}>\n")

            # Stack locals
            f.write("\n-- STACK FRAME LOCALS --\n")
            for i, frame_info in enumerate(inspect.stack()):
                f.write(f"\nFrame {i}: {frame_info.function} (Line {frame_info.lineno})\n")
                for var, val in frame_info.frame.f_locals.items():
                    try:
                        f.write(f"{var} = {pprint.pformat(val)}\n")
                    except Exception as e:
                        f.write(f"{var} = <UNPRINTABLE: {e}>\n")

            f.write("\n===== End of Variable Dump =====\n")

        # ===== 2. Swimmer / Database Dump =====
        swimmer_log_path = os.path.join(temp_dir, "swimmers.txt")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            with open(swimmer_log_path, "w", encoding="utf-8") as f:
                def dump_table(name):
                    f.write(f"\n==== TABLE: {name} ====\n")
                    try:
                        cursor.execute(f"SELECT * FROM {name}")
                        rows = cursor.fetchall()
                        col_names = [desc[0] for desc in cursor.description]
                        f.write(" | ".join(col_names) + "\n")
                        for row in rows:
                            f.write(" | ".join(str(cell) for cell in row) + "\n")
                    except Exception as e:
                        f.write(f"[ERROR] Could not dump table '{name}': {e}\n")

                for table in ['events', 'heats', 'lanes']:
                    dump_table(table)

            conn.close()
        except Exception as e:
            with open(swimmer_log_path, "w", encoding="utf-8") as f:
                f.write(f"[ERROR] Unable to dump swimmer data: {e}\n")

        # ===== 3. Copy DB file =====
        if os.path.exists(db_path):
            shutil.copy2(db_path, os.path.join(temp_dir, os.path.basename(db_path)))
        else:
            with open(var_log_path, "a", encoding="utf-8") as f:
                f.write(f"\n[WARNING] Database file not found at {db_path}\n")

        # ===== 4. Add Everything to ZIP =====
        with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add the variable + swimmer logs + db copy
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    path = os.path.join(root, file)
                    arcname = os.path.relpath(path, temp_dir)
                    zipf.write(path, arcname)

            # Add full Active_meet directory
            active_meet_path = os.path.join(base_dir, "Active_meet")
            if os.path.exists(active_meet_path):
                for root, _, files in os.walk(active_meet_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, base_dir)
                        zipf.write(file_path, arcname)

    print(f" Full debug dump written to:\n{zip_output_path}")                  

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
def get_heat_number_from_id(db_path: str, heat_id: int) -> int | None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT heat_num FROM heats
        WHERE id = ?
    """, (heat_id,))
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None
def get_number_of_heats_for_event(db_path: str, event_id: int) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM heats
        WHERE event_id = ?
    """, (event_id,))
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else 0
def get_total_number_of_events(db_path: str) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM events")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0
def list_all_info(db_path: str):
    for x in range(1, y + 1):
        print(f"Event {x}:")
        print(get_heats_for_event(db_path, x))
        print(get_fastest_swimmer_in_event(db_path, x))
        print(list_swimmers_in_event(db_path, x))
        print(get_event_results(db_path, x))
        print("\n")
    print("All swimmers in the database:")
    swimmers = list_all_swimmers(db_path)
    for swimmer in swimmers:
        print(swimmer)

def rendered_a_timesheets(db_path: str, event_id: int): 
    qr_size = 125
    bg_width = 1000
    bg_height = 400

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    font_path = os.path.join(base_dir, 'app_resources', 'arial.ttf')

    try:
        font = ImageFont.truetype(font_path, 30)  # Bigger font size for clarity
    except IOError:
        font = ImageFont.load_default()
        print("Warning: 'arial.ttf' font not found, using default font.")

    margin_left = 30
    margin_top = 20
    line_spacing = 50  # vertical space between lines

    for heat in get_heats_for_event(db_path, event_id):
        heat_id = heat[0]
        heat_num = heat[2]

        swimmers = get_swimmers_in_heat(db_path, heat_id)

        for lane_num in range(1, 9):
            # Try to get swimmer in this lane
            swimmer = next((s for s in swimmers if s[0] == lane_num), None)  # s[0] is lane_num

            if swimmer:
                _, swimmer_name, t1, t2, t3, total = swimmer
                lane_id = get_lane_id_by_heat_and_lane(db_path, heat_id, lane_num)
            else:
                swimmer_name = "Empty Lane"
                lane_id = None

            # Prepare the image background
            background = Image.new("RGBA", (bg_width, bg_height), (255, 255, 255, 255))
            draw = ImageDraw.Draw(background)

            if lane_id:
                qr_code_data = f"Event ID: {event_id}, heat Id:{heat_id}, heat number:{heat_num}, lane id: {lane_id}, lane num:{lane_num},  swimmer name: {swimmer_name}"
                generate_qr_code(qr_code_data, "Active_meet/temp/qr_code.png")
                qr_path = "Active_meet/temp/qr_code.png"
                if os.path.exists(qr_path):
                    qr_code = Image.open(qr_path).convert("RGBA").resize((qr_size, qr_size))
                    background.paste(qr_code, (15, 15), qr_code)

            # Draw header texts
            margin_left_2 = margin_left + qr_size
            draw.text((margin_left_2, margin_top), f"Swimmer: {swimmer_name}", fill=(0, 0, 0), font=font)
            draw.text((margin_left_2, margin_top + line_spacing), f"Event: {event_id} | Heat: {heat_num} | Lane: {lane_num}", fill=(0, 0, 0), font=font)

            # Draw timer lines even if empty
            line_y = margin_top + line_spacing * 2 - 10
            times_start_y = line_y + 30
            draw.text((margin_left, times_start_y), "Timer 1: ____________________", fill=(0, 0, 0), font=font)
            draw.text((margin_left, times_start_y + line_spacing), "Timer 2: ____________________", fill=(0, 0, 0), font=font)
            draw.text((margin_left, times_start_y + 2 * line_spacing), "Timer 3: ____________________", fill=(0, 0, 0), font=font)
            draw.text((margin_left, times_start_y + 3 * line_spacing), "Total:   ____________________", fill=(0, 0, 0), font=font)

            # Save output
            output_dir = f"Active_meet/Time_sheets/{event_id}/{heat_num}"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"lane_{lane_num}_timesheet.png")
            background.save(output_path)

def rendered_all_timesheets(db_path: str):
    number_of_events = get_total_number_of_events(db_path)
    x = number_of_events
    for i in range(1, x + 1):
        rendered_a_timesheets(db_path,i)
        percent = (i / (number_of_events))  # Calculate percentage of completion
        percent = round(percent * 100, 2)
        print(f"Rendering timesheets for event {i} of {number_of_events}:")
        print(f"{percent} %")

def random_swimmer_name():
    first_names = [
        "Liam", "Olivia", "Noah", "Emma", "Elijah", "Ava",
        "James", "Sophia", "Benjamin", "Isabella", "Lucas", "Mia"
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones",
        "Garcia", "Miller", "Davis", "Wilson", "Martinez", "Lee", "Clark"
    ]
    return f"{random.choice(first_names)} {random.choice(last_names)}"
def generate_realistic_test_data(db_path: str, num_events=10):
    genders = ["Boys", "Girls"]
    strokes = ["freestyle", "backstroke", "breaststroke", "butterfly"]
    age_ranges = [(9, 10), (11, 12), (13, 14)]
    distances = [25, 50, 100]

    for _ in range(num_events):
        gender = random.choice(genders)
        age_min, age_max = random.choice(age_ranges)
        distance = random.choice(distances)
        stroke = random.choice(strokes)

        event_id = create_event(db_path, gender, age_min, age_max, distance, stroke)

        num_heats = random.randint(1, 7)
        for heat_num in range(1, num_heats + 1):
            heat_id = add_heat(db_path, event_id, heat_num)

            # More empty lanes in the last heat
            if heat_num < num_heats:
                num_lanes = random.randint(6, 8)
            else:
                num_lanes = random.randint(1, 5)

            used_lanes = random.sample(range(1, 9), num_lanes)
            assigned_lanes = {}  # lane_num: swimmer_name

            for lane_num in sorted(used_lanes):
                swimmer_name = random_swimmer_name()
                add_swimmer_to_lane(db_path, heat_id, lane_num, swimmer_name)
                assigned_lanes[lane_num] = swimmer_name


    print(f"{num_events} realistic events generated without timing data.")

db_path = "Active_meet/swim_meet.db"

initialize_database_at_path(db_path)

generate_realistic_test_data(db_path)

rendered_all_timesheets(db_path)

y = get_total_number_of_events(db_path)

get_all_events(db_path)

full_state_dump(db_path,"done")

